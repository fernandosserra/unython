import json
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from app import api_main
from src.utils import dependencies, security

STRONG = "Zq8!vL2#pR7$tW4&yN9*cK6^mB3@hX5%"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    return TestClient(api_main.app, raise_server_exceptions=False)


def _healthy_db():
    db = MagicMock()
    db.DB_NAME = "x"
    db.execute_query.return_value = (["?column?"], (1,))
    return db


def test_request_id_generated_and_valid_preserved(client):
    with patch.object(api_main, "DatabaseManager", return_value=_healthy_db()):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert len(r.headers["X-Request-ID"]) == 32
        r = client.get("/api/health", headers={"X-Request-ID": "abc-12345.XYZ"})
        assert r.headers["X-Request-ID"] == "abc-12345.XYZ"
        r = client.get("/api/health", headers={"X-Request-ID": "bad id\r\n<x>"})
        assert r.headers["X-Request-ID"] != "bad id"
        assert len(r.headers["X-Request-ID"]) == 32


def test_request_id_on_error_and_404(client):
    r = client.get("/api/rota-inexistente")
    assert r.status_code == 404 and "X-Request-ID" in r.headers


def test_health_executes_select_1(client):
    db = _healthy_db()
    with patch.object(api_main, "DatabaseManager", return_value=db):
        assert client.get("/api/health").json() == {"status": "connected"}
        assert client.get("/db-status").json() == {"status": "connected", "database": "x"}
    db.execute_query.assert_called_with("SELECT 1", fetch_one=True)
    db.disconnect.assert_called()


def test_health_503_without_details(client):
    db = _healthy_db()
    db.execute_query.side_effect = RuntimeError("password=hunter2 host=10.0.0.1")
    with patch.object(api_main, "DatabaseManager", return_value=db):
        r = client.get("/api/health")
    assert r.status_code == 503
    assert r.json() == {"status": "unavailable"}
    assert "hunter2" not in r.text and "X-Request-ID" in r.headers


