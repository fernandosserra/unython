from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from decimal import Decimal

from src.utils.dependencies import DBDependency
from src.modules.caixas import CaixaService
from src.utils.models import Caixa

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
        raise HTTPException(status_code=400, detail="Nao foi possivel criar o caixa.")
    return {"id": cid}


@router.get("/{caixa_id}/movimento-ativo")
def movimento_ativo(caixa_id: int, db: DBDependency):
    service = CaixaService(db)
    mov = service.buscar_movimento_ativo(caixa_id)
    if not mov:
        raise HTTPException(status_code=404, detail="Nenhum movimento ativo.")
    return mov.__dict__


@router.post("/{caixa_id}/abrir", status_code=status.HTTP_201_CREATED)
def abrir_movimento(caixa_id: int, usuario_id: int, valor_abertura: Decimal, id_evento: Optional[int] = None, db: DBDependency = None):
    service = CaixaService(db)
    mid = service.abrir_movimento(caixa_id, usuario_id, valor_abertura, id_evento)
    if not mid:
        raise HTTPException(status_code=400, detail="Nao foi possivel abrir movimento.")
    return {"movimento_id": mid}


@router.post("/{movimento_id}/fechar")
def fechar_movimento(movimento_id: int, db: DBDependency):
    service = CaixaService(db)
    ok = service.fechar_movimento(movimento_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Nao foi possivel fechar movimento.")
    return {"status": "fechado"}
