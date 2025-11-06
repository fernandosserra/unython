# app/routers/relatorios.py

from fastapi import APIRouter, Depends, status, HTTPException
from typing import List, Annotated, Dict, Any
import sys
import os
from decimal import Decimal # Necessário para o cálculo de soma do Inventário

# Adiciona o diretório 'src' para imports modulares
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Importa Services e Infraestrutura
from src.utils.dependencies import DBDependency
from src.modules.relatorio import RelatorioService
from src.modules.estoque import EstoqueService
from src.utils.schemas import InventarioResponse # Reutilizaremos este Schema para o Inventário

# Cria o Router para as rotas de relatórios
router = APIRouter(
    prefix="/relatorios",
    tags=["Análise e Fluxo de Caixa (Relatórios)"]
)

# ------------------------------------------------------------------
# 1. ENDPOINT: SALDO TOTAL DO FLUXO DE CAIXA
# ------------------------------------------------------------------

@router.get("/caixa/saldo", status_code=status.HTTP_200_OK)
def get_saldo_caixa(db: DBDependency):
    """Calcula e retorna o saldo total do caixa (Receitas - Despesas)."""
    relatorio_service = RelatorioService(db)
    
    saldo = relatorio_service.calcular_saldo_fluxo_caixa()
    
    return {
        "saldo_atual": f"R$ {saldo:.2f}",
        "valor_raw": float(saldo) # Retorna um float para fácil consumo pelo frontend
    }

# ------------------------------------------------------------------
# 2. ENDPOINT: DESPESAS POR CATEGORIA
# ------------------------------------------------------------------

@router.get("/despesas/categoria", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
def get_despesas_por_categoria(db: DBDependency):
    """Gera um relatório de soma total gasta por cada categoria (Ex: Material, Aluguel)."""
    relatorio_service = RelatorioService(db)
    
    despesas = relatorio_service.gerar_despesas_por_categoria()
    
    if not despesas:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma despesa ativa encontrada.")
         
    return despesas