from pydantic import BaseModel, Field, validator
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
    valor_compra: Optional[Decimal] = Field(default=None, ge=Decimal("0.0"))
    valor_venda: Decimal = Field(..., gt=Decimal("0.0"))
    status: str = 'Ativo'
    id_categoria: Optional[int] = None
    estoque_minimo: int = Field(default=0, ge=0)


class FacilitadorCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=255)
    especialidade: Optional[str] = Field(None, max_length=255)
    observacoes: Optional[str] = None
    status: Literal['Ativo', 'Inativo'] = 'Ativo'

    @validator('nome', pre=True)
    def limpar_nome(cls, value):
        return value.strip() if isinstance(value, str) else value


class AtividadeCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=255)
    descricao: Optional[str] = None
    status: Literal['Ativo', 'Inativo'] = 'Ativo'

    @validator('nome', pre=True)
    def limpar_nome(cls, value):
        return value.strip() if isinstance(value, str) else value


class DoacaoCreate(BaseModel):
    valor: Decimal = Field(..., gt=Decimal("0"), max_digits=10, decimal_places=2)
    data: date
    nome_doador: Optional[str] = Field(None, max_length=255)
    forma_pagamento: Optional[str] = Field(None, max_length=100)
    descricao: Optional[str] = None
    id_evento: Optional[int] = Field(None, gt=0)


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
    responsavel_id: Optional[int] = Field(None, alias="responsavelId")
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
    termo_atividade: str = Field(default="Entidade / Serviço", min_length=2, max_length=50)
    alias_evento: str = Field(default="Evento", min_length=2, max_length=50)
    subtitulo: Optional[str] = None
    registro: Optional[str] = None
    cidade_uf: Optional[str] = None
    telefone_contato: Optional[str] = None
    termo_atendente_plural: str = Field(default="Médiuns / Cambones", min_length=2, max_length=50)
    termo_atividade_plural: str = Field(default="Entidades / Serviços", min_length=2, max_length=50)
    alias_evento_plural: str = Field(default="Eventos", min_length=2, max_length=50)
    habilitar_pdv: bool = True
    habilitar_atendimentos: bool = True
    habilitar_doacoes: bool = True
    exigir_documento_atendimento: bool = False


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
    tipo_servico: Optional[str] = None
    id_facilitador: Optional[int] = None
    id_atividade: Optional[int] = None
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
    id_atividade: Optional[int] = None
    atividade: Optional[str] = None
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
    usuario_id: Optional[int] = Field(None, gt=0)
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
    permissoes: Optional[List[Literal['pdv', 'caixa', 'atendimentos', 'doacoes', 'estoque', 'relatorios', 'eventos']]] = None

    @validator('permissoes')
    def permissoes_unicas(cls, value):
        if value is not None and len(value) != len(set(value)):
            raise ValueError('Permissões duplicadas não são permitidas.')
        return value


class RoleUpdate(BaseModel):
    role: str
    status: str = "Ativo"
    funcao: Optional[str] = None


class PermissoesUpdate(BaseModel):
    permissoes: Optional[List[Literal['pdv', 'caixa', 'atendimentos', 'doacoes', 'estoque', 'relatorios', 'eventos']]]

    @validator('permissoes')
    def permissoes_unicas(cls, value):
        if value is not None and len(value) != len(set(value)):
            raise ValueError('Permissões duplicadas não são permitidas.')
        return value


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


class VendaItemHistorico(BaseModel):
    id_item: int
    nome: str
    quantidade: int
    valor_unitario: Decimal
    subtotal: Decimal


class VendaRecenteResponse(BaseModel):
    id: int
    id_pessoa: Optional[int] = None
    responsavel: str
    id_evento: int
    data_venda: date
    data_hora_venda: Optional[datetime] = None
    itens: List[VendaItemHistorico] = Field(default_factory=list)
    total: Decimal = Decimal("0.00")


class InventarioResponse(BaseModel):
    id: int
    nome: str
    saldo_atual: int
    custo_total_estoque: Decimal
    valor_venda: Decimal
    valor_compra: Optional[Decimal] = None

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
    permissoes: Optional[List[str]] = None

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
    permissoes: Optional[List[str]] = None


class ChangePasswordRequest(BaseModel):
    email: str
    old_password: str
    new_password: str
