# src/modules/relatorio.py
from typing import List, Dict, Any
from src.utils.database_manager import DatabaseManager
from src.modules.estoque import EstoqueService

class RelatorioService:
    """
    Gerencia a lógica de análise de dados e relatórios.
    A Dimensão da Análise Genial, que transforma dados brutos em inteligência.
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def gerar_faturamento_mensal(self) -> List[Dict[str, Any]]:
        """
        Calcula o faturamento total por mês (Ano-Mês) proveniente das vendas.
        Retorna uma lista de dicionários: [{'mes': '2025-10', 'faturamento_total': 150.50}, ...]
        """
        # A Sintaxe Universal para Agregação no SQLite:
        query = """
        SELECT 
            -- Formata a data de venda para 'YYYY-MM' (Ex: 2025-11)
            TO_CHAR(v.data_venda, 'YYYY-MM') AS mes, 
            -- Soma o valor total de cada item na venda (quantidade * valor_unitario)
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
        
        # O Protocolo de Execução Segura:
        try:
            columns, results = self.db.execute_query(query, fetch_all=True)
            
            if results:
                # Transmutando Tuplas SQL para Dicionários (a forma ideal para relatórios)
                return [dict(zip(columns, row)) for row in results]
            return []
        except Exception as e:
            print(f" (Alerta Washu Relatório): Falha ao gerar faturamento: {e}")
            return []
            

    def gerar_detalhe_agendamentos_pendentes(self) -> List[Dict[str, Any]]:
        """
        Busca todos os agendamentos com status 'Agendado' e junta com o nome da Pessoa e Facilitador.
        """
        query = """
        SELECT 
            p.nome AS pessoa,
            u.nome AS facilitador,
            a.data_hora,
            a.tipo_servico
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
            # APENAS EXECUTA. Confia que a conexão está aberta pelo main.py.
            columns, results = self.db.execute_query(query, fetch_all=True)
            
            if results:
                return [dict(zip(columns, row)) for row in results]
            return []
        except Exception as e:
            # Captura o erro para logging, mas permite que o main.py faça o rollback geral
            print(f" (Alerta Washu Relatório): Falha ao gerar agendamentos pendentes: {e}")
            return []
        
    def calcular_saldo_fluxo_caixa(self) -> float:
        """
        Calcula o saldo total do fluxo de caixa (Receitas - Despesas).
        Considera apenas movimentos com status 'Ativo'.
        """
        
        # Consulta para somar receitas
        query_receitas = """
        SELECT SUM(valor) FROM movimentos_financeiros 
        WHERE tipo_movimento = 'Receita' AND status = 'Ativo'
        """
        
        # Consulta para somar despesas
        query_despesas = """
        SELECT SUM(valor) FROM movimentos_financeiros 
        WHERE tipo_movimento = 'Despesa' AND status = 'Ativo'
        """
        
        _, result_receitas = self.db.execute_query(query_receitas, fetch_one=True)
        _, result_despesas = self.db.execute_query(query_despesas, fetch_one=True)
        
        # Trata caso onde SUM retorna None (se não houver registros)
        total_receitas = result_receitas[0] if result_receitas and result_receitas[0] is not None else 0.0
        total_despesas = result_despesas[0] if result_despesas and result_despesas[0] is not None else 0.0
        
        saldo = total_receitas - total_despesas
        return saldo
    
    def gerar_lucro_bruto_mensal(self) -> List[Dict[str, Any]]:
        """
        Calcula o lucro bruto total por mês, subtraindo o custo da venda.
        """
        # CRÍTICO: INNER JOIN em 3 tabelas
        query = """
        SELECT
            -- 1. Agrupamento temporal
            TO_CHAR(v.data_venda, 'YYYY-MM') AS mes,
            
            -- 2. CÁLCULO DO LUCRO BRUTO:
            -- Lucro Bruto = SUM( Quantidade * (Valor de Venda - Custo de Compra) )
            SUM(
                iv.quantidade * (iv.valor_unitario - i.valor_compra)
            ) AS lucro_bruto_total
            
        FROM 
            vendas v
        INNER JOIN 
            itens_venda iv ON v.id = iv.id_venda  -- Liga o cabeçalho ao detalhe
        INNER JOIN
            itens i ON iv.id_item = i.id          -- Liga o detalhe ao catálogo para pegar o custo
        GROUP BY 
            mes
        ORDER BY 
            mes;
        """
        
        try:
            columns, results = self.db.execute_query(query, fetch_all=True)
            
            if results:
                # Transmutando Tuplas SQL para Dicionários
                return [dict(zip(columns, row)) for row in results]
            return []
        except Exception as e:
            print(f" (Alerta Washu Lucro): Falha ao gerar relatório de lucro: {e}")
            return []
        
        
    def gerar_inventario_total(self) -> List[Dict[str, Any]]:
        """
        Gera o inventário completo consultando itens e usando o EstoqueService 
        para calcular o saldo de cada item individualmente.
        """
        
        # 1. Consulta Apenas os Itens Ativos (Catálogo)
        query = "SELECT id, nome, valor_compra, valor_venda FROM itens WHERE status = 'Ativo'"
        columns, itens_raw = self.db.execute_query(query, fetch_all=True)

        if not itens_raw:
            return []
            
        inventario_completo = []
        estoque_service = EstoqueService(self.db) # Inicializa o serviço de estoque
        
        # 2. Itera sobre cada item para calcular o saldo (Método Híbrido)
        for row in itens_raw:
            item = dict(zip(columns, row))
            item_id = item['id']
            
            # Chama a lógica de cálculo de saldo que já está testada!
            saldo_atual = estoque_service.calcular_saldo_item(item_id)
            
            # Adiciona os campos calculados
            item['saldo_atual'] = saldo_atual
            item['custo_total_estoque'] = saldo_atual * item['valor_compra']
            
            inventario_completo.append(item)
            
        return inventario_completo
    
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
                # Transmutando Tuplas SQL para Dicionários
                return [dict(zip(columns, row)) for row in results]
            return []
        except Exception as e:
            print(f" (Alerta Washu Despesas): Falha ao gerar relatório de despesas: {e}")
            return []