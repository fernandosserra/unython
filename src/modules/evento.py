# src/modules/evento.py
from src.utils.database_manager import DatabaseManager
from src.utils.models import Evento
from typing import Optional, List

class EventoService:
    """
    Gerencia a lógica de criação e controle do Ciclo de Eventos (Dias Fiscais).
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def registrar_evento(self, evento: Evento) -> Optional[int]:
        """Insere um novo evento na base de dados e retorna o ID."""
        query = "INSERT INTO eventos (nome, data_evento, tipo, status) VALUES (?, ?, ?, ?)"
        params = (evento.nome, evento.data_evento, evento.tipo, evento.status)
        
        # Retorna o lastrowid do novo Evento
        return self.db.execute_query(query, params, commit=True)
    
    def buscar_evento_aberto(self) -> Optional[Evento]:
        """
        Busca o Evento atualmente aberto (status='Aberto'). 
        Deve haver no máximo um por vez.
        """
        query = "SELECT id, nome, data_evento, tipo, status FROM eventos WHERE status = 'Aberto' LIMIT 1"
        columns, result = self.db.execute_query(query, fetch_one=True)
        
        if result:
            # Transmutação de Tupla SQL para Objeto Evento
            return Evento(**dict(zip(columns, result)))
        return None

    def fechar_evento(self, id_evento: int) -> bool:
        """Fecha um evento, finalizando o ciclo fiscal."""
        query = "UPDATE eventos SET status = 'Fechado' WHERE id = ?"
        return self.db.execute_query(query, (id_evento,), commit=True)

    # Nota: Poderíamos adicionar buscar_eventos, mas estes três são cruciais para o fluxo.