# src/modules/venda.py
from typing import List, Optional
from decimal import Decimal

from src.utils.database_manager import DatabaseManager
from src.utils.models import ItemVenda, MovimentoEstoque, Venda
from src.modules.estoque import EstoqueService
from src.modules.caixas import CaixaService


class VendaService:
    """
    Coordena transações de venda, garantindo atomicidade e vínculo com o movimento de caixa.
    """

    def __init__(self, db_manager: DatabaseManager, estoque_service: EstoqueService, caixa_service: CaixaService):
        self.db = db_manager
        self.estoque_service = estoque_service
        self.caixa_service = caixa_service

    # -----------------------------------------------------------
    # Inserções auxiliares (sem commit)
    # -----------------------------------------------------------

    def registrar_venda(self, venda: Venda) -> Optional[int]:
        """Registra o cabeçalho da venda (sem commit)."""
        query = """
        INSERT INTO vendas (id_pessoa, data_venda, responsavel, id_evento, id_movimento_caixa)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
        """
        values = (venda.id_pessoa, venda.data_venda, venda.responsavel, venda.id_evento, venda.id_movimento_caixa)
        return self.db.execute_query(query, values, commit=False)

    def registrar_item_venda(self, item_venda: ItemVenda) -> Optional[int]:
        """Registra o detalhe de item de uma venda (sem commit)."""
        query = "INSERT INTO itens_venda (id_venda, id_item, quantidade, valor_unitario) VALUES (%s, %s, %s, %s) RETURNING id"
        values = (item_venda.id_venda, item_venda.id_item, item_venda.quantidade, item_venda.valor_unitario)
        return self.db.execute_query(query, values, commit=False)

    # -----------------------------------------------------------
    # Fluxo principal: venda completa com baixa de estoque
    # -----------------------------------------------------------

    def registrar_venda_completa(self, venda_cabecalho: Venda, itens_detalhe: List[ItemVenda]) -> Optional[int]:
        """
        Insere cabeçalho, itens e baixa estoque em uma transação.
        Se qualquer passo falhar, executa rollback e retorna None.
        """
        id_venda = None

        try:
            # 0. Checagem de estoque
            for item_venda in itens_detalhe:
                saldo = self.estoque_service.calcular_saldo_item(item_venda.id_item)
                if saldo < item_venda.quantidade:
                    raise Exception(f"Estoque Insuficiente! Item ID {item_venda.id_item} (Necessário: {item_venda.quantidade}, Saldo: {saldo})")

            # 1. Cabeçalho
            id_venda = self.registrar_venda(venda_cabecalho)
            if not isinstance(id_venda, int) or id_venda <= 0:
                raise Exception("Falha ao criar o cabeçalho da Venda. ID não foi capturado.")

            # 2. Detalhes + saída de estoque
            for item_venda in itens_detalhe:
                item_venda.id_venda = id_venda
                self.registrar_item_venda(item_venda)

                # Baixa de estoque
                self.estoque_service.registrar_movimento(
                    MovimentoEstoque(
                        id_item=item_venda.id_item,
                        quantidade=item_venda.quantidade,
                        tipo_movimento="Saida",
                        origem_recurso="Venda",
                        id_usuario=int(venda_cabecalho.responsavel),
                        id_evento=venda_cabecalho.id_evento,
                    )
                )

            # 3. Commit geral
            self.db.conn.commit()
            return id_venda

        except Exception as e:
            self.db.conn.rollback()
            print(f"(Alerta: Transação de venda falhou. Rollback executado.) Erro: {e}")
            return None

    # -----------------------------------------------------------
    # Consultas
    # -----------------------------------------------------------

    def buscar_vendas(self) -> List[Venda]:
        """Busca todas as vendas."""
        query = "SELECT id, id_pessoa, data_venda, responsavel, id_evento, id_movimento_caixa FROM vendas"
        columns, results = self.db.execute_query(query, fetch_all=True)
        if results:
            return [Venda(**dict(zip(columns, row))) for row in results]
        return []
