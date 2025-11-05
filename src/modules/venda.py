# src/modules/venda.py
from typing import List, Optional
from src.utils.database_manager import DatabaseManager
from src.utils.models import Venda, ItemVenda, Item , MovimentoEstoque
from src.modules.estoque import EstoqueService
from datetime import datetime # Incluído para clareza, caso precise de data

class VendaService:
    """
    Coordena as transações de venda, garantindo a atomicidade (Tudo ou Nada) 
    e a ligação correta entre Vendas, Itens e Eventos.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def registrar_venda(self, venda: Venda) -> Optional[int]:
        """
        Registra o cabeçalho de uma nova venda. Não comita, mantendo a transação aberta.
        Retorna o ID (int) se o INSERT for bem-sucedido, senão retorna False.
        """
        # Query atualizada para incluir a chave estrangeira id_evento
        query = "INSERT INTO vendas (id_pessoa, data_venda, responsavel, id_evento) VALUES (%s, %s, %s, %s) RETURNING id"
        
        # Valores alinhados com a query e o Model
        values = (venda.id_pessoa, venda.data_venda, venda.responsavel, venda.id_evento)
        
        # CRÍTICO: commit=False. O DatabaseManager deve retornar o lastrowid (int) ou False (em caso de erro).
        id_retornado = self.db.execute_query(query, values, commit=False)
        
        # Garante que apenas um ID inteiro e positivo seja retornado.
        if isinstance(id_retornado, int) and id_retornado > 0:
            return id_retornado
        
        # Retorna False se a execução falhou ou o ID não foi capturado (embora a falha deva ser tratada pelo try/except)
        return None
    
    
    def registrar_item_venda(self, item_venda: ItemVenda) -> Optional[int]:
        """
        Registra o detalhe (item) de uma venda. Não comita.
        """
        query = "INSERT INTO itens_venda (id_venda, id_item, quantidade, valor_unitario) VALUES (%s, %s, %s, %s) RETURNING id"
        values = (item_venda.id_venda, item_venda.id_item, item_venda.quantidade, item_venda.valor_unitario)
        
        # CRÍTICO: commit=False
        return self.db.execute_query(query, values, commit=False) # Retorna ID (int) ou False
    
    
    def buscar_vendas(self) -> List[Venda]:
        """
        Busca todas as vendas e as converte em objetos Venda.
        Query ajustada para incluir id_evento.
        """
        query = "SELECT id, id_pessoa, data_venda, responsavel, id_evento FROM vendas"
        columns, results = self.db.execute_query(query, fetch_all=True)
        
        if results:
            return [Venda(**dict(zip(columns, row))) for row in results]
        return []
        
        
    def registrar_venda_completa(self, venda_cabecalho: Venda, itens_detalhe: List[ItemVenda]) -> Optional[int]:
        id_venda = None
        
        # CRÍTICO: Instanciar o EstoqueService aqui dentro para usar o cálculo de saldo
        estoque_service = EstoqueService(self.db) 
        
        try:
            # 0. PROTOCOLO DE CONDIÇÃO: CHECAGEM DE ESTOQUE
            for item_venda in itens_detalhe:
                saldo = estoque_service.calcular_saldo_item(item_venda.id_item)
                if saldo < item_venda.quantidade:
                    raise Exception(f"Estoque Insuficiente! Item ID {item_venda.id_item} (Necessário: {item_venda.quantidade}, Saldo: {saldo})")

            # 1. Registra o Cabeçalho (Obtém o ID)
            id_venda = self.registrar_venda(venda_cabecalho)
            
            if not isinstance(id_venda, int) or id_venda <= 0:
                raise Exception("Falha ao criar o cabeçalho da Venda.")

            # 2. Registra Detalhes E SAÍDA DE ESTOQUE
            for item_venda in itens_detalhe:
                item_venda.id_venda = id_venda
                
                # A. REGISTRA O DETALHE DA VENDA (Para relatório)
                self.registrar_item_venda(item_venda) 
                
                # B. REGISTRA A SAÍDA DE ESTOQUE (Para gestão física)
                estoque_service.registrar_movimento(
                    MovimentoEstoque(
                        id_item=item_venda.id_item, 
                        quantidade=item_venda.quantidade, 
                        tipo_movimento='Saída', 
                        origem_recurso='Venda em Feirinha', 
                        id_usuario=venda_cabecalho.responsavel, # Assumindo que responsavel é o id do usuário que vendeu
                        id_evento=venda_cabecalho.id_evento
                    )
                )

            # 3. Se TUDO deu certo, comita a transação inteira
            self.db.conn.commit()
            return id_venda

        except Exception as e:
            self.db.conn.rollback()
            # O alerta agora é mais informativo!
            print(f" (Alerta Washu: Transação de Venda Falhou. Rollback executado.) Erro: {e}")
            return None