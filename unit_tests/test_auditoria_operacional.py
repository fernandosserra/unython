from decimal import Decimal
import sqlite3
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api_main import app
from app.routers import caixas, estoque, usuarios, vendas
from src.modules.estoque import EstoqueService
from src.modules.organizacao import OrganizacaoService
from src.modules.venda import VendaService
from src.utils.audit import record_audit
from src.utils.dependencies import get_current_user, get_db
from src.utils.models import ItemVenda, OrganizacaoConfig, Usuario, Venda


@pytest.fixture
def api(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr(OrganizacaoService, "obter_configuracoes", lambda self: OrganizacaoConfig())
    actor = Usuario(id=7, nome="Operador", email="op@example.test", funcao="Admin", role="Administrador")
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: actor
    client = TestClient(app, raise_server_exceptions=False)
    try:
        yield db, client
    finally:
        client.close()
        app.dependency_overrides.clear()


def test_record_audit_never_commits():
    db = MagicMock()
    record_audit(db, user_id=7, acao="abrir_caixa", entidade="movimento_caixa",
                 entidade_id=20, detalhes={"valor": "10.00"}, request_id="request-123")
    args, kwargs = db.execute_query.call_args
    assert args[1][:4] == (7, "abrir_caixa", "movimento_caixa", 20)
    assert args[1][4].adapted == {"valor": "10.00"}
    assert args[1][5] == "request-123"
    assert kwargs["commit"] is False
    db.conn.commit.assert_not_called()


@pytest.mark.parametrize("fails", [False, True])
def test_abertura_caixa_audit_actor_e_rollback(api, monkeypatch, fails):
    db, client = api
    service = MagicMock()
    service.buscar_movimento_ativo.return_value = None
    service.abrir_movimento.return_value = 22
    monkeypatch.setattr(caixas, "CaixaService", lambda db: service)
    audit = MagicMock(side_effect=RuntimeError("falha") if fails else None)
    monkeypatch.setattr(caixas, "record_audit", audit)
    response = client.post("/api/caixas/4/abrir", json={"usuario_id": 999, "valor_abertura": 10, "id_evento": 3},
                           headers={"X-Request-ID": "request-123"})
    assert response.status_code == (500 if fails else 201)
    service.abrir_movimento.assert_called_once_with(4, 7, Decimal("10"), 3, commit=False)
    assert audit.call_args.kwargs["user_id"] == 7
    assert audit.call_args.kwargs["request_id"] == "request-123"
    assert db.conn.commit.call_count == (0 if fails else 1)
    assert db.conn.rollback.call_count == (1 if fails else 0)


def test_fechamento_auditado_so_quando_altera(api, monkeypatch):
    db, client = api
    service = MagicMock()
    service.fechar_movimento.return_value = False
    monkeypatch.setattr(caixas, "CaixaService", lambda db: service)
    audit = MagicMock()
    monkeypatch.setattr(caixas, "record_audit", audit)
    assert client.post("/api/caixas/42/fechar").status_code == 400
    audit.assert_not_called()
    db.conn.rollback.assert_called_once()
    service.fechar_movimento.return_value = True
    assert client.post("/api/caixas/42/fechar").status_code == 200
    assert audit.call_args.kwargs["entidade_id"] == 42
    db.conn.commit.assert_called_once()


def test_saida_ignora_usuario_informado_e_audita(api, monkeypatch):
    db, client = api
    service = MagicMock()
    service.saida_item.return_value = 31
    monkeypatch.setattr(estoque, "EstoqueService", lambda db: service)
    audit = MagicMock()
    monkeypatch.setattr(estoque, "record_audit", audit)
    response = client.post("/api/estoque/saida", json={
        "itemId": 2, "quantidade": 3, "usuarioId": 999, "eventoId": 4, "origem_recurso": "Avaria",
    })
    assert response.status_code == 201
    assert service.saida_item.call_args.kwargs["id_usuario"] == 7
    assert service.saida_item.call_args.kwargs["commit"] is False
    assert audit.call_args.kwargs["detalhes"]["quantidade"] == 3
    assert audit.call_args.kwargs["user_id"] == 7
    db.conn.commit.assert_called_once()


@pytest.mark.parametrize("existing", [True, False])
def test_cadastro_audita_atualizacao_sem_gravar_senha(api, monkeypatch, existing):
    db, client = api
    previous = Usuario(id=9, nome="Antigo", email="p@example.test", funcao="Operador", role="Operador")
    service = MagicMock()
    service.buscar_usuario_por_email.return_value = previous if existing else None
    service.buscar_usuario_por_id.return_value = previous
    service.registrar_usuario.return_value = 9
    monkeypatch.setattr(usuarios, "UsuarioService", lambda db: service)
    audit = MagicMock()
    monkeypatch.setattr(usuarios, "record_audit", audit)
    response = client.post("/api/usuarios/", json={"nome": "Pessoa", "email": "p@example.test",
                           "role": "Administrador", "senha": "senha-secreta"})
    assert response.status_code == 201
    assert service.registrar_usuario.call_args.kwargs["commit"] is False
    assert audit.call_count == int(existing)
    if existing:
        assert audit.call_args.kwargs["detalhes"]["role_anterior"] == "Operador"
        assert "senha" not in repr(audit.call_args)
    db.conn.commit.assert_called_once()


def test_alteracao_role_audita_estados_e_rollback(api, monkeypatch):
    db, client = api
    previous = Usuario(id=9, nome="Antigo", email="p@example.test", funcao="Operador", role="Operador")
    service = MagicMock()
    service.buscar_usuario_por_id.return_value = previous
    service.atualizar_role_status.return_value = True
    monkeypatch.setattr(usuarios, "UsuarioService", lambda db: service)
    audit = MagicMock(side_effect=RuntimeError("falha"))
    monkeypatch.setattr(usuarios, "record_audit", audit)
    response = client.put("/api/usuarios/9/role", json={"role": "Administrador", "status": "Inativo"})
    assert response.status_code == 500
    assert audit.call_args.kwargs["detalhes"]["status_anterior"] == "Ativo"
    assert audit.call_args.kwargs["detalhes"]["status_novo"] == "Inativo"
    db.conn.commit.assert_not_called()
    db.conn.rollback.assert_called_once()


def test_venda_responsavel_derivado_do_token(api, monkeypatch):
    db, client = api
    sale = MagicMock()
    sale.registrar_venda_completa.return_value = 14
    stock = MagicMock()
    stock.calcular_saldo_item.return_value = 10
    monkeypatch.setattr(vendas, "EstoqueService", lambda db: stock)
    monkeypatch.setattr(vendas, "VendaService", lambda *args: sale)
    response = client.post("/api/vendas/", json={"eventoId": 3, "movimentoCaixaId": 5,
                            "responsavelId": 999, "itens": [{"itemId": 1, "quantidade": 2, "valor_unitario": 4}]})
    assert response.status_code == 201
    assert sale.registrar_venda_completa.call_args.args[0].responsavel == "7"


@pytest.mark.parametrize("path", ["/api/vendas/", "/vendas/", "/api/caixas/", "/caixas/"])
def test_vendas_e_caixas_exigem_token(path):
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)
    try:
        assert client.get(path).status_code == 401
    finally:
        client.close()
        app.dependency_overrides.clear()


