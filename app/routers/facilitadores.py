from fastapi import APIRouter, Depends, HTTPException, status

from src.utils.dependencies import DBDependency, require_role
from src.utils.models import Usuario
from src.utils.schemas import FacilitadorCreate

router = APIRouter(prefix="/facilitadores", tags=["Facilitadores"])
ADMIN_ONLY = require_role({"Administrador"})


@router.get("/")
def listar_facilitadores(db: DBDependency, apenas_ativos: bool = False):
    query = "SELECT id, nome, especialidade, observacoes, status FROM facilitadores"
    if apenas_ativos:
        query += " WHERE status = 'Ativo'"
    columns, rows = db.execute_query(query + " ORDER BY nome, id", fetch_all=True)
    return [dict(zip(columns, row)) for row in rows]


@router.post("/", status_code=status.HTTP_201_CREATED)
def criar_facilitador(
    payload: FacilitadorCreate,
    db: DBDependency,
    current_user: Usuario = Depends(ADMIN_ONLY),
):
    fid = db.execute_query(
        "INSERT INTO facilitadores (nome, especialidade, observacoes, status) VALUES (%s, %s, %s, %s) RETURNING id",
        (payload.nome.strip(), payload.especialidade, payload.observacoes, payload.status),
        commit=True,
    )
    return {"id": fid}


@router.put("/{facilitador_id}")
def atualizar_facilitador(
    facilitador_id: int,
    payload: FacilitadorCreate,
    db: DBDependency,
    current_user: Usuario = Depends(ADMIN_ONLY),
):
    count = db.execute_query(
        "UPDATE facilitadores SET nome = %s, especialidade = %s, observacoes = %s, status = %s WHERE id = %s",
        (payload.nome.strip(), payload.especialidade, payload.observacoes, payload.status, facilitador_id),
        commit=True, return_rowcount=True,
    )
    if not count:
        raise HTTPException(status_code=404, detail="Facilitador não encontrado.")
    return {"id": facilitador_id}


@router.delete("/{facilitador_id}")
def excluir_facilitador(
    facilitador_id: int,
    db: DBDependency,
    current_user: Usuario = Depends(ADMIN_ONLY),
):
    count = db.execute_query(
        "UPDATE facilitadores SET status = 'Inativo' WHERE id = %s",
        (facilitador_id,), commit=True, return_rowcount=True,
    )
    if not count:
        raise HTTPException(status_code=404, detail="Facilitador não encontrado.")
    return {"id": facilitador_id, "status": "Inativo"}
