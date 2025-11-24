# app/routers/auth.py

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
import sys
import os

# Adiciona o diretório 'src'
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Importa Services e Schemas
from src.utils.dependencies import DBDependency
from src.modules.usuario import UsuarioService
from src.utils.schemas import Token, LoginRequest, ChangePasswordRequest

# Cria o Router
router = APIRouter(
    tags=["Autenticacao (Login)"]
)

# ------------------------------------------------------------------
# ENDPOINT: LOGIN
# ------------------------------------------------------------------

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DBDependency
):
    """
    Verifica as credenciais (email/senha) e retorna um token JWT (simulado).
    """
    usuario_service = UsuarioService(db)
    usuario = usuario_service.verificar_credenciais(form_data.username, form_data.password)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas ou e-mail nao encontrado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": f"access-token-para-usuario-{usuario.id}",
        "token_type": "bearer",
        "user_id": usuario.id,
        "require_password_change": getattr(usuario, "require_password_change", False),
    }


@router.post("/change-password")
async def change_password(payload: ChangePasswordRequest, db: DBDependency):
    """Altera a senha do usuario e limpa o flag de troca obrigatoria."""
    usuario_service = UsuarioService(db)
    ok = usuario_service.alterar_senha(payload.email, payload.old_password, payload.new_password)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual invalida ou usuario inexistente.",
        )
    return {"status": "ok"}
