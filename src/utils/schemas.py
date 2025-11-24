# src/utils/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, date

# --- 1. MODELOS DE ENTRADA (Para POST/PUT) ---

class ItemBase(BaseModel):
    """Modelo base para criar ou atualizar um Item (Catalogo)."""
    nome: str = Field(..., min_length=2, max_length=255)
    valor_compra: float = Field(..., gt=0.0)
    valor_venda: float = Field(..., gt=0.0)
    status: str = 'Ativo'
    
class ItemVendaRequest(BaseModel):
    """Detalhe do item que está sendo vendido."""
    item_id: int = Field(..., gt=0, alias="itemId")
    quantidade: int = Field(..., gt=0)
    valor_unitario: float = Field(..., gt=0.0)

    class Config:
        populate_by_name = True

class VendaCreate(BaseModel):
    """Modelo completo para criar uma transação de venda."""
    id_pessoa: Optional[int] = Field(None, alias="pessoaId")
    responsavel_id: int = Field(..., alias="responsavelId")
    id_evento: int = Field(..., alias="eventoId")
    id_caixa: Optional[int] = Field(None, alias="caixaId")
    itens: List[ItemVendaRequest]
    
    class Config:
        populate_by_name = True
        
class AgendamentoUpdateStatus(BaseModel):
    compareceu: Literal['Sim', 'Nao']

# --- 2. MODELOS DE SAIDA (Para GET) ---

class ItemResponse(ItemBase):
    id: int
    
    class Config:
        from_attributes = True


class VendaResponse(BaseModel):
    id: int
    id_pessoa: Optional[int] = Field(None, alias="pessoaId")
    responsavel: str
    id_evento: int = Field(..., alias="eventoId")
    data_venda: date
    
    class Config:
        from_attributes = True
        populate_by_name = True

class InventarioResponse(BaseModel):
    nome: str
    saldo_atual: int
    custo_total_estoque: float
    valor_venda: float
    
    class Config:
        from_attributes = True
        
# --- 4. AUTENTICACAO DA API ---

class LoginRequest(BaseModel):
    email: str
    password: str
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    require_password_change: bool


class ChangePasswordRequest(BaseModel):
    email: str
    old_password: str
    new_password: str
