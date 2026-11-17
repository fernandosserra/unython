from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import List, Optional
from decimal import Decimal

from src.utils.audit import record_audit
from src.utils.dependencies import DBDependency, get_current_user, require_module
from src.modules.caixas import CaixaService
from src.utils.models import Caixa, Usuario
from src.utils.schemas import CaixaAbrirRequest

router = APIRouter(prefix="/caixas", tags=["Caixas"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=List[dict], dependencies=[Depends(require_module("caixa", "pdv", check_features=False))])
def listar_caixas(db: DBDependency):
    service = CaixaService(db)
    caixas = service.buscar_todos_caixas()
    return [c.__dict__ for c in caixas]


@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_module("caixa"))])
def criar_caixa(caixa: Caixa, db: DBDependency):
    service = CaixaService(db)
    cid = service.registrar_caixa(caixa)
    if not cid:
        raise HTTPException(status_code=400, detail="Não foi possível criar o caixa.")
    return {"id": cid}


@router.get("/{caixa_id}/movimento-ativo", dependencies=[Depends(require_module("caixa", "pdv", check_features=False))])
def movimento_ativo(caixa_id: int, db: DBDependency):
    service = CaixaService(db)
    mov = service.buscar_movimento_ativo(caixa_id)
    if not mov:
        raise HTTPException(status_code=404, detail="Nenhum movimento ativo.")
    return mov.__dict__


@router.post("/{caixa_id}/abrir", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_module("caixa"))])
def abrir_movimento(
    caixa_id: int,
    db: DBDependency,
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    payload: Optional[CaixaAbrirRequest] = None,
    usuario_id: Optional[int] = None,
    valor_abertura: Optional[Decimal] = None,
    id_evento: Optional[int] = None,
):
    """Abre uma nova sessão de movimento de caixa, aceitando corpo JSON ou parâmetros de consulta."""
    service = CaixaService(db)
    val = payload.valor_abertura if payload else (valor_abertura or Decimal("0.00"))
    ev_id = payload.id_evento if payload else id_evento

    if ev_id is None:
        from src.modules.evento import EventoService
        evs = EventoService(db)
        ev = evs.buscar_evento_aberto()
        if not ev:
            raise HTTPException(status_code=400, detail="Nenhum evento aberto. Abra um evento antes.")
        ev_id = ev.id

    try:
        evento = service.validar_evento_abertura(ev_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        db.execute_query("SELECT id FROM caixas WHERE id = %s FOR UPDATE", (caixa_id,), fetch_one=True)
        if service.buscar_movimento_ativo(caixa_id):
            raise HTTPException(status_code=400, detail="Já existe movimento aberto para este caixa.")
        mid = service.abrir_movimento(caixa_id, current_user.id, val, ev_id, commit=False)
        if not mid:
            raise HTTPException(status_code=400, detail="Não foi possível abrir movimento.")
        record_audit(db, user_id=current_user.id, acao="abrir_caixa",
                     entidade="movimento_caixa", entidade_id=mid,
                     detalhes={
                         "caixa_id": caixa_id,
                         "evento_id": ev_id,
                         "evento_nome": evento.nome,
                         "evento_data": str(evento.data_evento),
                         "valor_abertura": str(val),
                     },
                     request_id=request.state.request_id)
        db.conn.commit()
    except Exception:
        db.conn.rollback()
        raise
    return {"movimento_id": mid}


@router.post("/{movimento_id}/fechar", dependencies=[Depends(require_module("caixa"))])
def fechar_movimento(movimento_id: int, db: DBDependency, request: Request, current_user: Usuario = Depends(get_current_user)):
    service = CaixaService(db)
    try:
        ok = service.fechar_movimento(movimento_id, commit=False)
        if not ok:
            raise HTTPException(status_code=400, detail="Não foi possível fechar movimento.")
        record_audit(db, user_id=current_user.id, acao="fechar_caixa",
                     entidade="movimento_caixa", entidade_id=movimento_id,
                     detalhes={}, request_id=request.state.request_id)
        db.conn.commit()
    except Exception:
        db.conn.rollback()
        raise
    return {"status": "fechado"}
