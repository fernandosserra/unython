import pytest
from fastapi.testclient import TestClient

from app.api_main import app
from src.modules.usuario import UsuarioService
from src.utils.dependencies import get_current_user, get_db
from src.utils.models import Usuario
from src.utils.security import create_access_token


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("get", "/api/usuarios/", None),
        ("post", "/api/usuarios/", {
            "nome": "Operador",
            "email": "operador@example.test",
            "funcao": "Operador",
            "role": "Operador",
            "status": "Ativo",
            "senha": "senha-temporaria",
            "require_password_change": True,
        }),
        ("put", "/api/usuarios/1/role", {"role": "Operador", "status": "Ativo", "funcao": "Operador"}),
        ("post", "/api/catalogo/categorias", {"nome": "Bebidas", "descricao": "", "status": "Ativo"}),
        ("post", "/api/catalogo/itens", {
            "nome": "Café",
            "valor_compra": 2,
            "valor_venda": 5,
            "status": "Ativo",
        }),
        ("put", "/api/catalogo/itens/1", {
            "nome": "Café",
            "valor_compra": 2,
            "valor_venda": 5,
            "status": "Ativo",
        }),
        ("post", "/api/estoque/entrada", {
            "itemId": 1,
            "quantidade": 1,
            "usuarioId": 1,
            "eventoId": 1,
        }),
        ("post", "/api/estoque/saida", {
            "itemId": 1,
            "quantidade": 1,
            "usuarioId": 1,
            "eventoId": 1,
        }),
        ("post", "/api/atividades/", {"nome": "Atendimento"}),
        ("put", "/api/atividades/1", {"nome": "Atendimento"}),
        ("delete", "/api/atividades/1", None),
        ("post", "/api/facilitadores/", {"nome": "Atendente"}),
        ("put", "/api/facilitadores/1", {"nome": "Atendente"}),
        ("delete", "/api/facilitadores/1", None),
    ],
)
def test_admin_endpoints_reject_operational_user(method, path, payload):
    operational_user = Usuario(
        id=1,
        nome="Operador",
        email="operador@example.test",
        funcao="Operador",
        role="Operador",
    )
    app.dependency_overrides[get_db] = lambda: None
    app.dependency_overrides[get_current_user] = lambda: operational_user
    client = TestClient(app)

    try:
        response = getattr(client, method)(path, json=payload) if payload else getattr(client, method)(path)
        assert response.status_code == 403
    finally:
        client.close()
        app.dependency_overrides.clear()


def test_inactive_user_cannot_use_existing_access_token(monkeypatch):
    inactive_user = Usuario(
        id=1,
        nome="Desativado",
        email="desativado@example.test",
        funcao="Operador",
        role="Operador",
        status="Inativo",
    )
    monkeypatch.setattr(UsuarioService, "buscar_usuario_por_id", lambda self, user_id: inactive_user)
    app.dependency_overrides[get_db] = lambda: None
    client = TestClient(app)
    token = create_access_token({"user_id": 1})

    try:
        response = client.get("/api/doacoes/", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401
    finally:
        client.close()
        app.dependency_overrides.clear()


def test_inactive_user_cannot_log_in(monkeypatch):
    inactive_user = Usuario(
        id=1,
        nome="Desativado",
        email="desativado@example.test",
        funcao="Operador",
        role="Operador",
        status="Inativo",
    )
    monkeypatch.setattr(UsuarioService, "verificar_credenciais", lambda self, email, password: inactive_user)
    app.dependency_overrides[get_db] = lambda: None
    client = TestClient(app)

    try:
        response = client.post(
            "/api/token",
            data={"username": inactive_user.email, "password": "valid-password"},
        )
        assert response.status_code == 401
    finally:
        client.close()
        app.dependency_overrides.clear()
