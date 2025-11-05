# src/utils/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

# --- 1. MODELOS DE ENTRADA (Para POST/PUT) ---

class ItemBase(BaseModel):
    """Modelo base para criar ou atualizar um Item (Catálogo)."""
    nome: str = Field(..., min_length=2, max_length=255)
    valor_compra: float = Field(..., gt=0.0)
    valor_venda: float = Field(..., gt=0.0)
    status: str = 'Ativo'
    
class ItemVendaRequest(BaseModel):
    """Detalhe do item que está sendo vendido."""
    item_id: int = Field(..., gt=0, alias="itemId") # ID do Item no catálogo
    quantidade: int = Field(..., gt=0)
    valor_unitario: float = Field(..., gt=0.0) # Preço cobrado na hora da venda

    # Permite receber o campo com underscore (Python) ou camelCase (JS/Web)
    class Config:
        populate_by_name = True

class VendaCreate(BaseModel):
    """Modelo completo para criar uma transação de venda."""
    id_pessoa: Optional[int] = Field(None, alias="pessoaId") # Quem está comprando (opcional)
    responsavel_id: int = Field(..., alias="responsavelId") # Quem está registrando (id_usuario)
    id_evento: int = Field(..., alias="eventoId")          # Qual evento está ativo
    itens: List[ItemVendaRequest]
    
    class Config:
        populate_by_name = True

# --- 2. MODELOS DE SAÍDA (Para GET - O que a API retorna) ---

class ItemResponse(ItemBase):
    """Modelo completo para leitura, incluindo o ID do DB."""
    id: int
    
    # Configuração Pydantic (necessária para lidar com objetos ORM/DB, mesmo com o dataclass)
    class Config:
        from_attributes = True


class VendaResponse(BaseModel):
    id: int
    id_pessoa: Optional[int] = Field(None, alias="pessoaId")
    responsavel: str # ID do usuário que registrou
    id_evento: int = Field(..., alias="eventoId")
    data_venda: date # Retorna como Data
    
    class Config:
        from_attributes = True
        populate_by_name = True

# --- 3. MODELO DE SAÍDA PARA RELATÓRIO DE ESTOQUE ---

class InventarioResponse(BaseModel):
    """Modelo para relatórios que incluem dados calculados."""
    nome: str
    saldo_atual: int
    custo_total_estoque: float
    valor_venda: float
    # Note: O Pydantic lida com o tipo Decimal do Postgres/Numerics, mas 
    # para ser exibido, o valor é geralmente tratado como float/str na saída.
    
    class Config:
        from_attributes = True