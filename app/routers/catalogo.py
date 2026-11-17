# app/routers/catalogo.py

from fastapi import APIRouter, Depends, status, HTTPException
from typing import Dict, List, Any

from src.utils.dependencies import DBDependency, get_current_user, require_module
from src.modules.categoria import CategoriaService
from src.modules.item import ItemService
from src.utils.models import Categoria, Item, Usuario
from src.utils.schemas import CategoriaCreate, ItemBase

router = APIRouter(
    prefix="/catalogo",
    tags=["Catálogo (Grupos de Venda)"]
)
CATALOGO_WRITE = require_module("estoque", legacy_admin_only=True)
CATALOGO_READ = require_module("pdv", "estoque", check_features=False)

@router.get("/grupos", status_code=status.HTTP_200_OK, dependencies=[Depends(CATALOGO_READ)])
def get_itens_agrupados_por_categoria(db: DBDependency):
    """Retorna o catálogo de itens agrupados por categoria para o PDV."""
    categoria_service = CategoriaService(db)
    data = categoria_service.buscar_itens_por_categoria()
    return data or {}


# --- Categorias ---
@router.get("/categorias", dependencies=[Depends(CATALOGO_READ)])
def listar_categorias(db: DBDependency):
    service = CategoriaService(db)
    cats = service.buscar_todas_categorias()
    return [c.__dict__ for c in cats]


@router.post("/categorias", status_code=status.HTTP_201_CREATED, dependencies=[Depends(CATALOGO_WRITE)])
def criar_categoria(
    payload: CategoriaCreate,
    db: DBDependency,
    current_user: Usuario = Depends(get_current_user),
):
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
@router.get("/itens", dependencies=[Depends(CATALOGO_READ)])
def listar_itens(db: DBDependency):
    item_service = ItemService(db)
    itens = item_service.buscar_todos_itens(apenas_ativos=False)
    return [i.__dict__ for i in itens]


@router.post("/itens", status_code=status.HTTP_201_CREATED, dependencies=[Depends(CATALOGO_WRITE)])
def criar_item(
    payload: ItemBase,
    db: DBDependency,
    current_user: Usuario = Depends(get_current_user),
):
    item_service = ItemService(db)
    existente = item_service.buscar_item_por_nome(payload.nome)
    minimo = payload.estoque_minimo
    if existente and "estoque_minimo" not in payload.model_fields_set:
        minimo = existente.estoque_minimo
    valor_compra = payload.valor_compra
    if existente and "valor_compra" not in payload.model_fields_set:
        valor_compra = existente.valor_compra
    item = Item(
        nome=payload.nome,
        valor_compra=valor_compra,
        valor_venda=payload.valor_venda,
        id_categoria=payload.id_categoria,
        status=payload.status,
        estoque_minimo=minimo,
    )
    iid = item_service.registrar_item(item)
    if not iid:
        raise HTTPException(status_code=400, detail="Não foi possível cadastrar o item.")
    return {"id": iid, "nome": payload.nome}


@router.put("/itens/{item_id}", dependencies=[Depends(CATALOGO_WRITE)])
def atualizar_item(
    item_id: int,
    payload: ItemBase,
    db: DBDependency,
    current_user: Usuario = Depends(get_current_user),
):
    service = ItemService(db)
    if not service.buscar_item_por_id(item_id):
        raise HTTPException(status_code=404, detail="Item não encontrado.")
    service.editar_item(item_id, payload.nome, payload.valor_compra, payload.valor_venda,
                        payload.status, payload.id_categoria, payload.estoque_minimo)
    return {"id": item_id, "nome": payload.nome}
