# app/api_main.py
from fastapi import FastAPI, Depends, HTTPException, status
from typing import Annotated, Generator
import sys
import os
import uvicorn

# Adiciona o diretório 'src' ao PATH para imports modulares
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Importa a infraestrutura do back-end
from src.utils.database_manager import DatabaseManager
from src.utils.dependencies import DBDependency
from src.modules.usuario import UsuarioService
from src.utils.models import Usuario
from src.utils.security import hash_password

# Importa os routers
from app.routers import estoque, vendas, relatorios, agendamentos, auth, catalogo, caixas, eventos, usuarios

# Cria a instância da API
app = FastAPI(
    title="Unython - Gestão API",
    description="API REST para gerenciamento de ONGs e Fluxo de Eventos.",
    version="1.0.0"
)

# ----------------------------------------------------
# 1. ENDPOINTS BÁSICOS
# ----------------------------------------------------

@app.get("/")
def read_root():
    """Confirma que a API está operacional."""
    return {"message": "Unython API Operational. Data source: PostgreSQL."}

@app.get("/db-status")
def get_db_status(db: DBDependency):
    """Teste para garantir que a conexão está ativa."""
    # Se a conexão foi bem-sucedida pelo get_db, a API retorna OK
    return {"status": "connected", "database": db.DB_NAME}

# ----------------------------------------------------
# 2. INCLUSÃO DE ROUTERS
# ----------------------------------------------------

app.include_router(vendas.router)
app.include_router(relatorios.router)
app.include_router(agendamentos.router)
app.include_router(auth.router)
app.include_router(catalogo.router)
app.include_router(caixas.router)
app.include_router(eventos.router)
app.include_router(usuarios.router)
app.include_router(estoque.router)

# ----------------------------------------------------


@app.on_event("startup")
def ensure_superuser():
    """Garante um superusuário padrão para bootstrap."""
    dbm = DatabaseManager()
    dbm.connect()
    dbm.create_tables()
    usuario_service = UsuarioService(dbm)

    email = "admin@unython.local"
    password = "change-me-now"
    admin = usuario_service.buscar_usuario_por_email(email)
    if not admin:
        usuario = Usuario(
            nome="Super Usuário",
            email=email,
            funcao="Administrador",
            role="Administrador",
            status="Ativo",
            require_password_change=True,
        )
        usuario_service.registrar_usuario(usuario, password, require_password_change=True)
        print(f"[bootstrap] Superusuário criado com email {email}")
    dbm.disconnect()


if __name__ == "__main__":
    # Comando para rodar o servidor Uvicorn localmente
    uvicorn.run(app, host="127.0.0.1", port=8000)
