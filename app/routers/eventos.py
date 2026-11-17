from fastapi import APIRouter, Depends, HTTPException, Request, status
from datetime import date
from typing import List, Optional
from psycopg2.errors import UniqueViolation

from src.utils.audit import record_audit
from src.utils.dependencies import DBDependency, get_current_user, require_module
from src.modules.evento import EventoService
from src.utils.models import Evento, Usuario

router = APIRouter(prefix="/eventos", tags=["Eventos"])
EVENTOS_READ = require_module("eventos", "atendimentos", "caixa", "doacoes", "pdv", check_features=False)
EVENTO_ABERTO_READ = require_module("eventos", "atendimentos", "caixa", "doacoes", "pdv", "estoque", check_features=False)
EVENTOS_ATENDIMENTOS_WRITE = require_module("eventos", "atendimentos")
EVENTOS_CAIXA_WRITE = require_module("eventos", "caixa")
EVENTOS_OPERACAO_WRITE = require_module("eventos", "atendimentos", "caixa")


@router.get("/data-operacional", dependencies=[Depends(EVENTOS_READ)])
def obter_data_operacional():
    """Retorna a data usada pelo servidor para validar operações do dia."""
    return {"data_operacional": date.today().isoformat()}


@router.get("/aberto", dependencies=[Depends(EVENTO_ABERTO_READ)])
def evento_aberto(db: DBDependency):
    service = EventoService(db)
    ev = service.buscar_evento_aberto()
    if not ev:
        raise HTTPException(status_code=404, detail="Nenhum evento aberto.")
    return ev.__dict__


@router.get("/ativos-e-futuros", dependencies=[Depends(EVENTOS_READ)])
def listar_eventos_ativos_e_futuros(db: DBDependency):
    """Retorna eventos abertos e pré-cadastrados para seleção por outros módulos."""
    service = EventoService(db)
    evs = service.buscar_eventos_futuros_ou_abertos()
    return [e.__dict__ for e in evs]


@router.get("/", dependencies=[Depends(EVENTOS_READ)])
def listar_eventos(db: DBDependency, data_inicio: Optional[date] = None, data_fim: Optional[date] = None) -> List[dict]:
    service = EventoService(db)
    eventos = service.buscar_eventos(data_inicio, data_fim)
    return [e.__dict__ for e in eventos]


@router.post("/novo", status_code=status.HTTP_201_CREATED, dependencies=[Depends(EVENTOS_ATENDIMENTOS_WRITE)])
def criar_evento_agendado(
    nome: str,
    data_evento: date,
    tipo: str = "Atendimento",
    status: str = "Agendado",
    db: DBDependency = None,
):
    """Cria um evento futuro com antecedência (ex: Gira de Marinheiro na próxima sexta)."""
    if status != "Agendado":
        raise HTTPException(status_code=400, detail="Novos eventos devem ser criados como Agendado.")
    service = EventoService(db)
    ev = Evento(nome=nome, data_evento=data_evento, tipo=tipo, status=status)
    ev_id = service.registrar_evento(ev)
    if not ev_id:
        raise HTTPException(status_code=400, detail="Não foi possível criar o evento.")
    return {"id": ev_id, "nome": nome, "data_evento": str(data_evento), "tipo": tipo, "status": status}


