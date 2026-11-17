from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api_main import app
from src.modules.caixas import CaixaService
from src.modules.categoria import CategoriaService
from src.modules.evento import EventoService
from src.modules.organizacao import OrganizacaoService
from src.modules.relatorio import RelatorioService
from src.utils.dependencies import get_current_user, get_db
from src.utils.models import OrganizacaoConfig, Usuario


@pytest.fixture
def client(monkeypatch):
    config = OrganizacaoConfig()
    monkeypatch.setattr(OrganizacaoService, "obter_configuracoes", lambda self: config)
    monkeypatch.setattr(CaixaService, "buscar_todos_caixas", lambda self: [])
    monkeypatch.setattr(CategoriaService, "buscar_todas_categorias", lambda self: [])
    monkeypatch.setattr(EventoService, "buscar_evento_aberto", lambda self: None)
    monkeypatch.setattr(RelatorioService, "calcular_saldo_fluxo_caixa", lambda self: 0)
    app.dependency_overrides[get_db] = lambda: MagicMock()
    test_client = TestClient(app)
    try:
        yield test_client, config
    finally:
        test_client.close()
        app.dependency_overrides.clear()


def use_user(permissoes, role="Operador"):
    user = Usuario(id=1, nome="Teste", email="teste@example.test", funcao="Operador",
                   role=role, permissoes=permissoes)
    app.dependency_overrides[get_current_user] = lambda: user


@pytest.mark.parametrize(
    ("method", "path", "permissoes", "expected"),
    [
        ("get", "/api/caixas/", ["pdv"], 200),
        ("get", "/api/caixas/", ["atendimentos"], 403),
        ("post", "/api/caixas/", ["pdv"], 403),
        ("get", "/api/catalogo/categorias", ["estoque"], 200),
        ("get", "/api/catalogo/categorias", ["pdv"], 200),
        ("get", "/api/catalogo/categorias", ["caixa"], 403),
        ("post", "/api/catalogo/categorias", None, 403),
        ("post", "/api/catalogo/categorias", ["estoque"], 422),
        ("post", "/api/atividades/", None, 403),
        ("post", "/api/atividades/", ["atendimentos"], 422),
        ("get", "/api/relatorios/caixa/saldo", None, 200),
        ("get", "/api/relatorios/caixa/saldo", [], 403),
        ("get", "/api/relatorios/relatorio-gerencial", None, 403),
        ("get", "/api/eventos/aberto", ["doacoes"], 404),
        ("get", "/api/eventos/aberto", ["estoque"], 404),
        ("get", "/api/eventos/", ["estoque"], 403),
        ("post", "/api/eventos/novo", ["caixa"], 403),
        ("post", "/api/eventos/novo", ["atendimentos"], 422),
        ("post", "/api/eventos/abrir", ["atendimentos"], 403),
    ],
)
def test_module_permissions_on_routes(client, method, path, permissoes, expected):
    test_client, _ = client
    use_user(permissoes)
    assert test_client.request(method, path).status_code == expected


def test_shared_reads_skip_flags_but_feature_routes_do_not(client):
    test_client, config = client
    config.habilitar_pdv = False
    use_user(["pdv"])
    assert test_client.get("/api/catalogo/categorias").status_code == 200
    assert test_client.get("/api/caixas/").status_code == 200
    assert test_client.get("/api/vendas/").status_code == 403
    use_user([], role="Administrador")
    assert test_client.get("/api/vendas/").status_code == 403
