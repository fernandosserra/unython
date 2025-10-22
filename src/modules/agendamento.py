# src/modules/agendamento.py
# O Serviço que liga Pessoa e Usuario no Tempo e Espaço

from src.utils.database_manager import DatabaseManager
from src.utils.models import Agendamento
from typing import Optional, List

class AgendamentoService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def registrar_agendamento(self, agendamento: Agendamento):
        """Registra um agendamento usando os IDs de Pessoa e Facilitador."""
        query = """
            INSERT INTO agendamentos 
            (id_pessoa, id_facilitador, data_hora, tipo_servico, status) 
            VALUES (?, ?, ?, ?, ?)
        """
        params = (
            agendamento.id_pessoa,
            agendamento.id_facilitador,
            agendamento.data_hora,
            agendamento.tipo_servico,
            agendamento.status
        )
        # Retorna o ID do novo agendamento, se a função execute_query estiver correta.
        return self.db.execute_query(query, params, commit=True)

    def buscar_agendamentos(self, id_pessoa: Optional[int] = None, id_facilitador: Optional[int] = None) -> List[Agendamento]:
        """Busca agendamentos com filtros opcionais por Pessoa ou Facilitador."""
        query = "SELECT id, id_pessoa, id_facilitador, data_hora, tipo_servico, status FROM agendamentos"
        conditions = []
        params = []
        
        if id_pessoa is not None:
            conditions.append("id_pessoa = ?")
            params.append(id_pessoa)
        
        if id_facilitador is not None:
            conditions.append("id_facilitador = ?")
            params.append(id_facilitador)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        columns, results = self.db.execute_query(query, tuple(params), fetch_all=True)
        
        if results:
            return [Agendamento(**dict(zip(columns, row))) for row in results]
        return []