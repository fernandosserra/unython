from datetime import datetime
from decimal import Decimal

import pytest

from src.modules.agendamento import AgendamentoService
from src.modules.caixas import CaixaService
from src.modules.categoria import CategoriaService
from src.modules.estoque import EstoqueService
from src.modules.evento import EventoService
from src.modules.fluxo_caixa import FluxoDeCaixaService
from src.modules.item import ItemService
from src.modules.pessoa import PessoaService
from src.modules.relatorio import RelatorioService
from src.modules.usuario import UsuarioService
from src.modules.venda import VendaService
from src.utils.config import get_alias
from src.utils.models import (
    Agendamento,
    Caixa,
    Categoria,
    Evento,
    Item,
    ItemVenda,
    MovimentoFinanceiro,
    Pessoa,
    Usuario,
    Venda,
)
from src.utils.security import verify_password


@pytest.fixture
def seed_basico(db_manager):
    pessoa_srv = PessoaService(db_manager)
    usuario_srv = UsuarioService(db_manager)
    evento_srv = EventoService(db_manager)

    alias_facilitador = get_alias("FACILITADOR")
    senha_master = "minhasenhaadmin123"

    evento = Evento(
        nome=f"Atendimento e Feirinha {datetime.now():%Y-%m-%d}",
        data_evento=datetime.now().date(),
        tipo="Atendimento e Venda",
    )
    id_evento = evento_srv.registrar_evento(evento)

    facilitador = Usuario(
        nome="Dra. Washu Hakubi",
        email="washu@unython.com",
        funcao=get_alias("FUNCAO_FACILITADOR"),
        role="Administrador",
        status="Ativo",
    )
    id_facilitador = usuario_srv.registrar_usuario(facilitador, senha_master)
    usuario_db = usuario_srv.buscar_usuario_por_email(facilitador.email)
    assert usuario_db, "Usuário não encontrado."
    assert verify_password(senha_master, usuario_db.hashed_password), "Senha incorreta."
    assert usuario_db.role == "Administrador", "Role inesperada."

    pessoa = Pessoa(nome="Fernando, O Aprendiz", telefone="551199887766")
    id_pessoa = pessoa_srv.registrar_pessoa(pessoa)

    return {
        "id_evento": id_evento,
        "id_facilitador": id_facilitador,
        "id_pessoa": id_pessoa,
        "alias_facilitador": alias_facilitador,
    }


@pytest.fixture
def catalogo(db_manager):
    cat_srv = CategoriaService(db_manager)
    item_srv = ItemService(db_manager)

    id_cat_bebidas = cat_srv.registrar_categoria(Categoria(nome="Bebidas", descricao="Refrigerantes, Agua, Sucos"))
    id_cat_esotericos = cat_srv.registrar_categoria(Categoria(nome="Esotericos", descricao="Velas, Incensos, Banhos"))

    id_coca = item_srv.registrar_item(
        Item(nome="Coca Cola Lata", valor_compra=Decimal("1.50"), valor_venda=Decimal("2.50"), id_categoria=id_cat_bebidas)
    )
    id_vela = item_srv.registrar_item(
        Item(nome="Vela 7 Dias", valor_compra=Decimal("5.00"), valor_venda=Decimal("10.00"), id_categoria=id_cat_esotericos)
    )

    return {"id_coca": id_coca, "id_vela": id_vela}


def test_agendamento_fluxo_inicial(db_manager, seed_basico):
    ag_srv = AgendamentoService(db_manager)
    relatorio_srv = RelatorioService(db_manager)

    agendamento = Agendamento(
        id_pessoa=seed_basico["id_pessoa"],
        id_facilitador=seed_basico["id_facilitador"],
        id_evento=seed_basico["id_evento"],
        data_hora=datetime.now().replace(second=0, microsecond=0),
        tipo_servico=get_alias("TIPO_SERVICO"),
    )
    ag_srv.registrar_agendamento(agendamento)

    pendentes = ag_srv.buscar_agendamentos(status="Agendado")
    assert pendentes, "Agendamento não foi salvo."

    relatorio = relatorio_srv.gerar_detalhe_agendamentos_pendentes()
    assert relatorio, "Relatório de agendamentos não retornou dados."


def test_venda_sucesso_com_caixa(db_manager, seed_basico, catalogo):
    estoque_srv = EstoqueService(db_manager)
    caixa_srv = CaixaService(db_manager)
    venda_srv = VendaService(db_manager, estoque_srv, caixa_srv)

    estoque_srv.entrada_item(
        id_item=catalogo["id_coca"],
        quantidade=20,
        origem_recurso="Doacao Inicial",
        id_usuario=seed_basico["id_facilitador"],
        id_evento=seed_basico["id_evento"],
    )

    id_caixa = caixa_srv.registrar_caixa(Caixa(nome="Caixa Principal", descricao="Caixa 1 do PDV"))
    id_mov = caixa_srv.abrir_movimento(
        id_caixa=id_caixa, id_usuario_abertura=seed_basico["id_facilitador"], valor_abertura=Decimal("100.00")
    )

    venda = Venda(
        id_pessoa=seed_basico["id_pessoa"],
        responsavel=str(seed_basico["id_facilitador"]),
        id_evento=seed_basico["id_evento"],
        id_movimento_caixa=id_mov,
    )
    itens = [ItemVenda(id_venda=0, id_item=catalogo["id_coca"], quantidade=2, valor_unitario=Decimal("2.50"))]

    id_venda = venda_srv.registrar_venda_completa(venda, itens)
    assert id_venda, "Venda deveria ter sido registrada."

    caixa_srv.fechar_movimento(id_mov)


