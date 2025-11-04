# src/modules/agendamento.py
# O Serviço que liga Pessoa e Usuario no Tempo e Espaço

from src.utils.database_manager import DatabaseManager
from src.utils.models import Agendamento
from typing import Optional, List

class AgendamentoService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def registrar_agendamento(self, agendamento: Agendamento):
    # A query precisa do id_evento
        query = """
            INSERT INTO agendamentos 
            (id_pessoa, id_facilitador, data_hora, tipo_servico, status, id_evento) 
            VALUES (?, ?, ?, ?, ?, ?) RETURNING id
        """
        params = (
            agendamento.id_pessoa,
            agendamento.id_facilitador,
            agendamento.data_hora,
            agendamento.tipo_servico,
            agendamento.status,
            agendamento.id_evento  # <-- NOVO PARÂMETRO
    )
        return self.db.execute_query(query, params, commit=True)

    def buscar_agendamentos(self, id_pessoa: Optional[int] = None, id_facilitador: Optional[int] = None, status: Optional[str] = None) -> List[Agendamento]:
        """Busca agendamentos com filtros opcionais por Pessoa, Facilitador ou Status."""
        
        query = "SELECT id, id_pessoa, id_facilitador, data_hora, tipo_servico, status, id_evento FROM agendamentos"
        conditions = []
        params = []
        
        if id_pessoa is not None:
            conditions.append("id_pessoa = %s") # Postgres placeholder
            params.append(id_pessoa)
        
        if id_facilitador is not None:
            conditions.append("id_facilitador = %s") # Postgres placeholder
            params.append(id_facilitador)
            
        if status is not None: # <--- NOVA LÓGICA DE FILTRO POR STATUS
            conditions.append("status = %s") # Postgres placeholder
            params.append(status)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        # Adicionamos ORDER BY para consistência
        query += " ORDER BY data_hora DESC"
            
        columns, results = self.db.execute_query(query, tuple(params), fetch_all=True)
        
        if results:
            return [Agendamento(**dict(zip(columns, row))) for row in results]
        return []