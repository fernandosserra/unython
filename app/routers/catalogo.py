# app/routers/catalogo.py

from fastapi import APIRouter, Depends, status, HTTPException
from typing import Dict, List, Any
import sys
import os

# Adiciona o diretório 'src'
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.dependencies import DBDependency
from src.modules.categoria import CategoriaService
from src.modules.item import ItemService
from src.utils.models import Categoria, Item

router = APIRouter(
    prefix="/catalogo",
    tags=["Catálogo (Grupos de Venda)"]
)

@router.get("/grupos", status_code=status.HTTP_200_OK)
def get_itens_agrupados_por_categoria(db: DBDependency):
    """Retorna o catálogo de itens agrupados por categoria para o PDV."""
    categoria_service = CategoriaService(db)
    
    # Chama o novo serviço para obter os dados agrupados
    data = categoria_service.buscar_itens_por_categoria()
    
    # Se não houver dados, retorna dict vazio (evita 404 no PDV)
    return data or {}


# --- Categorias ---
@router.get("/categorias")
def listar_categorias(db: DBDependency):
    service = CategoriaService(db)
    cats = service.buscar_todas_categorias()
    return [c.__dict__ for c in cats]


@router.post("/categorias", status_code=status.HTTP_201_CREATED)
def criar_categoria(categoria: Categoria, db: DBDependency):
    service = CategoriaService(db)
    cid = service.registrar_categoria(categoria)
    return {"id": cid}


# --- Itens ---
@router.get("/itens")
def listar_itens(db: DBDependency):
    item_service = ItemService(db)
    query = "SELECT id, nome, valor_compra, valor_venda, status, id_categoria FROM itens WHERE status = 'Ativo' ORDER BY nome"
    columns, results = item_service.db.execute_query(query, fetch_all=True)
    if results:
        return [dict(zip(columns, row)) for row in results]
    return []


@router.post("/itens", status_code=status.HTTP_201_CREATED)
def criar_item(item: Item, db: DBDependency):
    item_service = ItemService(db)
    iid = item_service.registrar_item(item)
    return {"id": iid}
