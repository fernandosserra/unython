# src/utils/models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Tuple

@dataclass
class Pessoa:
    nome: str
    telefone: Optional[str] = None
    data_cadastro: Optional[str] = datetime.now().strftime("%Y-%m-%d")
    id: Optional[int] = None

@dataclass
class Usuario:
    nome: str
    email: str
    funcao: str
    status: str = 'Ativo'
    id: Optional[int] = None

@dataclass
class Agendamento:
    id_pessoa: int                  # Chave Estrangeira para Pessoa (Consulente)
    data_hora: str
    tipo_servico: str
    id_facilitador: Optional[int] = None # Chave Estrangeira para Usuario (Sacerdote)
    status: str = 'Agendado'
    id: Optional[int] = None

# ----------------- NOVOS MODELOS PARA FEIRINHA -----------------

@dataclass
class Item:
    nome: str
    valor_compra: float
    valor_venda: float
    status: str = 'Ativo'
    id: Optional[int] = None

@dataclass
class Venda:
    # A Venda principal é a transação:
    id_pessoa: Optional[int] # Quem comprou (referencia Pessoa)
    responsavel: str         # Quem registrou (referencia Usuario, ou string simples)
    data_venda: Optional[str] = datetime.now().strftime("%Y-%m-%d")
    id: Optional[int] = None
    
@dataclass
class ItemVenda:
    # Esta é a Tabela de LIGAÇÃO (Um item em uma venda específica)
    id_venda: int
    id_item: int
    quantidade: int
    valor_unitario: float # O preço do momento da venda
    id: Optional[int] = None