def test_security_headers_no_hsts_on_http(client):
    with patch.object(api_main, "DatabaseManager", return_value=_healthy_db()):
        r = client.get("/api/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert "frame-ancestors 'none'" in r.headers["Content-Security-Policy"]
    assert "Strict-Transport-Security" not in r.headers


def test_hsts_only_in_production_https(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    with patch.object(api_main, "DatabaseManager", return_value=_healthy_db()):
        c = TestClient(api_main.app, base_url="https://testserver")
        assert "Strict-Transport-Security" in c.get("/api/health").headers
        c = TestClient(api_main.app, base_url="http://testserver")
        assert "Strict-Transport-Security" not in c.get("/api/health").headers


def test_access_log_is_structured_and_safe(client, caplog):
    caplog.set_level(logging.INFO, logger="unython.access")
    logger = logging.getLogger("unython.access")
    logger.propagate = True
    try:
        with patch.object(api_main, "DatabaseManager", return_value=_healthy_db()):
            client.get("/api/health?token=SEGREDO", headers={"Authorization": "Bearer JWT.SECRETO"})
    finally:
        logger.propagate = False
    rec = json.loads(caplog.records[-1].getMessage())
    assert rec["method"] == "GET" and rec["route"] == "/api/health" and rec["status"] == 200
    assert "duration_ms" in rec
    assert "SEGREDO" not in caplog.text and "JWT.SECRETO" not in caplog.text


def _add_route_first(path, fn):
    api_main.app.get(path)(fn)
    api_main.app.router.routes.insert(0, api_main.app.router.routes.pop())


def test_unhandled_exception_returns_500_with_request_id(client):
    def boom():
        raise ValueError("segredo interno")

    _add_route_first("/__boom", boom)

    r = client.get("/__boom")
    assert r.status_code == 500
    assert "segredo" not in r.text and "X-Request-ID" in r.headers


def test_request_state_request_id_reaches_handlers(client):
    def rid(request: api_main.Request):
        return {"rid": request.state.request_id}

    _add_route_first("/__rid", rid)

    r = client.get("/__rid")
    assert r.json()["rid"] == r.headers["X-Request-ID"]


# --- configuração de produção ---
@pytest.mark.parametrize("secret", [None, "", security.DEV_SECRET_KEY, "curta", "change-me-" + "a1B2c3D4" * 4, "a" * 40])
def test_production_rejects_bad_jwt_secret(monkeypatch, secret):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.org")
    if secret is None:
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    else:
        monkeypatch.setenv("JWT_SECRET_KEY", secret)
    with pytest.raises(RuntimeError):
        api_main.validate_production_config()
    with pytest.raises(RuntimeError):
        security.create_access_token({"sub": "1"})


@pytest.mark.parametrize("cors", ["", "*", "http://app.example.org", "https://*.example.org",
                                  "https://app.example.org/path", "https://user@app.example.org"])
def test_production_rejects_unsafe_cors(monkeypatch, cors):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", STRONG)
    monkeypatch.setenv("CORS_ORIGINS", cors)
    with pytest.raises(RuntimeError):
        api_main.validate_production_config()


def test_production_valid_config(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", STRONG)
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.org/")
    api_main.validate_production_config()
    assert api_main.get_cors_origins() == ["https://app.example.org"]
    token = security.create_access_token({"sub": "1"})
    assert security.decode_access_token(token)["sub"] == "1"


def test_bootstrap_password_policy(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("BOOTSTRAP_ADMIN_PASSWORD", raising=False)
    assert api_main.resolve_bootstrap_password() is None
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", "change-me-now")
    assert api_main.resolve_bootstrap_password() is None
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", "curta")
    assert api_main.resolve_bootstrap_password() is None
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", STRONG)
    assert api_main.resolve_bootstrap_password() == STRONG
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("BOOTSTRAP_ADMIN_PASSWORD")
    assert api_main.resolve_bootstrap_password() == "change-me-now"


def test_production_rejects_configured_default_bootstrap_password(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", STRONG)
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.org")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", "change-me-now")
    with pytest.raises(RuntimeError, match="BOOTSTRAP_ADMIN_PASSWORD"):
        api_main.validate_production_config()


def test_production_refuses_existing_default_admin_password(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", STRONG)
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.org")
    monkeypatch.delenv("BOOTSTRAP_ADMIN_PASSWORD", raising=False)
    db = _healthy_db()
    admin = SimpleNamespace(hashed_password=security.hash_password("change-me-now"))
    service = MagicMock()
    service.buscar_usuario_por_email.return_value = admin
    with patch.object(api_main, "DatabaseManager", return_value=db), patch.object(api_main, "UsuarioService", return_value=service):
        with pytest.raises(RuntimeError, match="senha padrão"):
            with TestClient(api_main.app):
                pass
    db.disconnect.assert_called_once()


def test_legacy_tokens_rejected():
    assert security.decode_access_token("access-token-para-usuario-1") is None
    assert security.decode_access_token("lixo") is None


def test_token_without_exp_rejected(monkeypatch):
    import jwt
    tok = jwt.encode({"sub": "1"}, security.get_secret_key(), algorithm="HS256")
    assert security.decode_access_token(tok) is None


# --- require_password_change ---
def _app_with_user(user):
    app = FastAPI()

    @app.get("/protegida")
    def protegida(u=Depends(dependencies.get_current_user)):
        return {"id": u.id}

    @app.get("/me")
    def me(u=Depends(dependencies.get_current_user)):
        return {"id": u.id}

    app.dependency_overrides[dependencies.get_db] = lambda: MagicMock()
    return app


@pytest.mark.parametrize("pending,path,code", [
    (True, "/protegida", 403), (True, "/me", 200), (False, "/protegida", 200),
])
def test_get_current_user_password_change(monkeypatch, pending, path, code):
    user = SimpleNamespace(id=1, status="Ativo", require_password_change=pending, role="Administrador")
    svc = MagicMock()
    svc.buscar_usuario_por_id.return_value = user
    monkeypatch.setattr(dependencies, "UsuarioService", lambda db: svc)
    token = security.create_access_token({"sub": "1"})
    r = TestClient(_app_with_user(user)).get(path, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == code
