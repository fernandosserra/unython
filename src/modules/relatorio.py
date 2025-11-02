# src/modules/relatorio.py
from src.utils.database_manager import DatabaseManager
from typing import List, Dict, Any

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
            strftime('%Y-%m', v.data_venda) AS mes, 
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
            # O RelatorioService assume o controle da conexão para garantir o ciclo completo da análise.
            self.db.connect() 
            columns, results = self.db.execute_query(query, fetch_all=True)
            
            if results:
                # Transmutando Tuplas SQL para Dicionários (a forma ideal para relatórios)
                return [dict(zip(columns, row)) for row in results]
            return []
        except Exception as e:
            print(f" (Alerta Washu Relatório): Falha ao gerar faturamento: {e}")
            return []
        finally:
            self.db.disconnect()
            

    def gerar_detalhe_agendamentos_pendentes(self) -> List[Dict[str, Any]]:
        """
        Busca todos os agendamentos com status 'Agendado' e junta com o nome da Pessoa e Facilitador.
        """
        # A Sintaxe Universal para Joins:
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
            usuarios u ON a.id_facilitador = u.id -- LEFT JOIN para caso o facilitador seja opcional/nulo
        WHERE
            a.status = 'Agendado'
        ORDER BY 
            a.data_hora;
        """
        
        try:
            self.db.connect()
            columns, results = self.db.execute_query(query, fetch_all=True)
            
            if results:
                # Transmutando Tuplas SQL para Dicionários
                return [dict(zip(columns, row)) for row in results]
            return []
        except Exception as e:
            print(f" (Alerta Washu Relatório): Falha ao gerar agendamentos pendentes: {e}")
            return []
        finally:
            self.db.disconnect()