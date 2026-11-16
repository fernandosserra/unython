from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional

from src.utils.dependencies import DBDependency, require_role
from src.modules.usuario import UsuarioService
from src.utils.models import Usuario
from src.utils.schemas import UsuarioResponse, UsuarioCreate, RoleUpdate

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

ADMIN_OR_OPERATOR = require_role({"Administrador", "Operador"})
ADMIN_ONLY = require_role({"Administrador"})


@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(db: DBDependency):
    """Lista todos os usuários sem expor hashes de senha."""
    service = UsuarioService(db)
    usuarios = service.buscar_usuarios()
    return [
        UsuarioResponse(
            id=u.id,
            nome=u.nome,
            email=u.email,
            funcao=u.funcao,
            role=u.role,
            status=u.status,
            require_password_change=u.require_password_change,
        )
        for u in usuarios
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
def criar_usuario(
    payload: UsuarioCreate,
    db: DBDependency,
):
    """Cria um novo usuário recebendo as credenciais de forma segura no corpo JSON."""
    service = UsuarioService(db)
    usuario = Usuario(
        nome=payload.nome,
        email=payload.email,
        funcao=payload.funcao or "Operador",
        role=payload.role,
        status=payload.status,
        require_password_change=payload.require_password_change,
    )
    uid = service.registrar_usuario(
        usuario,
        payload.senha,
        require_password_change=payload.require_password_change,
    )
    if not uid:
        raise HTTPException(status_code=400, detail="Não foi possível criar/atualizar usuário.")
    return {"id": uid}


@router.put("/{user_id}/role")
def atualizar_role(user_id: int, payload: RoleUpdate, db: DBDependency):
    """Atualiza o papel e status do usuário."""
    service = UsuarioService(db)
    ok = service.atualizar_role_status(
        user_id, payload.role, payload.status, payload.funcao or payload.role
    )
    if not ok:
        raise HTTPException(status_code=400, detail="Não foi possível atualizar usuário.")
    return {"id": user_id, "role": payload.role, "status": payload.status}
