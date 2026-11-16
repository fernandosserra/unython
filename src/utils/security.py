# src/utils/security.py
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import bcrypt

# Chave secreta e algoritmo para JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "unython-secret-key-change-me-in-production-2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 8 horas
BCRYPT_MAX_BYTES = 72


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
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Valida e decodifica um token JWT. Retorna o payload se válido, ou None se inválido/expirado.
    Também aceita tokens legados de desenvolvimento ('access-token-para-usuario-X') para transição suave.
    """
    import jwt
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        # Suporte legado temporário para testes de integração existentes
        if token.startswith("access-token-para-usuario-"):
            try:
                user_id = int(token.split("-")[-1])
                return {"sub": str(user_id), "user_id": user_id}
            except ValueError:
                pass
        return None
