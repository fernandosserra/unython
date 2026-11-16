# app/routers/catalogo.py

from fastapi import APIRouter, Depends, status, HTTPException
from typing import Dict, List, Any

from src.utils.dependencies import DBDependency
from src.modules.categoria import CategoriaService
from src.modules.item import ItemService
from src.utils.models import Categoria, Item
from src.utils.schemas import CategoriaCreate, ItemBase

router = APIRouter(
    prefix="/catalogo",
    tags=["Catálogo (Grupos de Venda)"]
)

@router.get("/grupos", status_code=status.HTTP_200_OK)
def get_itens_agrupados_por_categoria(db: DBDependency):
    """Retorna o catálogo de itens agrupados por categoria para o PDV."""
    categoria_service = CategoriaService(db)
    data = categoria_service.buscar_itens_por_categoria()
    return data or {}


# --- Categorias ---
@router.get("/categorias")
def listar_categorias(db: DBDependency):
    service = CategoriaService(db)
    cats = service.buscar_todas_categorias()
    return [c.__dict__ for c in cats]


@router.post("/categorias", status_code=status.HTTP_201_CREATED)
def criar_categoria(payload: CategoriaCreate, db: DBDependency):
    service = CategoriaService(db)
    cat = Categoria(
        nome=payload.nome,
        descricao=payload.descricao,
        status=payload.status,
    )
    cid = service.registrar_categoria(cat)
    if not cid:
        raise HTTPException(status_code=400, detail="Não foi possível criar categoria.")
    return {"id": cid, "nome": payload.nome}


# --- Itens ---
@router.get("/itens")
def listar_itens(db: DBDependency):
    item_service = ItemService(db)
    itens = item_service.buscar_todos_itens(apenas_ativos=False)
    return [i.__dict__ for i in itens]


@router.post("/itens", status_code=status.HTTP_201_CREATED)
def criar_item(payload: ItemBase, db: DBDependency):
    item_service = ItemService(db)
    item = Item(
        nome=payload.nome,
        valor_compra=payload.valor_compra,
        valor_venda=payload.valor_venda,
        id_categoria=payload.id_categoria,
        status=payload.status,
    )
    iid = item_service.registrar_item(item)
    if not iid:
        raise HTTPException(status_code=400, detail="Não foi possível cadastrar o item.")
    return {"id": iid, "nome": payload.nome}
