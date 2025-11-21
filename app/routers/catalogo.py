# app/routers/catalogo.py

from fastapi import APIRouter, Depends, status, HTTPException
from typing import Dict, List, Any
import sys
import os

# Adiciona o diretório 'src'
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.dependencies import DBDependency
from src.modules.categoria import CategoriaService

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
    
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma categoria ativa ou itens encontrados.")
        
    return data