from datetime import datetime, time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.utils.dependencies import DBDependency, get_current_user, require_module
from src.utils.models import Usuario
from src.utils.schemas import DoacaoCreate

router = APIRouter(prefix="/doacoes", tags=["Doações financeiras"], dependencies=[Depends(require_module("doacoes"))])
CurrentUser = Annotated[Usuario, Depends(get_current_user)]


@router.get("/")
def listar_doacoes(db: DBDependency, current_user: CurrentUser):
    columns, rows = db.execute_query(
        """SELECT m.id, m.data_registro, m.valor, m.nome_doador, m.forma_pagamento,
                  m.descricao, m.id_evento, e.nome AS evento, m.status
           FROM movimentos_financeiros m LEFT JOIN eventos e ON e.id = m.id_evento
           WHERE m.tipo_movimento = 'Receita' AND m.categoria = 'Doacao'
           ORDER BY m.data_registro DESC, m.id DESC""",
        fetch_all=True,
    )
    return [dict(zip(columns, row)) for row in rows]


@router.post("/", status_code=status.HTTP_201_CREATED)
def registrar_doacao(payload: DoacaoCreate, db: DBDependency, current_user: CurrentUser):
    if payload.id_evento is not None:
        _, evento = db.execute_query("SELECT id FROM eventos WHERE id = %s", (payload.id_evento,), fetch_one=True)
        if not evento:
            raise HTTPException(status_code=400, detail="Evento não encontrado.")
    doacao_id = db.execute_query(
        """INSERT INTO movimentos_financeiros
           (data_registro, id_usuario, tipo_movimento, valor, descricao, categoria, id_evento, nome_doador, forma_pagamento)
           VALUES (%s, %s, 'Receita', %s, %s, 'Doacao', %s, %s, %s) RETURNING id""",
        (datetime.combine(payload.data, time(12)), current_user.id, payload.valor,
         payload.descricao, payload.id_evento, payload.nome_doador, payload.forma_pagamento),
        commit=True,
    )
    return {"id": doacao_id}


@router.patch("/{doacao_id}/cancelar")
def cancelar_doacao(doacao_id: int, db: DBDependency, current_user: CurrentUser):
    count = db.execute_query(
        """UPDATE movimentos_financeiros SET status = 'Cancelado'
           WHERE id = %s AND tipo_movimento = 'Receita' AND categoria = 'Doacao' AND status = 'Ativo'""",
        (doacao_id,), commit=True, return_rowcount=True,
    )
    if not count:
        raise HTTPException(status_code=404, detail="Doação ativa não encontrada.")
    return {"id": doacao_id, "status": "Cancelado"}
