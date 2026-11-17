# app/api_main.py
from contextlib import asynccontextmanager
from pathlib import Path
import json
import logging
import os
import re
import time
import uuid
from typing import Optional
from urllib.parse import urlsplit
from fastapi import FastAPI, APIRouter, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

# Importa a infraestrutura do back-end
from src.utils.database_manager import DatabaseManager
from src.utils.security import is_production, validate_secret_key, verify_password
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


logger = logging.getLogger("unython.access")
app_logger = logging.getLogger("unython.app")
for _lg in (logger, app_logger):
    if not _lg.handlers:
        _h = logging.StreamHandler()
        _h.setFormatter(logging.Formatter("%(message)s"))
        _lg.addHandler(_h)
        _lg.setLevel(logging.INFO)
        _lg.propagate = False

REQUEST_ID_HEADER = "X-Request-ID"
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
DEV_BOOTSTRAP_PASSWORD = "change-me-now"
BOOTSTRAP_EMAIL = "admin@unython.local"
MIN_BOOTSTRAP_PASSWORD_LENGTH = 12
DEV_CORS_ORIGINS = ["*"]

CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; "
    "manifest-src 'self'; worker-src 'self'; object-src 'none'; base-uri 'self'; "
    "form-action 'self'; frame-ancestors 'none'"
)
_NO_CSP_PATHS = ("/docs", "/redoc", "/openapi.json")


def resolve_request_id(incoming: Optional[str]) -> str:
    """Aceita o ID do cliente apenas se for seguro; caso contrário gera um novo."""
    if incoming and _REQUEST_ID_RE.fullmatch(incoming):
        return incoming
    return uuid.uuid4().hex


def get_cors_origins() -> list[str]:
    """Lê CORS_ORIGINS (separado por vírgula). Em produção é obrigatório e deve ser seguro."""
    raw = os.getenv("CORS_ORIGINS", "")
    origins = [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]
    if not is_production():
        return origins or DEV_CORS_ORIGINS
    if not origins:
        raise RuntimeError("CORS_ORIGINS deve ser definido explicitamente em produção.")
    for origin in origins:
        if origin == "*" or "*" in origin:
            raise RuntimeError("CORS_ORIGINS não pode usar curinga em produção.")
        parsed = urlsplit(origin)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
                or parsed.path or parsed.query or parsed.fragment):
            raise RuntimeError("CORS_ORIGINS em produção deve conter apenas origens https válidas.")
        try:
            parsed.port
        except ValueError as exc:
            raise RuntimeError("CORS_ORIGINS contém porta inválida.") from exc
    return origins


def validate_production_config() -> None:
    """Falha o startup se a configuração de produção for insegura."""
    if not is_production():
        return
    validate_secret_key(os.getenv("JWT_SECRET_KEY"))
    get_cors_origins()
    if os.getenv("BOOTSTRAP_ADMIN_PASSWORD") is not None and resolve_bootstrap_password() is None:
        raise RuntimeError("BOOTSTRAP_ADMIN_PASSWORD insegura para produção.")


