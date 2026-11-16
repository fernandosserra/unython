# src/modules/relatorio.py
from typing import List, Dict, Any
from src.utils.database_manager import DatabaseManager
from src.modules.estoque import EstoqueService

class RelatorioService:
    """
    Gerencia a lógica de análise de dados e relatórios.
    Transforma dados brutos em inteligência gerencial.
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def gerar_faturamento_mensal(self) -> List[Dict[str, Any]]:
        """
        Calcula o faturamento total por mês (Ano-Mês) proveniente das vendas.
        Retorna uma lista de dicionários: [{'mes': '2025-10', 'faturamento_total': 150.50}, ...]
        """
        query = """
        SELECT 
            TO_CHAR(v.data_venda, 'YYYY-MM') AS mes, 
            SUM(iv.quantidade * iv.valor_unitario) AS faturamento_total
        FROM 
            vendas v
        INNER JOIN 
            itens_venda iv ON v.id = iv.id_venda
        GROUP BY 
            mes
        ORDER BY 
            mes;
        """
        try:
            columns, results = self.db.execute_query(query, fetch_all=True)
            if results:
                return [dict(zip(columns, row)) for row in results]
            return []
        except Exception as e:
            print(f" (Alerta Relatório): Falha ao gerar faturamento: {e}")
            return []

    def gerar_detalhe_agendamentos_pendentes(self) -> List[Dict[str, Any]]:
        """
        Busca todos os agendamentos com status 'Agendado' e junta com o nome da Pessoa e Facilitador.
        """
        query = """
        SELECT 
            a.id,
            p.nome AS pessoa,
            u.nome AS facilitador,
            a.data_hora,
            a.tipo_servico,
            a.compareceu
        FROM 
            agendamentos a
        INNER JOIN 
            pessoas p ON a.id_pessoa = p.id
        LEFT JOIN
            usuarios u ON a.id_facilitador = u.id
        WHERE
            a.status = 'Agendado'
        ORDER BY 
            a.data_hora;
        """
        try:
            columns, results = self.db.execute_query(query, fetch_all=True)
            if results:
                return [dict(zip(columns, row)) for row in results]
            return []
        except Exception as e:
            print(f" (Alerta Relatório): Falha ao gerar agendamentos pendentes: {e}")
            return []

    def calcular_saldo_fluxo_caixa(self) -> float:
        """
        Calcula o saldo total do fluxo de caixa (Receitas - Despesas).
        Considera apenas movimentos com status 'Ativo'.
        """
        query_receitas = """
        SELECT SUM(valor) FROM movimentos_financeiros 
        WHERE tipo_movimento = 'Receita' AND status = 'Ativo'
        """
        query_despesas = """
        SELECT SUM(valor) FROM movimentos_financeiros 
        WHERE tipo_movimento = 'Despesa' AND status = 'Ativo'
        """
        _, result_receitas = self.db.execute_query(query_receitas, fetch_one=True)
        _, result_despesas = self.db.execute_query(query_despesas, fetch_one=True)
        
        total_receitas = result_receitas[0] if result_receitas and result_receitas[0] is not None else 0.0
        total_despesas = result_despesas[0] if result_despesas and result_despesas[0] is not None else 0.0
        
        saldo = float(total_receitas) - float(total_despesas)
        return saldo

    def gerar_lucro_bruto_mensal(self) -> List[Dict[str, Any]]:
        """
        Calcula o lucro bruto total por mês, subtraindo o custo da venda.
        """
        query = """
        SELECT
            TO_CHAR(v.data_venda, 'YYYY-MM') AS mes,
            SUM(
                iv.quantidade * (iv.valor_unitario - i.valor_compra)
            ) AS lucro_bruto_total
        FROM 
            vendas v
        INNER JOIN 
            itens_venda iv ON v.id = iv.id_venda
        INNER JOIN
            itens i ON iv.id_item = i.id
        GROUP BY 
            mes
        ORDER BY 
            mes;
        """
        try:
            columns, results = self.db.execute_query(query, fetch_all=True)
            if results:
                return [dict(zip(columns, row)) for row in results]
            return []
        except Exception as e:
            print(f" (Alerta Lucro): Falha ao gerar relatório de lucro: {e}")
            return []

    def gerar_inventario_total(self) -> List[Dict[str, Any]]:
        """
        Gera o inventário completo agregando estoque e itens em uma única consulta SQL,
        eliminando o gargalo de N+1 queries.
        """
        query = """
        SELECT
            i.id,
            i.nome,
            i.valor_compra,
            i.valor_venda,
            COALESCE(
                SUM(CASE WHEN e.tipo_movimento = 'Entrada' THEN e.quantidade ELSE -e.quantidade END),
                0
            ) AS saldo_atual,
            COALESCE(
                SUM(CASE WHEN e.tipo_movimento = 'Entrada' THEN e.quantidade ELSE -e.quantidade END),
                0
            ) * i.valor_compra AS custo_total_estoque
        FROM
            itens i
        LEFT JOIN
            estoque e ON i.id = e.id_item
        WHERE
            i.status = 'Ativo'
        GROUP BY
            i.id, i.nome, i.valor_compra, i.valor_venda
        ORDER BY
            i.nome;
        """
        try:
            columns, results = self.db.execute_query(query, fetch_all=True)
            if results:
                return [dict(zip(columns, row)) for row in results]
            return []
        except Exception as e:
            print(f" (Alerta Inventário): Falha ao gerar inventário total: {e}")
            return []

    def gerar_despesas_por_categoria(self) -> List[Dict[str, Any]]:
        """
        Calcula o total gasto por categoria de despesa.
        """
        query = """
        SELECT
            categoria,
            SUM(valor) AS total_gasto
        FROM
            movimentos_financeiros
        WHERE
            tipo_movimento = 'Despesa'
            AND status = 'Ativo'
        GROUP BY
            categoria
        ORDER BY
            total_gasto DESC;
        """
        try:
            columns, results = self.db.execute_query(query, fetch_all=True)
            if results:
                return [dict(zip(columns, row)) for row in results]
            return []
        except Exception as e:
            print(f" (Alerta Despesas): Falha ao gerar relatório de despesas: {e}")
            return []
