from fastapi import APIRouter, HTTPException, status

from src.utils.dependencies import DBDependency
from src.utils.schemas import AtividadeCreate

router = APIRouter(prefix="/atividades", tags=["Entidades e serviços"])


@router.get("/")
def listar_atividades(db: DBDependency, apenas_ativos: bool = False):
    query = "SELECT id, nome, descricao, status FROM atividades_atendimento"
    if apenas_ativos:
        query += " WHERE status = 'Ativo'"
    columns, rows = db.execute_query(query + " ORDER BY nome, id", fetch_all=True)
    return [dict(zip(columns, row)) for row in rows]


@router.post("/", status_code=status.HTTP_201_CREATED)
def criar_atividade(payload: AtividadeCreate, db: DBDependency):
    aid = db.execute_query(
        "INSERT INTO atividades_atendimento (nome, descricao, status) VALUES (%s, %s, %s) RETURNING id",
        (payload.nome, payload.descricao, payload.status), commit=True,
    )
    return {"id": aid}


@router.put("/{atividade_id}")
def atualizar_atividade(atividade_id: int, payload: AtividadeCreate, db: DBDependency):
    count = db.execute_query(
        "UPDATE atividades_atendimento SET nome = %s, descricao = %s, status = %s WHERE id = %s",
        (payload.nome, payload.descricao, payload.status, atividade_id), commit=True, return_rowcount=True,
    )
    if not count:
        raise HTTPException(status_code=404, detail="Cadastro não encontrado.")
    return {"id": atividade_id}


@router.delete("/{atividade_id}")
def inativar_atividade(atividade_id: int, db: DBDependency):
    count = db.execute_query(
        "UPDATE atividades_atendimento SET status = 'Inativo' WHERE id = %s",
        (atividade_id,), commit=True, return_rowcount=True,
    )
    if not count:
        raise HTTPException(status_code=404, detail="Cadastro não encontrado.")
    return {"id": atividade_id, "status": "Inativo"}