@router.post("/{evento_id}/iniciar", dependencies=[Depends(EVENTOS_OPERACAO_WRITE)])
def iniciar_evento_agendado(evento_id: int, db: DBDependency, request: Request,
                             current_user: Usuario = Depends(get_current_user)):
    """Inicia / abre um evento que havia sido agendado previamente."""
    service = EventoService(db)
    try:
        evento = service.buscar_evento(evento_id, for_update=True)
        if not evento:
            raise HTTPException(status_code=404, detail="Evento não encontrado.")
        if evento.status != "Agendado":
            raise HTTPException(status_code=400, detail="O evento não está agendado.")
        if evento.data_evento != date.today():
            raise HTTPException(status_code=400, detail="A data do evento não corresponde à data operacional.")
        if not service.abrir_evento_existente(evento_id, commit=False):
            raise HTTPException(status_code=409, detail="Já existe um evento aberto.")
        record_audit(db, user_id=current_user.id, acao="abrir_evento", entidade="evento",
                     entidade_id=evento_id, detalhes={"nome": evento.nome, "data_evento": str(evento.data_evento)},
                     request_id=request.state.request_id)
        db.conn.commit()
    except UniqueViolation as exc:
        db.conn.rollback()
        raise HTTPException(status_code=409, detail="Já existe um evento aberto.") from exc
    except Exception:
        db.conn.rollback()
        raise
    return {"status": "Aberto", "id": evento_id}


@router.post("/abrir", status_code=status.HTTP_201_CREATED, dependencies=[Depends(EVENTOS_CAIXA_WRITE)])
def abrir_evento(request: Request, nome: str = None, tipo: str = "Operacao", db: DBDependency = None,
                 current_user: Usuario = Depends(get_current_user)):
    """Abre um evento avulso, preservando a compatibilidade com o fluxo legado."""
    service = EventoService(db)
    hoje = date.today()
    nome_final = nome or f"Operacao {hoje}"
    ev = Evento(nome=nome_final, data_evento=hoje, tipo=tipo)
    try:
        if service.buscar_evento_aberto():
            raise HTTPException(status_code=409, detail="Já existe um evento aberto.")
        ev_id = service.registrar_evento(ev, commit=False)
        if not ev_id:
            raise HTTPException(status_code=400, detail="Não foi possível abrir o evento.")
        record_audit(db, user_id=current_user.id, acao="abrir_evento", entidade="evento",
                     entidade_id=ev_id, detalhes={"nome": nome_final, "data_evento": str(hoje)},
                     request_id=request.state.request_id)
        db.conn.commit()
    except UniqueViolation as exc:
        db.conn.rollback()
        raise HTTPException(status_code=409, detail="Já existe um evento aberto.") from exc
    except Exception:
        db.conn.rollback()
        raise
    return {"id": ev_id, "nome": nome_final, "data_evento": str(hoje), "tipo": tipo}


@router.post("/{evento_id}/fechar", dependencies=[Depends(EVENTOS_OPERACAO_WRITE)])
def fechar_evento(evento_id: int, db: DBDependency, request: Request,
                  confirmar_caixa_aberto: bool = False, current_user: Usuario = Depends(get_current_user)):
    """Fecha um evento aberto."""
    service = EventoService(db)
    try:
        evento = service.buscar_evento(evento_id, for_update=True)
        if not evento or evento.status != "Aberto":
            raise HTTPException(status_code=400, detail="Evento aberto não encontrado.")
        _, row = db.execute_query(
            "SELECT COUNT(*) FROM movimentos_caixa WHERE id_evento = %s AND status = 'Aberto'",
            (evento_id,), fetch_one=True,
        )
        movimentos_abertos = row[0]
        if movimentos_abertos and not confirmar_caixa_aberto:
            raise HTTPException(status_code=409, detail={
                "code": "caixa_aberto", "movimentos_abertos": movimentos_abertos,
                "message": "Há movimento de caixa aberto vinculado a este evento.",
            })
        if not service.fechar_evento(evento_id, commit=False):
            raise HTTPException(status_code=400, detail="Não foi possível fechar o evento.")
        record_audit(db, user_id=current_user.id, acao="fechar_evento", entidade="evento",
                     entidade_id=evento_id, detalhes={"nome": evento.nome, "movimentos_abertos": movimentos_abertos},
                     request_id=request.state.request_id)
        db.conn.commit()
    except Exception:
        db.conn.rollback()
        raise
    return {"status": "fechado", "id": evento_id}
