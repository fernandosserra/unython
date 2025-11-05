# app/routers/estoque.py

from fastapi import APIRouter, Depends, status, HTTPException
from typing import List, Annotated
from decimal import Decimal
import sys
import os

# Adiciona o diretório 'src' para imports modulares
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Importa Services, Infraestrutura e Schemas
from src.utils.database_manager import DatabaseManager # Não precisa do import de DB_CONFIG
from src.modules.item import ItemService
from src.modules.estoque import EstoqueService
from src.utils.schemas import ItemBase, ItemResponse, InventarioResponse # Schemas

# Dependência do DB (do dependencies.py)
from src.utils.dependencies import DBDependency

# Cria o Router para as rotas de estoque
router = APIRouter(
    prefix="/estoque",
    tags=["Estoque & Itens (Inventário)"]
)

# ------------------------------------------------------------------
# 1. ENDPOINT: LISTAR CATÁLOGO (ITENS ATIVOS)
# ------------------------------------------------------------------

@router.get("/itens", response_model=List[ItemResponse], status_code=status.HTTP_200_OK)
def listar_itens(db: DBDependency):
    """Lista todos os itens ativos no catálogo da feirinha."""
    item_service = ItemService(db)
    
    # O ItemService.buscar_todos_itens já retorna uma lista de objetos Item (dataclasses)
    itens = item_service.buscar_todos_itens()
    
    # O FastAPI tentará converter a lista de Item (dataclass) para List[ItemResponse] (Pydantic)
    return itens

# ------------------------------------------------------------------
# 2. ENDPOINT: REGISTRAR NOVO ITEM
# ------------------------------------------------------------------

@router.post("/itens", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def registrar_novo_item(item_data: ItemBase, db: DBDependency):
    """
    Registra um novo item no catálogo.
    A validação de entrada é feita automaticamente pelo Pydantic (ItemBase).
    """
    item_service = ItemService(db)
    
    # Verifica se já existe um item com o mesmo nome (lógica de UPSERT)
    item_existente = item_service.buscar_item_por_nome(item_data.nome)
    if item_existente:
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Item '{item_data.nome}' já existe no catálogo com ID {item_existente.id}. Use PUT para atualizar."
        )

    # Convertendo Pydantic Base para o Dataclass de Persistência (Item)
    # Assumindo que você tem um construtor que aceita os campos de ItemBase no seu dataclass Item
    from src.utils.models import Item 
    
    novo_item = Item(**item_data.model_dump())
    
    item_id = item_service.registrar_item(novo_item)
    
    if not item_id:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao registrar item no DB.")

    # Retorna o item recém-criado, incluindo o ID gerado
    novo_item.id = item_id
    return novo_item

# ------------------------------------------------------------------
# 3. ENDPOINT: CALCULAR INVENTÁRIO TOTAL
# ------------------------------------------------------------------

@router.get("/inventario", response_model=List[InventarioResponse], status_code=status.HTTP_200_OK)
def calcular_inventario(db: DBDependency):
    """
    Calcula e retorna o saldo e o custo total de todo o inventário ativo.
    """
    from src.modules.relatorio import RelatorioService
    relatorio_service = RelatorioService(db)
    
    inventario = relatorio_service.gerar_inventario_total()
    
    if not inventario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhum item ativo encontrado.")
    
    # O relatório retorna List[Dict], Pydantic aceitará a conversão
    return inventario

# ------------------------------------------------------------------
# 4. ENDPOINT: SALDO DE UM ÚNICO ITEM
# ------------------------------------------------------------------
@router.get("/saldo/{item_id}", status_code=status.HTTP_200_OK)
def verificar_saldo_item(item_id: int, db: DBDependency):
    """Retorna o saldo atual (quantidade) e o custo de um item específico."""
    
    estoque_service = EstoqueService(db)
    item_service = ItemService(db)

    # 1. Checa o Saldo
    saldo = estoque_service.calcular_saldo_item(item_id)

    # 2. Busca o Catálogo para obter Preço e Nome
    item_catalogo = item_service.buscar_item_por_id(item_id)
    
    if not item_catalogo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item não encontrado no catálogo.")
        
    # 3. Calcula o Custo Total
    custo_total = Decimal(saldo) * item_catalogo.valor_compra
    
    # 4. Retorna no formato InventarioResponse (para consistência de dados)
    return {
        "nome": item_catalogo.nome,
        "saldo_atual": saldo,
        "custo_total_estoque": custo_total,
        "valor_venda": item_catalogo.valor_venda
    }