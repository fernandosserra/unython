# src/modules/evento.py
from typing import Optional, List
from datetime import date

from src.utils.database_manager import DatabaseManager
from src.utils.models import Evento


class EventoService:
    """Gerencia a criação e controle do ciclo de Eventos (Dias Fiscais)."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def registrar_evento(self, evento: Evento) -> Optional[int]:
        query = "INSERT INTO eventos (nome, data_evento, tipo, status) VALUES (%s, %s, %s, %s) RETURNING id"
        params = (evento.nome, evento.data_evento, evento.tipo, evento.status)
        return self.db.execute_query(query, params, commit=True)

    def buscar_evento_aberto(self) -> Optional[Evento]:
        query = "SELECT id, nome, data_evento, tipo, status FROM eventos WHERE status = 'Aberto' LIMIT 1"
        columns, result = self.db.execute_query(query, fetch_one=True)
        if result:
            return Evento(**dict(zip(columns, result)))
        return None

    def fechar_evento(self, id_evento: int) -> bool:
        query = "UPDATE eventos SET status = 'Fechado' WHERE id = %s"
        return self.db.execute_query(query, (id_evento,), commit=True)

    def buscar_eventos(self, data_inicio: Optional[date] = None, data_fim: Optional[date] = None) -> List[Evento]:
        base = "SELECT id, nome, data_evento, tipo, status FROM eventos"
        params = []
        clauses = []
        if data_inicio:
            clauses.append("data_evento >= %s")
            params.append(data_inicio)
        if data_fim:
            clauses.append("data_evento <= %s")
            params.append(data_fim)
        if clauses:
            base += " WHERE " + " AND ".join(clauses)
        base += " ORDER BY data_evento DESC, id DESC"
        columns, results = self.db.execute_query(base, tuple(params) if params else None, fetch_all=True)
        if results:
            return [Evento(**dict(zip(columns, row))) for row in results]
        return []
