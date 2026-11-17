import sqlite3
from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api_main import app
from app.routers import atividades, catalogo, doacoes, facilitadores, organizacao, relatorios
from app.routers.agendamentos import agendar_com_antecedencia, validar_atividade, validar_facilitador
from src.modules.agendamento import AgendamentoService
from src.modules.evento import EventoService
from src.modules.item import ItemService
from src.modules.relatorio import RelatorioService
from src.utils.models import Item, Usuario
from src.utils.dependencies import get_current_user, get_db
from src.utils.schemas import AcolhimentoCreateRequest, AtividadeCreate, DoacaoCreate, FacilitadorCreate, ItemBase, OrganizacaoConfigSchema


class MemoryDB:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn.executescript("""
            CREATE TABLE itens (id INTEGER PRIMARY KEY, nome TEXT, valor_compra NUMERIC,
                valor_venda NUMERIC, status TEXT, id_categoria INTEGER, estoque_minimo INTEGER);
            CREATE TABLE estoque (id INTEGER PRIMARY KEY, id_item INTEGER, quantidade INTEGER, tipo_movimento TEXT);
            CREATE TABLE facilitadores (id INTEGER PRIMARY KEY, nome TEXT, especialidade TEXT,
                observacoes TEXT, status TEXT);
            CREATE TABLE atividades_atendimento (id INTEGER PRIMARY KEY, nome TEXT, descricao TEXT, status TEXT);
            CREATE TABLE pessoas (id INTEGER PRIMARY KEY, nome TEXT, telefone TEXT, documento TEXT);
            CREATE TABLE agendamentos (id INTEGER PRIMARY KEY, id_pessoa INTEGER, id_facilitador INTEGER,
                data_hora TEXT, tipo_servico TEXT, status TEXT, id_evento INTEGER, compareceu TEXT,
                numero_senha TEXT, preferencial BOOLEAN, ordem_chegada INTEGER, observacoes TEXT, id_atividade INTEGER);
            CREATE TABLE eventos (id INTEGER PRIMARY KEY, status TEXT, nome TEXT);
            CREATE TABLE movimentos_financeiros (id INTEGER PRIMARY KEY, data_registro TEXT, id_usuario INTEGER,
                tipo_movimento TEXT, valor NUMERIC, descricao TEXT, categoria TEXT, id_evento INTEGER,
                nome_doador TEXT, forma_pagamento TEXT, status TEXT DEFAULT 'Ativo');
            CREATE TABLE organizacao_config (id INTEGER PRIMARY KEY, nome_organizacao TEXT, tipo_organizacao TEXT,
                termo_assistido TEXT, termo_assistido_plural TEXT, termo_atendente TEXT, termo_servico TEXT,
                termo_atividade TEXT, alias_evento TEXT);
        """)

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False, commit=False, return_rowcount=False):
        params = tuple(float(v) if isinstance(v, Decimal) else v for v in (params or ()))
        cursor = self.conn.execute(query.replace("%s", "?"), params)
        columns = [d[0] for d in cursor.description] if cursor.description else []
        if fetch_one or fetch_all:
            rows = cursor.fetchall()
            rows = [tuple(Decimal(str(v)) if v is not None and c in ("valor_compra", "custo_previsto") else v
                          for c, v in zip(columns, row)) for row in rows]
            return columns, (rows[0] if rows else None) if fetch_one else rows
        if cursor.description:
            result = cursor.fetchone()[0]
        else:
            result = cursor.rowcount if return_rowcount else True
        if commit:
            self.conn.commit()
        return result


@pytest.fixture
def db():
    db = MemoryDB()
    yield db
    db.conn.close()


def test_projecao_considera_saldo_negativo_minimo_e_itens_ativos(db):
    db.conn.executemany("INSERT INTO itens VALUES (?, ?, ?, ?, ?, ?, ?)", [
        (1, "Café", 12.50, 20, "Ativo", None, 5),
        (2, "Chá", 3, 5, "Ativo", None, 2),
        (3, "Água", 4, 5, "Inativo", None, 10),
        (4, "Açúcar", 2, 5, "Ativo", None, 0),
    ])
    db.conn.executemany("INSERT INTO estoque (id_item, quantidade, tipo_movimento) VALUES (?, ?, ?)", [
        (1, 2, "Entrada"), (1, 3, "Saida"), (2, 2, "Entrada"),
    ])
    result = relatorios.get_projecao_estoque(db)
    assert len(result["itens"]) == 1
    item = result["itens"][0]
    assert (item["saldo_atual"], item["estoque_minimo"], item["quantidade_repor"]) == (-1, 5, 6)
    assert item["custo_previsto"] == Decimal("75.00")
    assert result["total_previsto"] == Decimal("75.00")


