from datetime import date, datetime, timezone
from decimal import Decimal

from src.modules.estoque import EstoqueService
from src.modules.venda import VendaService


class RecentSalesDB:
    def __init__(self):
        self.columns = [
            "id", "id_pessoa", "data_venda", "data_hora_venda", "responsavel",
            "id_evento", "id_item", "nome_item", "quantidade", "valor_unitario",
        ]
        self.rows = [
            (12, 4, date(2025, 5, 2), datetime(2025, 5, 2, 14, 30, tzinfo=timezone.utc),
             "8", 3, 5, "Café", 2, Decimal("4.50")),
            (12, 4, date(2025, 5, 2), datetime(2025, 5, 2, 14, 30, tzinfo=timezone.utc),
             "8", 3, 6, "Bolo", 1, Decimal("7.00")),
        ]
        self.params = None

    def execute_query(self, query, params=None, fetch_all=False):
        self.params = params
        return self.columns, self.rows


def test_historico_agrega_itens_e_calcula_total():
    db = RecentSalesDB()
    service = VendaService(db, None, None)

    sales = service.buscar_ultimas_vendas_com_itens(10)

    assert db.params == (10,)
    assert len(sales) == 1
    assert [item["nome"] for item in sales[0]["itens"]] == ["Café", "Bolo"]
    assert sales[0]["total"] == Decimal("16.00")
    assert sales[0]["data_hora_venda"] == datetime(2025, 5, 2, 14, 30, tzinfo=timezone.utc)


class StockMovementDB:
    def __init__(self):
        self.params = None

    def execute_query(self, query, params=None, commit=False):
        self.params = params
        return 21


def test_saida_manual_persiste_motivo_informado():
    db = StockMovementDB()
    service = EstoqueService(db)

    result = service.saida_item(
        id_item=5,
        quantidade=2,
        id_usuario=8,
        id_evento=3,
        origem_recurso="Avaria",
    )

    assert result == 21
    assert db.params[3] == "Avaria"
