from fastapi import APIRouter, Depends, HTTPException, status
from datetime import date
from typing import List, Optional

from src.utils.dependencies import DBDependency, require_module
from src.modules.evento import EventoService
from src.utils.models import Evento

router = APIRouter(prefix="/eventos", tags=["Eventos"])
EVENTOS_READ = require_module("eventos", "atendimentos", "caixa", "doacoes", "pdv", check_features=False)
EVENTO_ABERTO_READ = require_module("eventos", "atendimentos", "caixa", "doacoes", "pdv", "estoque", check_features=False)
EVENTOS_ATENDIMENTOS_WRITE = require_module("eventos", "atendimentos")
EVENTOS_CAIXA_WRITE = require_module("eventos", "caixa")


@router.get("/aberto", dependencies=[Depends(EVENTO_ABERTO_READ)])
def evento_aberto(db: DBDependency):
    service = EventoService(db)
    ev = service.buscar_evento_aberto()
    if not ev:
        raise HTTPException(status_code=404, detail="Nenhum evento aberto.")
    return ev.__dict__


@router.get("/ativos-e-futuros", dependencies=[Depends(EVENTOS_READ)])
def listar_eventos_ativos_e_futuros(db: DBDependency):
    """Retorna eventos abertos e agendados com antecedência."""
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
    service = EventoService(db)
    ev = Evento(nome=nome, data_evento=data_evento, tipo=tipo, status=status)
    ev_id = service.registrar_evento(ev)
    if not ev_id:
        raise HTTPException(status_code=400, detail="Não foi possível criar o evento.")
    return {"id": ev_id, "nome": nome, "data_evento": str(data_evento), "tipo": tipo, "status": status}


@router.post("/{evento_id}/iniciar", dependencies=[Depends(EVENTOS_ATENDIMENTOS_WRITE)])
def iniciar_evento_agendado(evento_id: int, db: DBDependency):
    """Inicia / abre um evento que havia sido agendado previamente."""
    service = EventoService(db)
    ok = service.abrir_evento_existente(evento_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Não foi possível iniciar o evento.")
    return {"status": "Aberto", "id": evento_id}


@router.post("/abrir", status_code=status.HTTP_201_CREATED, dependencies=[Depends(EVENTOS_CAIXA_WRITE)])
def abrir_evento(nome: str = None, tipo: str = "Operacao", db: DBDependency = None):
    """Abre um evento/dia de trabalho; se já houver aberto, retorna-o."""
    service = EventoService(db)
    aberto = service.buscar_evento_aberto()
    if aberto:
        return aberto.__dict__
    hoje = date.today()
    nome_final = nome or f"Operacao {hoje}"
    ev = Evento(nome=nome_final, data_evento=hoje, tipo=tipo)
    ev_id = service.registrar_evento(ev)
    return {"id": ev_id, "nome": nome_final, "data_evento": str(hoje), "tipo": tipo}


@router.post("/{evento_id}/fechar", dependencies=[Depends(EVENTOS_CAIXA_WRITE)])
def fechar_evento(evento_id: int, db: DBDependency):
    """Fecha um evento aberto."""
    service = EventoService(db)
    ok = service.fechar_evento(evento_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Não foi possível fechar o evento.")
    return {"status": "fechado", "id": evento_id}
