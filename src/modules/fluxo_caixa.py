# src/modules/fluxo_caixa.py

from typing import List, Optional, Dict, Any
from src.utils.database_manager import DatabaseManager
from src.utils.models import MovimentoFinanceiro # Importar o dataclass que acabamos de criar

class FluxoDeCaixaService:
    """
    Gerencia a lógica de registro e consulta de Movimentos Financeiros
    (Contas a Pagar e Receber, Doações, Despesas).
    """

    def __init__(self, db_manager: DatabaseManager):
        # Injeção de Dependência: Recebe a conexão com o DB
        self.db = db_manager

    def _transmutar_movimento(self, columns: List[str], results: List[Any]) -> List[MovimentoFinanceiro]:
        """Converte resultados de query em objetos MovimentoFinanceiro."""
        movimentos: List[MovimentoFinanceiro] = []
        if not results:
            return movimentos

        for row in results:
            data_dict = dict(zip(columns, row))
            
            # Garante que o ID de Evento seja None se for 0 (do SQL)
            if data_dict.get('id_evento') == 0:
                data_dict['id_evento'] = None
            
            movimentos.append(MovimentoFinanceiro(**data_dict))
        
        return movimentos

    def registrar_movimento(self, movimento: MovimentoFinanceiro) -> Optional[int]:
        """Registra um novo movimento (Receita ou Despesa) no banco de dados."""
        
        query = """
        INSERT INTO movimentos_financeiros (
            data_registro, id_usuario, tipo_movimento, valor, descricao, categoria, id_evento
        ) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        """
        
        values = (
            movimento.data_registro,
            movimento.id_usuario,
            movimento.tipo_movimento,
            movimento.valor,
            movimento.descricao,
            movimento.categoria,
            movimento.id_evento
        )
        
        try:
            # Usamos commit=True aqui, pois cada movimento financeiro é atômico
            last_id = self.db.execute_query(query, values, commit=True)
            if last_id:
                print(f" -> Movimento Financeiro de {movimento.tipo_movimento} ({movimento.categoria}) registrado com ID: {last_id}")
            return last_id
        except Exception as e:
            print(f" (Alerta Washu: Falha ao registrar Movimento Financeiro) Erro: {e}")
            return None

    def buscar_todos_movimentos(self) -> List[MovimentoFinanceiro]:
        """Busca e retorna todos os movimentos financeiros ativos."""
        query = "SELECT * FROM movimentos_financeiros WHERE status = 'Ativo' ORDER BY data_registro DESC"
        columns, results = self.db.execute_query(query)
        return self._transmutar_movimento(columns, results)