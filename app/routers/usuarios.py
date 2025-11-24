from fastapi import APIRouter, HTTPException, status
from typing import List
from pydantic import BaseModel

from src.utils.dependencies import DBDependency
from src.modules.usuario import UsuarioService
from src.utils.models import Usuario

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("/", response_model=List[dict])
def listar_usuarios(db: DBDependency):
    service = UsuarioService(db)
    usuarios = service.buscar_usuarios()
    return [u.__dict__ for u in usuarios]


@router.post("/", status_code=status.HTTP_201_CREATED)
def criar_usuario(usuario: Usuario, senha: str, require_password_change: bool = False, db: DBDependency = None):
    service = UsuarioService(db)
    uid = service.registrar_usuario(usuario, senha, require_password_change=require_password_change)
    if not uid:
        raise HTTPException(status_code=400, detail="Nao foi possivel criar/atualizar usuario.")
    return {"id": uid}


class RoleUpdate(BaseModel):
    role: str
    status: str = "Ativo"
    funcao: str | None = None


@router.put("/{user_id}/role")
def atualizar_role(user_id: int, payload: RoleUpdate, db: DBDependency):
    service = UsuarioService(db)
    ok = service.atualizar_role_status(user_id, payload.role, payload.status, payload.funcao or payload.role)
    if not ok:
        raise HTTPException(status_code=400, detail="Nao foi possivel atualizar usuario.")
    return {"id": user_id, "role": payload.role, "status": payload.status}
