from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from decimal import Decimal

from src.utils.dependencies import DBDependency
from src.modules.caixas import CaixaService
from src.utils.models import Caixa
from src.utils.schemas import CaixaAbrirRequest

router = APIRouter(prefix="/caixas", tags=["Caixas"])


@router.get("/", response_model=List[dict])
def listar_caixas(db: DBDependency):
    service = CaixaService(db)
    caixas = service.buscar_todos_caixas()
    return [c.__dict__ for c in caixas]


@router.post("/", status_code=status.HTTP_201_CREATED)
def criar_caixa(caixa: Caixa, db: DBDependency):
    service = CaixaService(db)
    cid = service.registrar_caixa(caixa)
    if not cid:
        raise HTTPException(status_code=400, detail="Não foi possível criar o caixa.")
    return {"id": cid}


@router.get("/{caixa_id}/movimento-ativo")
def movimento_ativo(caixa_id: int, db: DBDependency):
    service = CaixaService(db)
    mov = service.buscar_movimento_ativo(caixa_id)
    if not mov:
        raise HTTPException(status_code=404, detail="Nenhum movimento ativo.")
    return mov.__dict__


@router.post("/{caixa_id}/abrir", status_code=status.HTTP_201_CREATED)
def abrir_movimento(
    caixa_id: int,
    db: DBDependency,
    payload: Optional[CaixaAbrirRequest] = None,
    usuario_id: Optional[int] = None,
    valor_abertura: Optional[Decimal] = None,
    id_evento: Optional[int] = None,
):
    """Abre uma nova sessão de movimento de caixa, aceitando corpo JSON ou parâmetros de consulta."""
    service = CaixaService(db)
    uid = payload.usuario_id if payload else usuario_id
    val = payload.valor_abertura if payload else (valor_abertura or Decimal("0.00"))
    ev_id = payload.id_evento if payload else id_evento

    if uid is None:
        raise HTTPException(status_code=400, detail="usuario_id é obrigatório.")

    if ev_id is None:
        from src.modules.evento import EventoService
        evs = EventoService(db)
        ev = evs.buscar_evento_aberto()
        if not ev:
            raise HTTPException(status_code=400, detail="Nenhum evento aberto. Abra um evento antes.")
        ev_id = ev.id

    mid = service.abrir_movimento(caixa_id, uid, val, ev_id)
    if not mid:
        raise HTTPException(status_code=400, detail="Não foi possível abrir movimento (já existe aberto?).")
    return {"movimento_id": mid}


@router.post("/{movimento_id}/fechar")
def fechar_movimento(movimento_id: int, db: DBDependency):
    service = CaixaService(db)
    ok = service.fechar_movimento(movimento_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Não foi possível fechar movimento.")
    return {"status": "fechado"}
