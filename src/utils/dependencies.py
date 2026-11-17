# src/utils/dependencies.py

from typing import Annotated, Generator, Set
from fastapi import Depends, HTTPException, Request, status
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


# Rotas permitidas mesmo com troca de senha obrigatória pendente
PASSWORD_CHANGE_ALLOWED_PATHS = {
    "/change-password", "/logout", "/me", "/perfil", "/auth/logout", "/auth/me",
    "/usuarios/me", "/usuarios/perfil",
}


def _path_allows_pending_password_change(path: str) -> bool:
    path = path.rstrip("/") or "/"
    if path.startswith("/api/"):
        path = path[4:]
    return path in PASSWORD_CHANGE_ALLOWED_PATHS


def get_current_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBDependency,
) -> Usuario:
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

    if user is None or user.status != "Ativo":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if getattr(user, "require_password_change", False) and not _path_allows_pending_password_change(
        request.url.path
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Troca de senha obrigatória antes de continuar.",
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


LEGACY_MODULES = frozenset({"pdv", "caixa", "atendimentos", "doacoes"})
MODULES = frozenset({*LEGACY_MODULES, "estoque", "relatorios", "eventos"})
MODULE_FEATURES = {
    "pdv": "habilitar_pdv",
    "atendimentos": "habilitar_atendimentos",
    "doacoes": "habilitar_doacoes",
}


def require_module(*modules: str, legacy_admin_only: bool = False, legacy_allow: bool = False, check_features: bool = True):
    """Autoriza qualquer um dos módulos, mantendo o acesso operacional legado."""
    if not modules or not set(modules) <= MODULES:
        raise ValueError("Módulo de permissão inválido.")

    def module_checker(
        db: DBDependency,
        current_user: Annotated[Usuario, Depends(get_current_user)],
    ):
        if current_user.role == "Administrador":
            allowed = set(modules)
        elif current_user.permissoes is None:
            allowed = set() if legacy_admin_only else set(modules) if legacy_allow else set(modules) & LEGACY_MODULES
        else:
            allowed = set(modules) & set(current_user.permissoes)
        if not allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso ao módulo negado.")
        if check_features and all(module in MODULE_FEATURES for module in allowed):
            from src.modules.organizacao import OrganizacaoService

            config = OrganizacaoService(db).obter_configuracoes()
            if not any(getattr(config, MODULE_FEATURES[module]) for module in allowed):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Módulo desabilitado pela organização.")
        return current_user

    return module_checker
