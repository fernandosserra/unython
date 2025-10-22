from typing import List, Optional
from src.utils.database_manager import DatabaseManager
from src.utils.models import Venda, ItemVenda, Item

class VendaService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def registrar_venda(self, venda: Venda) -> Optional[int]:
        """Registra uma nova venda e retorna o ID (O Protocolo de Inserção Genial)."""
        query = "INSERT INTO vendas (id_pessoa, data_venda, responsavel) VALUES (?, ?, ?)"
        values = (venda.id_pessoa, venda.data_venda, venda.responsavel)
        # Retorna o lastrowid!
        return self.db.execute_query(query, values, commit=True)
    
    def registrar_item_venda(self, item_venda: ItemVenda) -> Optional[int]:
        """Registra um item em uma venda e retorna o ID (O Protocolo de Inserção Genial)."""
        query = "INSERT INTO itens_venda (id_venda, id_item, quantidade, valor_unitario) VALUES (?, ?, ?, ?)"
        values = (item_venda.id_venda, item_venda.id_item, item_venda.quantidade, item_venda.valor_unitario)
        # Retorna o lastrowid!
        return self.db.execute_query(query, values, commit=True)
    
    def buscar_vendas(self) -> List[Venda]:
        """Busca todas as vendas e as converte em objetos Venda."""
        query = "SELECT id, id_pessoa, data_venda, responsavel FROM vendas"
        columns, results = self.db.execute_query(query, fetch_all=True)
        if results:
            return [Venda(**dict(zip(columns, row))) for row in results]
        
    def registrar_venda_completa(self, venda_cabecalho: Venda, itens_detalhe: List[ItemVenda]) -> Optional[int]:
        """
        Orquestra a inserção de Cabeçalho (Venda) e Detalhes (ItemVenda) em uma ÚNICA transação lógica.
        """
        try:
            # 1. Registra a Venda Principal (Cabeçalho)
            # Chame o método auxiliar sem commit!
            id_venda = self.registrar_venda(venda_cabecalho)
            
            if not id_venda:
                raise Exception("Falha ao criar o cabeçalho da Venda.")

            # 2. Registra todos os Itens (Detalhes)
            for item_venda in itens_detalhe:
                item_venda.id_venda = id_venda # Liga o detalhe ao cabeçalho recém-criado
                
                # Chame o método auxiliar sem commit!
                self.registrar_item_venda(item_venda)

            # 3. Se tudo deu certo, comita Apenas Aqui (Atomicidade Garantida!)
            self.db.conn.commit()
            return id_venda

        except Exception as e:
            # Em caso de qualquer falha (SQL ou Python), faz o rollback e reverte tudo.
            self.db.conn.rollback()
            print(f" (Alerta Washu: Transação de Venda falhou. Rollback executado.) Erro: {e}")
            return None