def test_produto_salva_minimo_e_edicao_legada_o_preserva(db):
    service = ItemService(db)
    item_id = service.registrar_item(Item(nome="Café", valor_compra=Decimal("10"), valor_venda=Decimal("15"), estoque_minimo=4))
    assert service.buscar_item_por_id(item_id).estoque_minimo == 4
    service.editar_item(item_id, "Café", 11, 15, "Ativo", None)
    assert service.buscar_item_por_id(item_id).estoque_minimo == 4
    catalogo.criar_item(ItemBase(nome="Café", valor_compra=12, valor_venda=15), db)
    assert service.buscar_item_por_id(item_id).estoque_minimo == 4
    catalogo.criar_item(ItemBase(nome="Café", valor_compra=12, valor_venda=15, estoque_minimo=0), db)
    assert service.buscar_item_por_id(item_id).estoque_minimo == 0
    with pytest.raises(ValueError):
        ItemBase(nome="Café", valor_compra=10, valor_venda=15, estoque_minimo=-1)


def test_facilitador_preservado_no_agendamento_apos_inativacao(db):
    db.conn.execute("INSERT INTO pessoas (id, nome) VALUES (1, 'João')")
    payload = FacilitadorCreate(nome="Caboclo Pena Verde", especialidade="Consulta")
    fid = facilitadores.criar_facilitador(payload, db)["id"]
    validar_facilitador(db, fid)
    service = AgendamentoService(db)
    service.pre_agendar(1, 1, id_facilitador=fid)
    assert service.listar_pre_agendados(1)[0]["facilitador"] == "Caboclo Pena Verde"
    facilitadores.excluir_facilitador(fid, db)
    assert service.listar_pre_agendados(1)[0]["facilitador"] == "Caboclo Pena Verde"
    with pytest.raises(HTTPException):
        validar_facilitador(db, fid)
    assert facilitadores.listar_facilitadores(db, apenas_ativos=True) == []
    facilitadores.atualizar_facilitador(fid, FacilitadorCreate(nome="Pena Verde", status="Ativo"), db)
    assert service.listar_pre_agendados(1)[0]["facilitador"] == "Pena Verde"
    validar_facilitador(db, fid)
    with pytest.raises(ValueError):
        FacilitadorCreate(nome="   ")


def test_projecao_vazia(db):
    assert relatorios.get_projecao_estoque(db) == {"itens": [], "total_previsto": Decimal("0"), "sem_preco": []}


def test_iniciar_evento_inexistente_nao_fecha_evento_aberto(db):
    db.conn.executemany("INSERT INTO eventos (id, status) VALUES (?, ?)", [(1, "Aberto"), (2, "Agendado")])
    service = EventoService(db)
    assert not service.abrir_evento_existente(99)
    assert db.conn.execute("SELECT status FROM eventos WHERE id = 1").fetchone()[0] == "Aberto"
    assert service.abrir_evento_existente(2)
    assert db.conn.execute("SELECT status FROM eventos ORDER BY id").fetchall() == [("Fechado",), ("Aberto",)]


def test_preco_ausente_e_zero_sao_distintos_na_projecao(db):
    service = ItemService(db)
    sem_custo = service.registrar_item(Item(nome="Café", valor_compra=None, valor_venda=Decimal("3"), estoque_minimo=2))
    service.registrar_item(Item(nome="Chá", valor_compra=Decimal("0"), valor_venda=Decimal("3"), estoque_minimo=1))
    service.registrar_item(Item(nome="Farinha", valor_compra=None, valor_venda=Decimal("3"), estoque_minimo=0))
    resultado = relatorios.get_projecao_estoque(db)
    assert {item["nome"] for item in resultado["sem_preco"]} == {"Café", "Farinha"}
    assert resultado["total_previsto"] == 0
    assert next(item for item in resultado["itens"] if item["id"] == sem_custo)["valor_compra"] is None
    inventario = relatorios.get_inventario(db)
    assert next(item for item in inventario if item.id == sem_custo).valor_compra is None
    catalogo.criar_item(ItemBase(nome="Chá", valor_venda=3), db)
    assert service.buscar_item_por_nome("Chá").valor_compra == 0


def test_atividade_separada_persiste_no_agendamento_inativo(db):
    db.conn.execute("INSERT INTO pessoas (id, nome) VALUES (1, 'João')")
    fid = facilitadores.criar_facilitador(FacilitadorCreate(nome="Padre João"), db)["id"]
    aid = atividades.criar_atividade(AtividadeCreate(nome="Batismo"), db)["id"]
    validar_atividade(db, aid)
    service = AgendamentoService(db)
    agendar_com_antecedencia(AcolhimentoCreateRequest(id_evento=1, id_pessoa=1, id_facilitador=fid, id_atividade=aid), db)
    atividades.inativar_atividade(aid, db)
    row = service.listar_pre_agendados(1)[0]
    assert (row["facilitador"], row["atividade"]) == ("Padre João", "Batismo")
    assert row["tipo_servico"] == "Batismo"
    with pytest.raises(HTTPException):
        validar_atividade(db, aid)


def test_doacao_sem_evento_integra_saldo_e_cancelamento(db):
    usuario = Usuario(id=7, nome="Operador", email="operador@example.test", funcao="Operador")
    payload = DoacaoCreate(valor=Decimal("12.34"), data=date(2026, 11, 17), nome_doador="Ana", forma_pagamento="Pix")
    id_doacao = doacoes.registrar_doacao(payload, db, usuario)["id"]
    assert RelatorioService(db).calcular_saldo_fluxo_caixa() == pytest.approx(12.34)
    row = doacoes.listar_doacoes(db, usuario)[0]
    assert (row["id_evento"], row["nome_doador"], row["forma_pagamento"]) == (None, "Ana", "Pix")
    doacoes.cancelar_doacao(id_doacao, db, usuario)
    assert RelatorioService(db).calcular_saldo_fluxo_caixa() == 0
    with pytest.raises(HTTPException):
        doacoes.cancelar_doacao(id_doacao, db, usuario)
    with pytest.raises(ValueError):
        DoacaoCreate(valor=Decimal("0"), data=date.today())
    with pytest.raises(ValueError):
        DoacaoCreate(valor=Decimal("1.234"), data=date.today())
    with pytest.raises(HTTPException):
        doacoes.registrar_doacao(DoacaoCreate(valor=1, data=date.today(), id_evento=999), db, usuario)


def test_config_legada_nao_apaga_termo_atividade(db):
    payload = dict(nome_organizacao="Casa", tipo_organizacao="Igreja", termo_assistido="Fiel",
                   termo_assistido_plural="Fiéis", termo_atendente="Padre", termo_servico="Consulta")
    organizacao.update_config(OrganizacaoConfigSchema(**payload, termo_atividade="Serviço"), db)
    organizacao.update_config(OrganizacaoConfigSchema(**payload), db)
    assert organizacao.get_config(db).termo_atividade == "Serviço"
    db.conn.execute("INSERT INTO pessoas (id, nome) VALUES (1, 'João')")
    agendar_com_antecedencia(AcolhimentoCreateRequest(id_evento=1, id_pessoa=1), db)
    assert AgendamentoService(db).listar_pre_agendados(1)[0]["tipo_servico"] == "Consulta"


def test_config_alias_evento_e_autorizacao(db):
    payload = dict(nome_organizacao="Casa", tipo_organizacao="Igreja", termo_assistido="Fiel",
                   termo_assistido_plural="Fiéis", termo_atendente="Padre", termo_servico="Consulta")
    admin = Usuario(id=1, nome="Admin", email="admin@example.test", funcao="Admin", role="Administrador")
    operador = Usuario(id=2, nome="Operador", email="op@example.test", funcao="Operador", role="Operador")
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    try:
        assert client.get("/api/organizacao/config").json()["alias_evento"] == "Evento"
        assert client.put("/api/organizacao/config", json=payload).status_code == 401
        app.dependency_overrides[get_current_user] = lambda: operador
        assert client.put("/api/organizacao/config", json=payload).status_code == 403
        assert db.conn.execute("SELECT COUNT(*) FROM organizacao_config").fetchone()[0] == 0
        app.dependency_overrides[get_current_user] = lambda: admin
        response = client.put("/api/organizacao/config", json={**payload, "alias_evento": "Gira",
                                                                 "termo_atividade": "Serviço"})
        assert response.status_code == 200
        assert response.json()["config"]["alias_evento"] == "Gira"
        response = client.put("/api/organizacao/config", json=payload)
        assert response.status_code == 200
        assert response.json()["config"]["alias_evento"] == "Gira"
        assert response.json()["config"]["termo_atividade"] == "Serviço"
        assert client.get("/api/organizacao/config").json()["alias_evento"] == "Gira"
        assert client.put("/api/organizacao/config", json={**payload, "alias_evento": ""}).status_code == 422
        assert client.put("/api/organizacao/config", json={**payload, "alias_evento": "x" * 51}).status_code == 422
        assert client.get("/api/organizacao/config").json()["alias_evento"] == "Gira"
    finally:
        client.close()
        app.dependency_overrides.clear()


def test_api_doacao_exige_usuario_e_aceita_fluxo_sem_evento(db):
    usuario = Usuario(id=7, nome="Operador", email="operador@example.test", funcao="Operador")
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    try:
        assert client.get("/api/doacoes/").status_code == 401
        app.dependency_overrides[get_current_user] = lambda: usuario
        resp = client.post("/api/doacoes/", json={"valor": "15.25", "data": "2026-11-17"})
        assert resp.status_code == 201
        assert client.get("/api/doacoes/").json()[0]["id_evento"] is None
        assert client.get("/api/relatorios/caixa/saldo").json()["valor_raw"] == 15.25
        assert client.patch(f"/api/doacoes/{resp.json()['id']}/cancelar").status_code == 200
        assert client.get("/api/relatorios/caixa/saldo").json()["valor_raw"] == 0
    finally:
        app.dependency_overrides.clear()
        client.close()
