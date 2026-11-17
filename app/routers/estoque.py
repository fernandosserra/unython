from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

from src.utils.dependencies import DBDependency, require_role
from src.modules.estoque import EstoqueService
from src.utils.models import Usuario

router = APIRouter(prefix="/estoque", tags=["Estoque"])
ADMIN_ONLY = require_role({"Administrador"})


class MovimentoEstoqueRequest(BaseModel):
    item_id: int = Field(..., alias="itemId", gt=0)
    quantidade: int = Field(..., gt=0)
    origem_recurso: Optional[str] = None
    usuario_id: int = Field(..., alias="usuarioId", gt=0)
    evento_id: int = Field(..., alias="eventoId", gt=0)

    class Config:
        populate_by_name = True


@router.post("/entrada", status_code=status.HTTP_201_CREATED)
def registrar_entrada(
    mov: MovimentoEstoqueRequest,
    db: DBDependency,
    current_user: Usuario = Depends(ADMIN_ONLY),
):
    service = EstoqueService(db)
    mid = service.entrada_item(
        id_item=mov.item_id,
        quantidade=mov.quantidade,
        origem_recurso=mov.origem_recurso or "Ajuste",
        id_usuario=mov.usuario_id,
        id_evento=mov.evento_id,
    )
    if not mid:
        raise HTTPException(status_code=400, detail="Falha ao registrar entrada.")
    return {"id": mid}


@router.post("/saida", status_code=status.HTTP_201_CREATED)
def registrar_saida(
    mov: MovimentoEstoqueRequest,
    db: DBDependency,
    current_user: Usuario = Depends(ADMIN_ONLY),
):
    service = EstoqueService(db)
    mid = service.saida_item(
        id_item=mov.item_id,
        quantidade=mov.quantidade,
        id_usuario=mov.usuario_id,
        id_evento=mov.evento_id,
        origem_recurso=mov.origem_recurso or "Consumo Interno",
    )
    if not mid:
        raise HTTPException(status_code=400, detail="Falha ao registrar saída.")
    return {"id": mid}


@router.get("/saldo/{item_id}")
def saldo_item(item_id: int, db: DBDependency):
    service = EstoqueService(db)
    saldo = service.calcular_saldo_item(item_id)
    return {"item_id": item_id, "saldo": saldo}


@router.get("/movimentos/{item_id}")
def movimentos_item(item_id: int, db: DBDependency):
    service = EstoqueService(db)
    movimentos = service.buscar_movimentos_por_item(item_id)
    return [m.__dict__ for m in movimentos]
