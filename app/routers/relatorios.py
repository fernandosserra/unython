# app/routers/relatorios.py

from fastapi import APIRouter, Depends, status, HTTPException
from typing import List, Annotated, Dict, Any
import sys
import os
from decimal import Decimal # Necessário para o cálculo de soma do Inventário

# Adiciona o diretório 'src' para imports modulares
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Importa Services e Infraestrutura
from src.utils.dependencies import DBDependency, get_current_user, require_module
from src.modules.relatorio import RelatorioService
from src.modules.estoque import EstoqueService
from src.utils.models import Usuario
from src.utils.schemas import InventarioResponse # Reutilizaremos este Schema para o Inventário

# Cria o Router para as rotas de relatórios
router = APIRouter(
    prefix="/relatorios",
    tags=["Análise e Fluxo de Caixa (Relatórios)"]
)
RELATORIOS_READ = require_module("relatorios", legacy_allow=True)
RELATORIOS_GERENCIAL = require_module("relatorios", legacy_admin_only=True)

# ------------------------------------------------------------------
# 1. ENDPOINT: SALDO TOTAL DO FLUXO DE CAIXA
# ------------------------------------------------------------------

@router.get("/caixa/saldo", status_code=status.HTTP_200_OK, dependencies=[Depends(RELATORIOS_READ)])
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

@router.get("/despesas/categoria", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK, dependencies=[Depends(RELATORIOS_READ)])
def get_despesas_por_categoria(db: DBDependency):
    """Gera um relatório de soma total gasta por cada categoria (Ex: Material, Aluguel)."""
    relatorio_service = RelatorioService(db)
    
    despesas = relatorio_service.gerar_despesas_por_categoria()
    
    if not despesas:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma despesa ativa encontrada.")
         
    return despesas


# ------------------------------------------------------------------
# 3. ENDPOINT: RELATÓRIO GERENCIAL
# ------------------------------------------------------------------

@router.get("/relatorio-gerencial", dependencies=[Depends(RELATORIOS_GERENCIAL)])
def get_relatorio_gerencial(
    db: DBDependency,
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    """
    Gera um relatório gerencial para usuários autorizados ao módulo de relatórios.
    """
    # Se o código chegou aqui, o usuário está autenticado E autorizado.
    
    # Exemplo de uso do usuário (opcional)
    print(f"Relatório acessado por: {current_user.nome} ({current_user.role})")
    
    # ... Lógica de geração do relatório
    return {"status": "ok", "dados": "Relatório Confidencial Gerencial"}



# ------------------------------------------------------------------
# 4. ENDPOINT: INVENTÁRIO / RELATÓRIO DE ESTOQUE
# ------------------------------------------------------------------

@router.get("/projecao-estoque", dependencies=[Depends(RELATORIOS_READ)])
def get_projecao_estoque(db: DBDependency):
    query = """
    SELECT id, nome, saldo_atual, estoque_minimo, valor_compra,
           estoque_minimo - saldo_atual AS quantidade_repor,
           (estoque_minimo - saldo_atual) * COALESCE(valor_compra, 0) AS custo_previsto
    FROM (
        SELECT i.id, i.nome, i.estoque_minimo, i.valor_compra,
               COALESCE(SUM(CASE WHEN e.tipo_movimento = 'Entrada'
                                 THEN e.quantidade ELSE -e.quantidade END), 0) AS saldo_atual
        FROM itens i LEFT JOIN estoque e ON e.id_item = i.id
        WHERE i.status = 'Ativo'
        GROUP BY i.id, i.nome, i.estoque_minimo, i.valor_compra
    ) saldos
    WHERE saldo_atual < estoque_minimo
    ORDER BY nome, id
    """
    columns, rows = db.execute_query(query, fetch_all=True)
    itens = [dict(zip(columns, row)) for row in rows]
    columns, rows = db.execute_query(
        "SELECT id, nome FROM itens WHERE status = 'Ativo' AND valor_compra IS NULL ORDER BY nome, id",
        fetch_all=True,
    )
    return {"itens": itens, "total_previsto": sum((item["custo_previsto"] for item in itens), Decimal("0")),
            "sem_preco": [dict(zip(columns, row)) for row in rows]}


@router.get("/inventario", response_model=List[InventarioResponse], status_code=status.HTTP_200_OK, dependencies=[Depends(RELATORIOS_READ)])
def get_inventario(db: DBDependency):
    """
    Retorna o inventário consolidado: cada item do catálogo com seu saldo atual,
    custo total em estoque e valor de venda unitário.
    """
    query = """
    SELECT 
        i.id,
        i.nome,
        i.valor_compra,
        COALESCE(
            SUM(CASE WHEN e.tipo_movimento = 'Entrada' THEN e.quantidade ELSE -e.quantidade END),
            0
        ) AS saldo_atual,
        i.valor_compra * COALESCE(
            SUM(CASE WHEN e.tipo_movimento = 'Entrada' THEN e.quantidade ELSE -e.quantidade END),
            0
        ) AS custo_total_estoque,
        i.valor_venda
    FROM 
        itens i
    LEFT JOIN 
        estoque e ON e.id_item = i.id
    WHERE 
        i.status = 'Ativo'
    GROUP BY 
        i.id, i.nome, i.valor_compra, i.valor_venda
    ORDER BY 
        i.nome ASC
    """
    
    try:
        columns, results = db.execute_query(query, fetch_all=True)
        if not results:
            return []
        
        inventario = []
        for row in results:
            data = dict(zip(columns, row))
            inventario.append(InventarioResponse(
                id=data['id'],
                nome=data['nome'],
                saldo_atual=int(data.get('saldo_atual', 0) or 0),
                custo_total_estoque=Decimal(str(data.get('custo_total_estoque', 0) or 0)),
                valor_venda=Decimal(str(data.get('valor_venda', 0) or 0)),
                valor_compra=data['valor_compra'],
            ))
        return inventario
    except Exception as e:
        print(f"Erro ao gerar inventário: {e}")
        return []
