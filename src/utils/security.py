# src/utils/security.py

from passlib.context import CryptContext
from typing import Optional

# Define o algoritmo de hashing (bcrypt é o padrão moderno e seguro)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
BCRYPT_MAX_BYTES = 72 # Constante de segurança

try:
    # Tenta usar a configuração padrão
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except AttributeError:
    # Se falhar ao carregar o bcrypt de forma complexa (o erro '__about__'),
    # Força o carregamento de forma simples, ignorando o erro de introspecção.
    print(" (Alerta Washu: Patch aplicado para erro de bcrypt/passlib. Segurança ok.)")
    pwd_context = CryptContext(schemes=["bcrypt"]) # Usa o fallback mais simples

def hash_password(password: str) -> str:
    """
    Retorna a versão hash (criptografada) da senha fornecida.
    Garante que a senha seja truncada para o limite máximo de 72 bytes do bcrypt.
    """
    # CRÍTICO: Trunca a senha para evitar o erro de 72 bytes
    if len(password.encode('utf8')) > BCRYPT_MAX_BYTES:
        # Codifica para bytes, trunca, e decodifica de volta para string
        password = password.encode('utf8')[:BCRYPT_MAX_BYTES].decode('utf8')
        print(" (Alerta de Segurança: Senha truncada para 72 bytes)")
        
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha em texto puro corresponde ao hash armazenado."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        # Retorna False se o hash for inválido (ex: hash antigo ou corrompido)
        return False