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
from src.modules.usuario import UsuarioService # Para verificar credenciais
from src.utils.schemas import Token, LoginRequest

# Cria o Router
router = APIRouter(
    tags=["Autenticação (Login)"]
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
    
    # 1. VERIFICAR AS CREDENCIAIS (O coração da segurança)
    # A função verificar_credenciais está no UsuarioService (você deve implementá-la)
    usuario = usuario_service.verificar_credenciais(form_data.username, form_data.password)
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas ou e-mail não encontrado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 2. SE SUCESSO: Retorna um token SIMULADO (A lógica JWT virá depois)
    return {
        "access_token": f"access-token-para-usuario-{usuario.id}",
        "token_type": "bearer",
    }