def test_abertura_automatica_venda_e_auditoria_fazem_rollback(api, monkeypatch):
    db, client = api
    cash = MagicMock()
    cash.buscar_movimento_ativo.return_value = None
    cash.abrir_movimento.return_value = 22
    stock = MagicMock()
    stock.calcular_saldo_item.return_value = 0
    audit = MagicMock()
    monkeypatch.setattr(vendas, "CaixaService", lambda db: cash)
    monkeypatch.setattr(vendas, "EstoqueService", lambda db: stock)
    monkeypatch.setattr(vendas, "record_audit", audit)
    response = client.post("/api/vendas/", json={"eventoId": 3, "caixaId": 5,
                            "itens": [{"itemId": 1, "quantidade": 2, "valor_unitario": 4}]})
    assert response.status_code == 400
    cash.abrir_movimento.assert_called_once_with(5, 7, Decimal("0.00"), 3, commit=False)
    assert audit.call_args.kwargs["user_id"] == 7
    db.conn.commit.assert_not_called()
    db.conn.rollback.assert_called_once()


def test_venda_rollback_se_segunda_baixa_falha():
    db = MagicMock()
    stock = MagicMock()
    stock.calcular_saldo_item.return_value = 10
    stock.registrar_movimento.side_effect = [1, RuntimeError("erro")]
    service = VendaService(db, stock, None)
    service.registrar_venda = MagicMock(return_value=4)
    service.registrar_item_venda = MagicMock(return_value=5)
    sale = Venda(id_pessoa=None, responsavel="7", id_evento=3, id_movimento_caixa=2)
    items = [ItemVenda(id_venda=0, id_item=i, quantidade=1, valor_unitario=Decimal("3")) for i in [1, 2]]
    assert service.registrar_venda_completa(sale, items) is None
    assert all(call.kwargs["commit"] is False for call in stock.registrar_movimento.call_args_list)
    db.conn.commit.assert_not_called()
    db.conn.rollback.assert_called_once()


