from fastapi import APIRouter, HTTPException, status
from typing import List

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
