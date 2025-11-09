# src/utils/models.py
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List, Tuple

@dataclass
class Pessoa:
    nome: str
    telefone: Optional[str] = None
    data_cadastro: Optional[date] = datetime.now().date()
    id: Optional[int] = None

@dataclass
class Usuario:
    nome: str
    email: str
    funcao: str
    hashed_password: Optional[str] = None
    role: str = 'Vendedor'
    status: str = 'Ativo'
    id: Optional[int] = None
    
@dataclass
class Item:
    nome: str
    valor_compra: float
    valor_venda: float
    status: str = 'Ativo'
    id: Optional[int] = None
    
@dataclass
class MovimentoEstoque:
    id_item: int
    quantidade: int
    tipo_movimento: str             # 'Entrada' ou 'Saída'
    origem_recurso: str = 'Doação'  # Ex: 'Doação', 'Compra_Fundo_Feirinha'
    id_usuario: Optional[int] = None
    id_evento: Optional[int] = None
    data_movimento: datetime = datetime.now()
    id: Optional[int] = None
    
@dataclass
class Evento:
    nome: str
    data_evento: datetime
    tipo: str
    status: str = 'Aberto'
    id: Optional[int] = None

@dataclass
class Agendamento:
    id_pessoa: int
    tipo_servico: str
    id_evento: int 
    id_facilitador: Optional[int] = None
    data_hora: datetime = datetime.now()
    status: str = 'Agendado'        
    # NOVO CAMPO CRÍTICO: Rastreamento de Presença
    # Opções: 'Pendente' (default), 'Sim', 'Não'
    compareceu: str = 'Pendente' 
    
    id: Optional[int] = None
    
@dataclass
class Venda:
    id_pessoa: Optional[int]
    responsavel: str
    id_evento: int                  # <--- CHAVE ESTRANGEIRA ADICIONADA!
    data_venda: Optional[date] = datetime.now().date()
    id: Optional[int] = None
    
@dataclass
class ItemVenda:
    # Esta é a Tabela de LIGAÇÃO (Um item em uma venda específica)
    id_venda: int
    id_item: int
    quantidade: int
    valor_unitario: float # O preço do momento da venda
    id: Optional[int] = None
    
@dataclass
class MovimentoFinanceiro:
    """Representa uma entrada ou saída financeira no fluxo de caixa."""
    id: Optional[int] = None
    data_registro: datetime = datetime.now()
    id_usuario: int = 0
    tipo_movimento: str = 'Receita'  # 'Receita' ou 'Despesa'
    valor: float = 0.0
    descricao: str = ""
    categoria: str = "Geral" # Ex: 'Aluguel', 'Doação', 'Salário'
    id_evento: Optional[int] = None # Para vincular a um evento específico
    status: str = 'Ativo' # 'Ativo' ou 'Cancelado'