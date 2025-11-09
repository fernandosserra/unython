# src/utils/dependencies.py

from typing import Annotated, Generator, Set
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ..utils.database_manager import DatabaseManager # Importação relativa corrigida
from src.modules.usuario import UsuarioService
from src.utils.models import Usuario


# --- DATABASE DEPENDENCIES ---
# Configuração de Database
def get_db() -> Generator[DatabaseManager, None, None]:
    """
    Função geradora que cria uma conexão de banco de dados 
    e garante que ela seja fechada após a requisição.
    """
    db = DatabaseManager()
    try:
        db.connect()
        yield db
    finally:
        db.disconnect()
        
# Alias para uso nos endpoints
DBDependency = Annotated[DatabaseManager, Depends(get_db)]


# --- AUTHENTICATION DEPENDENCIES ---

# Define o esquema OAuth2 (onde a API esperará o token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DBDependency) -> Usuario:
    """
    Função de dependência que (simuladamente) decodifica o token 
    e retorna o objeto Usuario completo.
    """
    # NOTE: Para fins de teste, vamos DECODIFICAR o token para obter o ID do usuário.
    # No seu caso, o token é 'access-token-para-usuario-1'. Vamos extrair o '1'.
    
    try:
        user_id_str = token.split('-')[-1] # Ex: '1'
        user_id = int(user_id_str)
    except Exception:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Busca o usuário no DB pelo ID
    usuario_service = UsuarioService(db)
    # NOTE: Você precisará de um método buscar_usuario_por_id no UsuarioService!
    user = usuario_service.buscar_usuario_por_id(user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(allowed_roles: Set[str]):
    """Cria uma dependência que checa se o usuário tem a função necessária."""
    
    def role_checker(current_user: Annotated[Usuario, Depends(get_current_user)]):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Requer função: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker