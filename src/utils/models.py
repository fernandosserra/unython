# Unython - (C) 2025 siegrfried@gmail.com
# Este programa e software livre: voce pode redistribui-lo e/ou modifica-lo
# sob os termos da GNU General Public License como publicada pela Free Software Foundation,
# na versao 3 da Licenca, ou (a seu criterio) qualquer versao posterior.
# src/utils/models.py
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Pessoa:
    nome: str
    telefone: Optional[str] = None
    data_cadastro: date = field(default_factory=lambda: datetime.now().date())
    id: Optional[int] = None


@dataclass
class Usuario:
    nome: str
    email: str
    funcao: str
    hashed_password: Optional[str] = None
    require_password_change: bool = False
    role: str = "Vendedor"
    status: str = "Ativo"
    id: Optional[int] = None


@dataclass
class Item:
    nome: str
    valor_compra: Decimal
    valor_venda: Decimal
    id_categoria: Optional[int] = None
    status: str = "Ativo"
    id: Optional[int] = None


@dataclass
class Categoria:
    """Define categorias de produtos (Bebidas, Esotericos, etc.)."""

    nome: str
    descricao: Optional[str] = None
    status: str = "Ativo"
    id: Optional[int] = None


@dataclass
class MovimentoEstoque:
    id_item: int
    quantidade: int
    tipo_movimento: str  # 'Entrada' ou 'Saida'
    origem_recurso: str = "Doacao"
    id_usuario: Optional[int] = None
    id_evento: Optional[int] = None
    data_movimento: datetime = field(default_factory=datetime.now)
    id: Optional[int] = None


@dataclass
class Evento:
    nome: str
    data_evento: date
    tipo: str
    status: str = "Aberto"
    id: Optional[int] = None


@dataclass
class Agendamento:
    id_pessoa: int
    tipo_servico: str
    id_evento: int
    id_facilitador: Optional[int] = None
    data_hora: datetime = field(default_factory=datetime.now)
    status: str = "Agendado"
    compareceu: str = "Pendente"  # 'Pendente', 'Sim', 'Nao'
    id: Optional[int] = None


@dataclass
class ItemVenda:
    # Tabela de ligação (um item em uma venda específica)
    id_venda: int
    id_item: int
    quantidade: int
    valor_unitario: Decimal  # Preço no momento da venda
    id: Optional[int] = None


@dataclass
class Venda:
    id_pessoa: Optional[int]
    responsavel: str
    id_evento: int
    id_movimento_caixa: int  # Campo obrigatório
    data_venda: date = field(default_factory=lambda: datetime.now().date())
    id: Optional[int] = None


@dataclass
class MovimentoFinanceiro:
    """Representa uma entrada ou saída financeira no fluxo de caixa."""

    id: Optional[int] = None
    data_registro: datetime = field(default_factory=datetime.now)
    id_usuario: int = 0
    tipo_movimento: str = "Receita"  # 'Receita' ou 'Despesa'
    valor: Decimal = Decimal("0.00")
    descricao: str = ""
    categoria: str = "Geral"  # Ex: 'Aluguel', 'Doacao', 'Salario'
    id_evento: Optional[int] = None  # Vinculo a um evento específico
    status: str = "Ativo"  # 'Ativo' ou 'Cancelado'


@dataclass
class Caixa:
    """Representa um ponto de venda físico (Caixa)."""

    nome: str
    descricao: Optional[str] = None
    status: str = "Ativo"
    id: Optional[int] = None


@dataclass
class MovimentoCaixa:
    """Registra a abertura e fechamento de uma sessão de caixa."""

    id_caixa: int
    id_usuario_abertura: int
    valor_abertura: Decimal = Decimal("0.00")
    status: str = "Aberto"  # 'Aberto', 'Fechado'
    data_abertura: datetime = field(default_factory=datetime.now)
    data_fechamento: Optional[datetime] = None
    id: Optional[int] = None