def test_estoque_commit_explicito():
    db = MagicMock()
    service = EstoqueService(db)
    service.saida_item(1, 2, 7, 3, commit=False)
    assert db.execute_query.call_args.kwargs["commit"] is False


def test_venda_desfaz_todas_insercoes_apos_falha_na_segunda_baixa():
    class TransactionDB:
        def __init__(self):
            self.conn = sqlite3.connect(":memory:")
            self.conn.executescript("""
                CREATE TABLE vendas (id INTEGER PRIMARY KEY, id_pessoa INTEGER, data_venda TEXT,
                    responsavel TEXT, id_evento INTEGER, id_movimento_caixa INTEGER);
                CREATE TABLE itens_venda (id INTEGER PRIMARY KEY, id_venda INTEGER, id_item INTEGER,
                    quantidade INTEGER, valor_unitario TEXT);
                CREATE TABLE estoque (id INTEGER PRIMARY KEY, id_item INTEGER, quantidade INTEGER,
                    tipo_movimento TEXT, origem_recurso TEXT, id_usuario INTEGER, id_evento INTEGER,
                    data_movimento TEXT);
            """)
            self.stock_writes = 0

        def execute_query(self, query, params=None, commit=False, fetch_one=False):
            if query.strip().startswith("INSERT INTO estoque"):
                self.stock_writes += 1
                if self.stock_writes == 2:
                    raise RuntimeError("baixa indisponível")
            values = tuple(str(v) if isinstance(v, Decimal) else v for v in (params or ()))
            cursor = self.conn.execute(query.replace("%s", "?"), values)
            if fetch_one:
                return [col[0] for col in cursor.description], cursor.fetchone()
            result = cursor.fetchone()[0] if cursor.description else True
            if commit:
                self.conn.commit()
            return result

    db = TransactionDB()
    stock = EstoqueService(db)
    stock.calcular_saldo_item = MagicMock(return_value=10)
    service = VendaService(db, stock, None)
    sale = Venda(id_pessoa=None, responsavel="7", id_evento=3, id_movimento_caixa=2)
    items = [ItemVenda(id_venda=0, id_item=i, quantidade=1, valor_unitario=Decimal("3")) for i in [1, 2]]
    try:
        assert service.registrar_venda_completa(sale, items) is None
        for table in ("vendas", "itens_venda", "estoque"):
            assert db.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    finally:
        db.conn.close()
