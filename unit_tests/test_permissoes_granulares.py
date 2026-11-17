from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api_main import app
from src.modules.organizacao import OrganizacaoService
from src.modules.usuario import UsuarioService
from src.utils.dependencies import get_current_user, get_db, require_module
from src.utils.models import Usuario
from src.utils.security import create_access_token


def usuario(permissoes=None, role="Operador"):
    return Usuario(id=7, nome="Pessoa", email="p@example.test", funcao="Operador",
                   role=role, permissoes=permissoes)


@pytest.mark.parametrize(
    ("permissoes", "role", "modulo", "legacy_admin_only", "expected"),
    [
        (None, "Operador", "pdv", False, 200),
        ([], "Operador", "pdv", False, 403),
        (["caixa"], "Operador", "pdv", False, 403),
        (["pdv"], "Operador", "pdv", False, 200),
        (None, "Operador", "atendimentos", True, 403),
        (["atendimentos"], "Operador", "atendimentos", True, 200),
        ([], "Administrador", "pdv", False, 200),
    ],
)
def test_permissoes_legadas_explicitas_e_admin(monkeypatch, permissoes, role, modulo, legacy_admin_only, expected):
    test_app = FastAPI()

    @test_app.get("/")
    def endpoint(_=Depends(require_module(modulo, legacy_admin_only=legacy_admin_only))):
        return {"ok": True}

    test_app.dependency_overrides[get_current_user] = lambda: usuario(permissoes, role)
    test_app.dependency_overrides[get_db] = lambda: None
    monkeypatch.setattr(OrganizacaoService, "obter_configuracoes", lambda _: SimpleNamespace(
        habilitar_pdv=True, habilitar_atendimentos=True, habilitar_doacoes=True))
    with TestClient(test_app) as client:
        assert client.get("/").status_code == expected


def test_modulo_desabilitado_na_organizacao(monkeypatch):
    test_app = FastAPI()

    @test_app.get("/")
    def endpoint(_=Depends(require_module("pdv"))):
        return {"ok": True}

    test_app.dependency_overrides[get_current_user] = lambda: usuario(["pdv"])
    test_app.dependency_overrides[get_db] = lambda: None
    monkeypatch.setattr(OrganizacaoService, "obter_configuracoes", lambda _: SimpleNamespace(habilitar_pdv=False))
    with TestClient(test_app) as client:
        assert client.get("/").status_code == 403


def test_atualizar_permissoes_audita_e_aplica_transacao(monkeypatch):
    db = MagicMock()
    before = usuario(None)
    monkeypatch.setattr(UsuarioService, "buscar_usuario_por_id", lambda self, uid: before)
    monkeypatch.setattr(UsuarioService, "atualizar_permissoes", lambda self, uid, value, **kw: True)
    audit = MagicMock()
    monkeypatch.setattr("app.routers.usuarios.record_audit", audit)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: usuario(role="Administrador")
    client = TestClient(app)
    try:
        response = client.put("/api/usuarios/7/permissoes", json={"permissoes": []})
        assert response.status_code == 200
        assert response.json()["permissoes"] == []
        assert audit.call_args.kwargs["detalhes"] == {
            "permissoes_anteriores": None, "permissoes_novas": [],
        }
        db.conn.commit.assert_called_once()
        assert client.put("/api/usuarios/7/permissoes", json={"permissoes": ["invalido"]}).status_code == 422
    finally:
        client.close()
        app.dependency_overrides.clear()


def test_revogacao_aplicada_ao_mesmo_token(monkeypatch):
    atual = usuario(["doacoes"])
    db = MagicMock()
    db.execute_query.return_value = ([], [])
    monkeypatch.setattr(UsuarioService, "buscar_usuario_por_id", lambda self, uid: atual)
    monkeypatch.setattr(OrganizacaoService, "obter_configuracoes", lambda _: SimpleNamespace(habilitar_doacoes=True))
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {create_access_token({'user_id': atual.id})}"}
    try:
        assert client.get("/api/doacoes/", headers=headers).status_code == 200
        atual.permissoes = []
        assert client.get("/api/doacoes/", headers=headers).status_code == 403
    finally:
        client.close()
        app.dependency_overrides.clear()


