# src/utils/security.py
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import bcrypt

# Chave de desenvolvimento: NUNCA aceita em produção.
DEV_SECRET_KEY = "unython-secret-key-change-me-in-production-2025"
MIN_SECRET_LENGTH = 32
_WEAK_SECRET_MARKERS = ("change-me", "changeme", "secret-key", "default", "password", "example")
PRODUCTION_ENVS = {"production", "prod"}
SECRET_KEY = os.getenv("JWT_SECRET_KEY") or DEV_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 8 horas
BCRYPT_MAX_BYTES = 72


def is_production() -> bool:
    """Produção é definida explicitamente por APP_ENV (ou ENVIRONMENT)."""
    env = os.getenv("APP_ENV") or os.getenv("ENVIRONMENT") or ""
    return env.strip().lower() in PRODUCTION_ENVS


def validate_secret_key(secret: Optional[str]) -> None:
    """Levanta RuntimeError se o segredo JWT for ausente, padrão ou fraco."""
    if not secret or secret == DEV_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY deve ser definido explicitamente em produção.")
    if len(secret) < MIN_SECRET_LENGTH or len(set(secret)) < 8:
        raise RuntimeError(f"JWT_SECRET_KEY fraco: use ao menos {MIN_SECRET_LENGTH} caracteres aleatórios.")
    if any(m in secret.lower() for m in _WEAK_SECRET_MARKERS):
        raise RuntimeError("JWT_SECRET_KEY contém padrão previsível; gere um valor aleatório.")


def get_secret_key() -> str:
    """Retorna o segredo JWT vigente; em produção exige segredo forte."""
    secret = os.getenv("JWT_SECRET_KEY") or None
    if is_production():
        validate_secret_key(secret)
        return secret
    return secret or SECRET_KEY


def hash_password(password: str) -> str:
    """
    Gera o hash da senha usando bcrypt direto, garantindo o limite de 72 bytes.
    """
    pwd_bytes = password.encode("utf-8")[:BCRYPT_MAX_BYTES]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha em texto puro corresponde ao hash armazenado.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:BCRYPT_MAX_BYTES],
            hashed_password.encode("utf-8"),
        )
    except Exception:
        # Fallback de compatibilidade caso o hash venha de outro esquema
        try:
            from passlib.context import CryptContext
            ctx = CryptContext(schemes=["bcrypt"])
            return ctx.verify(plain_password, hashed_password)
        except Exception:
            return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT assinado com claims de subject e expiração.
    """
    import jwt
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Valida e decodifica um token JWT. Retorna o payload se válido, ou None se inválido/expirado.
    Tokens legados não são aceitos.
    """
    import jwt
    try:
        return jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM], options={"require": ["exp"]})
    except jwt.PyJWTError:
        return None
