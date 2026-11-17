# app/api_main.py
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Annotated, Generator
import uvicorn

# Importa a infraestrutura do back-end
from src.utils.database_manager import DatabaseManager
from src.utils.dependencies import DBDependency
from src.modules.usuario import UsuarioService
from src.utils.models import Usuario

# Importa os routers
from app.routers import (
    estoque,
    vendas,
    relatorios,
    agendamentos,
    auth,
    catalogo,
    caixas,
    eventos,
    usuarios,
    organizacao,
    pessoas,
    facilitadores,
    atividades,
    doacoes,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "frontend-web" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Garante tabelas criadas e superusuário padrão no startup da API."""
    try:
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
    except Exception as e:
        print(f"[bootstrap] Alerta ao conectar/inicializar banco: {e}")
    yield


# Cria a instância da API com lifespan moderno
app = FastAPI(
    title="Unython - Gestão API",
    description="API REST para gerenciamento de ONGs e Fluxo de Eventos.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuração de CORS para permitir acesso seguro do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import socket

def get_local_ip() -> str:
    """Detecta o IP desta máquina na rede local Wi-Fi / Ethernet."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ----------------------------------------------------
# 1. ENDPOINTS DE DIAGNÓSTICO E REDE
# ----------------------------------------------------

@app.get("/api/rede")
def get_rede_info():
    """Retorna o IP da rede local para facilitar a conexão de celulares."""
    ip = get_local_ip()
    return {
        "local_ip": ip,
        "port": 8000,
        "url": f"http://{ip}:8000"
    }


@app.get("/api/health")
@app.get("/db-status")
def get_db_status(db: DBDependency):
    """Teste para garantir que a conexão com o PostgreSQL está ativa."""
    return {"status": "connected", "database": db.DB_NAME}


# ----------------------------------------------------
# 2. INCLUSÃO DE ROUTERS (Duplo mapeamento: / e /api)
# ----------------------------------------------------

api_router = APIRouter(prefix="/api")

routers = [
    vendas.router,
    relatorios.router,
    agendamentos.router,
    auth.router,
    catalogo.router,
    caixas.router,
    eventos.router,
    usuarios.router,
    estoque.router,
    organizacao.router,
    pessoas.router,
    facilitadores.router,
    atividades.router,
    doacoes.router,
]

for r in routers:
    app.include_router(r)
    api_router.include_router(r)

app.include_router(api_router)


# ----------------------------------------------------
# 3. SERVINDO SPA EM PRODUÇÃO
# ----------------------------------------------------

if DIST_DIR.exists():
    app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True), name="static_spa")
else:
    @app.get("/")
    def read_root():
        """Fallback quando a SPA ainda não foi compilada."""
        return {"message": "Unython API Operational. Data source: PostgreSQL."}


if __name__ == "__main__":
    uvicorn.run("app.api_main:app", host="127.0.0.1", port=8000, reload=True)
