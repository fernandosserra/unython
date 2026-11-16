# src/utils/dependencies.py

from typing import Annotated, Generator, Set
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.utils.database_manager import DatabaseManager
from src.modules.usuario import UsuarioService
from src.utils.models import Usuario
from src.utils.security import decode_access_token


# --- DATABASE DEPENDENCIES ---
def get_db() -> Generator[DatabaseManager, None, None]:
    """
    Função geradora que obtém uma conexão de banco de dados
    e garante devolução/fechamento após a requisição.
    """
    db = DatabaseManager()
    try:
        db.connect()
        yield db
    finally:
        db.disconnect()


DBDependency = Annotated[DatabaseManager, Depends(get_db)]


# --- AUTHENTICATION DEPENDENCIES ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DBDependency) -> Usuario:
    """
    Função de dependência que valida e decodifica o token JWT
    e retorna o objeto Usuario autenticado.
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id") or payload.get("sub")
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token com formato inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    usuario_service = UsuarioService(db)
    user = usuario_service.buscar_usuario_por_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(allowed_roles: Set[str]):
    """Cria uma dependência que checa se o usuário tem a função/role necessária."""

    def role_checker(current_user: Annotated[Usuario, Depends(get_current_user)]):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Requer função: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker
