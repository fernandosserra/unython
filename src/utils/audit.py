from psycopg2.extras import Json

from src.utils.database_manager import DatabaseManager


def record_audit(
    db: DatabaseManager,
    *,
    user_id: int,
    acao: str,
    entidade: str,
    entidade_id: int,
    detalhes: dict,
    request_id: str,
) -> None:
    db.execute_query(
        """
        INSERT INTO audit_logs (user_id, acao, entidade, entidade_id, detalhes, request_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (user_id, acao, entidade, entidade_id, Json(detalhes), request_id),
        commit=False,
    )