def test_venda_bloqueada_por_estoque_insuficiente(db_manager, seed_basico, catalogo):
    estoque_srv = EstoqueService(db_manager)
    caixa_srv = CaixaService(db_manager)
    venda_srv = VendaService(db_manager, estoque_srv, caixa_srv)

    estoque_srv.entrada_item(
        id_item=catalogo["id_coca"],
        quantidade=1,
        origem_recurso="Estoque minimo para falha",
        id_usuario=seed_basico["id_facilitador"],
        id_evento=seed_basico["id_evento"],
    )

    id_caixa = caixa_srv.registrar_caixa(Caixa(nome="Caixa Falha", descricao="Caixa para teste de falha"))
    id_mov = caixa_srv.abrir_movimento(
        id_caixa=id_caixa, id_usuario_abertura=seed_basico["id_facilitador"], valor_abertura=Decimal("10.00")
    )

    venda = Venda(
        id_pessoa=seed_basico["id_pessoa"],
        responsavel=str(seed_basico["id_facilitador"]),
        id_evento=seed_basico["id_evento"],
        id_movimento_caixa=id_mov,
    )
    itens = [ItemVenda(id_venda=0, id_item=catalogo["id_coca"], quantidade=100, valor_unitario=Decimal("2.50"))]

    id_venda = venda_srv.registrar_venda_completa(venda, itens)
    assert not id_venda, "Venda deveria ser bloqueada por falta de estoque."

    caixa_srv.fechar_movimento(id_mov)


def test_relatorios_financeiros_e_inventario(db_manager, seed_basico, catalogo):
    estoque_srv = EstoqueService(db_manager)
    caixa_srv = CaixaService(db_manager)
    venda_srv = VendaService(db_manager, estoque_srv, caixa_srv)
    relatorio_srv = RelatorioService(db_manager)
    fluxo_srv = FluxoDeCaixaService(db_manager)

    # Estoque + venda para gerar dados
    estoque_srv.entrada_item(
        id_item=catalogo["id_coca"],
        quantidade=5,
        origem_recurso="Entrada teste",
        id_usuario=seed_basico["id_facilitador"],
        id_evento=seed_basico["id_evento"],
    )
    id_caixa = caixa_srv.registrar_caixa(Caixa(nome="Caixa Relatorio", descricao=""))
    id_mov = caixa_srv.abrir_movimento(
        id_caixa=id_caixa, id_usuario_abertura=seed_basico["id_facilitador"], valor_abertura=Decimal("50.00")
    )
    venda = Venda(
        id_pessoa=seed_basico["id_pessoa"],
        responsavel=str(seed_basico["id_facilitador"]),
        id_evento=seed_basico["id_evento"],
        id_movimento_caixa=id_mov,
    )
    itens = [ItemVenda(id_venda=0, id_item=catalogo["id_coca"], quantidade=1, valor_unitario=Decimal("2.50"))]
    venda_srv.registrar_venda_completa(venda, itens)
    caixa_srv.fechar_movimento(id_mov)

    # Movimentos financeiros adicionais
    fluxo_srv.registrar_movimento(
        MovimentoFinanceiro(
            id_usuario=seed_basico["id_facilitador"],
            tipo_movimento="Receita",
            valor=Decimal("250.00"),
            descricao="Doacao",
            categoria="Doacao",
            id_evento=seed_basico["id_evento"],
        )
    )
    fluxo_srv.registrar_movimento(
        MovimentoFinanceiro(
            id_usuario=seed_basico["id_facilitador"],
            tipo_movimento="Despesa",
            valor=Decimal("50.00"),
            descricao="Material",
            categoria="Material",
            id_evento=seed_basico["id_evento"],
        )
    )

    assert relatorio_srv.gerar_faturamento_mensal() is not None
    assert relatorio_srv.gerar_lucro_bruto_mensal() is not None
    assert relatorio_srv.gerar_inventario_total() is not None
    assert relatorio_srv.gerar_despesas_por_categoria() is not None
    assert relatorio_srv.calcular_saldo_fluxo_caixa() is not None


def test_usuario_require_password_change(db_manager):
    usuario_srv = UsuarioService(db_manager)
    usuario = Usuario(
        nome="Admin Bootstrap",
        email="admin@unython.local",
        funcao="Administrador",
        role="Administrador",
        status="Ativo",
        require_password_change=True,
    )
    uid = usuario_srv.registrar_usuario(usuario, "old123", require_password_change=True)
    fetched = usuario_srv.buscar_usuario_por_id(uid)
    assert fetched and fetched.require_password_change

    ok = usuario_srv.alterar_senha(usuario.email, "old123", "new456")
    assert ok
    fetched2 = usuario_srv.buscar_usuario_por_id(uid)
    assert fetched2 and not fetched2.require_password_change
    assert usuario_srv.verificar_credenciais(usuario.email, "new456")