def test_auditoria_falha_reverte_permissoes(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr(UsuarioService, "buscar_usuario_por_id", lambda self, uid: usuario())
    monkeypatch.setattr(UsuarioService, "atualizar_permissoes", lambda self, uid, value, **kw: True)
    monkeypatch.setattr("app.routers.usuarios.record_audit", MagicMock(side_effect=RuntimeError("falha")))
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: usuario(role="Administrador")
    client = TestClient(app, raise_server_exceptions=False)
    try:
        assert client.put("/api/usuarios/7/permissoes", json={"permissoes": []}).status_code == 500
        db.conn.rollback.assert_called_once()
        db.conn.commit.assert_not_called()
    finally:
        client.close()
        app.dependency_overrides.clear()


@pytest.mark.parametrize("permissoes", [[], ["estoque"], ["atendimentos", "caixa", "pdv"]])
def test_cadastro_e_edicao_persistem_permissoes_explicitas(monkeypatch, permissoes):
    db = MagicMock()
    before = usuario(None)
    service = MagicMock()
    service.buscar_usuario_por_email.return_value = None
    service.buscar_usuario_por_id.return_value = before
    service.registrar_usuario.return_value = 7
    service.atualizar_role_status.return_value = True
    service.atualizar_permissoes.return_value = True
    monkeypatch.setattr("app.routers.usuarios.UsuarioService", lambda db: service)
    audit = MagicMock()
    monkeypatch.setattr("app.routers.usuarios.record_audit", audit)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: usuario(role="Administrador")
    client = TestClient(app)
    try:
        created = client.post("/api/usuarios/", json={
            "nome": "Pessoa", "email": "p@example.test", "senha": "senha",
            "funcao": "Apoio", "role": "Operador", "permissoes": permissoes,
        })
        assert created.status_code == 201
        assert service.registrar_usuario.call_args.args[0].permissoes == permissoes
        updated = client.put("/api/usuarios/7", json={
            "funcao": "Apoio", "role": "Operador", "status": "Ativo", "permissoes": permissoes,
        })
        assert updated.status_code == 200
        assert updated.json()["permissoes"] == permissoes
        service.atualizar_permissoes.assert_called_once_with(7, permissoes, commit=False)
        assert audit.call_args.kwargs["detalhes"]["permissoes_novas"] == permissoes
        assert db.conn.commit.call_count == 2
        assert client.put("/api/usuarios/7", json={
            "role": "Operador", "permissoes": ["pdv", "pdv"],
        }).status_code == 422
        assert client.put("/api/usuarios/7", json={
            "role": "Operador", "permissoes": None,
        }).status_code == 422
    finally:
        client.close()
        app.dependency_overrides.clear()


def test_edicao_unificada_reverte_se_auditoria_falhar(monkeypatch):
    db = MagicMock()
    service = MagicMock()
    service.buscar_usuario_por_id.return_value = usuario(["estoque"])
    service.atualizar_role_status.return_value = True
    service.atualizar_permissoes.return_value = True
    monkeypatch.setattr("app.routers.usuarios.UsuarioService", lambda db: service)
    monkeypatch.setattr("app.routers.usuarios.record_audit", MagicMock(side_effect=RuntimeError("falha")))
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: usuario(role="Administrador")
    client = TestClient(app, raise_server_exceptions=False)
    try:
        response = client.put("/api/usuarios/7", json={
            "role": "Operador", "permissoes": ["caixa"],
        })
        assert response.status_code == 500
        db.conn.rollback.assert_called_once()
        db.conn.commit.assert_not_called()
    finally:
        client.close()
        app.dependency_overrides.clear()


def test_edicao_unificada_exige_administrador():
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: usuario(["estoque"])
    client = TestClient(app)
    try:
        assert client.put("/api/usuarios/7", json={"role": "Operador", "permissoes": []}).status_code == 403
    finally:
        client.close()
        app.dependency_overrides.clear()