def resolve_bootstrap_password() -> Optional[str]:
    """
    Senha inicial do admin. Em desenvolvimento usa a senha padrão; em produção exige
    BOOTSTRAP_ADMIN_PASSWORD forte, senão o bootstrap é ignorado (retorna None).
    """
    if not is_production():
        return os.getenv("BOOTSTRAP_ADMIN_PASSWORD") or DEV_BOOTSTRAP_PASSWORD
    pwd = os.getenv("BOOTSTRAP_ADMIN_PASSWORD") or ""
    if len(pwd) < MIN_BOOTSTRAP_PASSWORD_LENGTH or pwd.lower() == DEV_BOOTSTRAP_PASSWORD:
        return None
    return pwd


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Valida a configuração e garante o superusuário inicial após as migrações."""
    validate_production_config()
    dbm = DatabaseManager()
    dbm.connect()
    try:
        usuario_service = UsuarioService(dbm)
        admin = usuario_service.buscar_usuario_por_email(BOOTSTRAP_EMAIL)
        if is_production() and admin and verify_password(DEV_BOOTSTRAP_PASSWORD, admin.hashed_password):
            raise RuntimeError("A senha padrão do superusuário não é permitida em produção.")
        if not admin:
            password = resolve_bootstrap_password()
            if password is None:
                app_logger.warning(
                    "bootstrap do superusuário ignorado: defina BOOTSTRAP_ADMIN_PASSWORD "
                    "(>= %d caracteres) em produção",
                    MIN_BOOTSTRAP_PASSWORD_LENGTH,
                )
            else:
                usuario = Usuario(
                    nome="Super Usuário",
                    email=BOOTSTRAP_EMAIL,
                    funcao="Administrador",
                    role="Administrador",
                    status="Ativo",
                    require_password_change=True,
                )
                usuario_service.registrar_usuario(usuario, password, require_password_change=True)
                app_logger.info("bootstrap: superusuário criado")
    finally:
        dbm.disconnect()
    yield


# Cria a instância da API com lifespan moderno
app = FastAPI(
    title="Unython - Gestão API",
    description="API REST para gerenciamento de ONGs e Fluxo de Eventos.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: tokens vão em Authorization (Bearer), portanto cookies/credenciais não são necessários.
# Avaliado na importação; em produção falha rápido se inseguro.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", REQUEST_ID_HEADER],
    expose_headers=[REQUEST_ID_HEADER],
)


def _apply_security_headers(request: Request, response: Response) -> None:
    h = response.headers
    h["X-Content-Type-Options"] = "nosniff"
    h["X-Frame-Options"] = "DENY"
    h["Referrer-Policy"] = "strict-origin-when-cross-origin"
    h["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if not request.url.path.startswith(_NO_CSP_PATHS):
        h.setdefault("Content-Security-Policy", CSP)
    if request.url.path.startswith("/api") or request.url.path in ("/token", "/db-status"):
        h.setdefault("Cache-Control", "no-store")
    if is_production() and request.url.scheme == "https":
        h["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    """Request ID, headers de segurança e log estruturado (sem query string, headers ou corpo)."""
    request_id = resolve_request_id(request.headers.get(REQUEST_ID_HEADER))
    request.state.request_id = request_id
    start = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as exc:
        app_logger.error(
            json.dumps({"event": "unhandled_exception", "request_id": request_id,
                        "error_type": type(exc).__name__})
        )
        response = JSONResponse({"detail": "Erro interno do servidor."}, status_code=500)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers[REQUEST_ID_HEADER] = request_id
    _apply_security_headers(request, response)
    route = request.scope.get("route")
    route_path = getattr(route, "path", None) or "unmatched"
    logger.info(
        json.dumps({
            "event": "request",
            "request_id": request_id,
            "method": request.method,
            "route": route_path,
            "status": status_code,
            "duration_ms": duration_ms,
        })
    )
    return response


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


def _check_database() -> Optional[str]:
    """Executa SELECT 1 real; retorna o nome do banco ou levanta exceção."""
    db = DatabaseManager(create_database=False)
    try:
        db.connect()
        _, result = db.execute_query("SELECT 1", fetch_one=True)
        if not result or result[0] != 1:
            raise RuntimeError("Verificação do banco retornou resultado inesperado.")
        return db.DB_NAME
    finally:
        db.disconnect()


@app.get("/api/health")
def get_health(request: Request):
    """Liveness/readiness: SELECT 1 real; 503 sem detalhes em caso de falha."""
    try:
        _check_database()
    except Exception as exc:
        app_logger.error(
            json.dumps({"event": "health_failed", "request_id": getattr(request.state, "request_id", None),
                        "error_type": type(exc).__name__})
        )
        return JSONResponse({"status": "unavailable"}, status_code=503)
    return {"status": "connected"}


@app.get("/db-status")
def get_db_status(request: Request):
    """Compatibilidade legada: mesmo teste de /api/health, mantendo o campo 'database'."""
    try:
        name = _check_database()
    except Exception as exc:
        app_logger.error(
            json.dumps({"event": "health_failed", "request_id": getattr(request.state, "request_id", None),
                        "error_type": type(exc).__name__})
        )
        return JSONResponse({"status": "unavailable"}, status_code=503)
    return {"status": "connected", "database": name}


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
