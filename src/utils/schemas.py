from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, date
from decimal import Decimal

# --- 1. MODELOS DE ENTRADA (Para POST/PUT) ---

class CategoriaCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    descricao: Optional[str] = None
    status: str = 'Ativo'


class ItemBase(BaseModel):
    """Modelo base para criar ou atualizar um Item (Catalogo)."""
    nome: str = Field(..., min_length=2, max_length=255)
    valor_compra: Decimal = Field(..., gt=Decimal("0.0"))
    valor_venda: Decimal = Field(..., gt=Decimal("0.0"))
    status: str = 'Ativo'
    id_categoria: Optional[int] = None


class ItemVendaRequest(BaseModel):
    """Detalhe do item que está sendo vendido."""
    item_id: int = Field(..., gt=0, alias="itemId")
    quantidade: int = Field(..., gt=0)
    valor_unitario: Decimal = Field(..., gt=Decimal("0.0"))

    class Config:
        populate_by_name = True


class VendaCreate(BaseModel):
    """Modelo completo para criar uma transacao de venda."""
    id_pessoa: Optional[int] = Field(None, alias="pessoaId")
    responsavel_id: int = Field(..., alias="responsavelId")
    id_evento: int = Field(..., alias="eventoId")
    id_caixa: Optional[int] = Field(None, alias="caixaId")
    id_movimento_caixa: Optional[int] = Field(None, alias="movimentoCaixaId")
    itens: List[ItemVendaRequest]

    class Config:
        populate_by_name = True


class AgendamentoUpdateStatus(BaseModel):
    compareceu: Literal['Sim', 'Nao']


class AgendamentoStatusUpdateRequest(BaseModel):
    status: Literal['Aguardando', 'Chamado', 'Atendido', 'Ausente']


class OrganizacaoConfigSchema(BaseModel):
    nome_organizacao: str = Field(default="Terreiro Caboclo Pena Branca", min_length=2, max_length=150)
    tipo_organizacao: str = Field(..., min_length=2, max_length=100)
    termo_assistido: str = Field(..., min_length=2, max_length=50)
    termo_assistido_plural: str = Field(..., min_length=2, max_length=50)
    termo_atendente: str = Field(..., min_length=2, max_length=50)
    termo_servico: str = Field(..., min_length=2, max_length=50)


class PessoaCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=255)
    telefone: Optional[str] = None
    documento: Optional[str] = None
    preferencial: bool = False
    observacoes: Optional[str] = None


class PessoaResponse(BaseModel):
    id: int
    nome: str
    telefone: Optional[str] = None
    documento: Optional[str] = None
    preferencial: bool = False
    observacoes: Optional[str] = None
    data_cadastro: date

    class Config:
        from_attributes = True


class AcolhimentoCreateRequest(BaseModel):
    id_evento: int
    id_pessoa: Optional[int] = None
    nome: Optional[str] = None
    telefone: Optional[str] = None
    documento: Optional[str] = None
    preferencial: bool = False
    tipo_servico: Optional[str] = "Passe / Consulta"
    id_facilitador: Optional[int] = None
    observacoes: Optional[str] = None


class AgendamentoFilaItem(BaseModel):
    id: int
    id_pessoa: int
    pessoa: str
    telefone: Optional[str] = None
    documento: Optional[str] = None
    id_evento: int
    id_facilitador: Optional[int] = None
    facilitador: Optional[str] = None
    data_hora: datetime
    tipo_servico: str
    status: str
    compareceu: str
    numero_senha: Optional[str] = None
    preferencial: bool = False
    ordem_chegada: int = 1
    observacoes: Optional[str] = None

    class Config:
        from_attributes = True


class CaixaAbrirRequest(BaseModel):
    usuario_id: int = Field(..., gt=0)
    valor_abertura: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    id_evento: Optional[int] = None


class UsuarioCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=255)
    email: str = Field(..., min_length=5, max_length=255)
    funcao: Optional[str] = "Operador"
    role: str = "Vendedor"
    status: str = "Ativo"
    senha: str = Field(..., min_length=4)
    require_password_change: bool = False


class RoleUpdate(BaseModel):
    role: str
    status: str = "Ativo"
    funcao: Optional[str] = None


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
    id: int
    nome: str
    saldo_atual: int
    custo_total_estoque: Decimal
    valor_venda: Decimal

    class Config:
        from_attributes = True


class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: str
    funcao: Optional[str] = None
    role: str
    status: str
    require_password_change: bool = False

    class Config:
        from_attributes = True


# --- 3. AUTENTICACAO DA API ---

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
    role: str


class ChangePasswordRequest(BaseModel):
    email: str
    old_password: str
    new_password: str
