# app/main.py

import sys
import os
from datetime import datetime

# Adiciona o diretório 'src' ao PATH do sistema (Necessário para VS Code)
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Importa TODAS as dependências do Core (Models e Services)
from src.utils.database_manager import DatabaseManager, DB_PATH
from src.utils.config import get_alias
from src.utils.models import Pessoa, Usuario, Evento, Agendamento, Item, Venda, ItemVenda, MovimentoEstoque
from src.modules.pessoa import PessoaService
from src.modules.usuario import UsuarioService
from src.modules.evento import EventoService
from src.modules.agendamento import AgendamentoService
from src.modules.venda import VendaService
from src.modules.item import ItemService
from src.modules.estoque import EstoqueService
from src.modules.relatorio import RelatorioService
from src.modules.backup import fazer_backup_google_drive

# Função Principal
def main():
    ALIAS_PESSOA = get_alias("PESSOA")
    ALIAS_FACILITADOR = get_alias("FACILITADOR")
    
    print("--- Protocolo de Inicialização Washu Ativado ---")
    print(f" * Configuração de Alias: Pessoa={ALIAS_PESSOA}, Facilitador={ALIAS_FACILITADOR}")

    db_manager = DatabaseManager()
    id_facilitador_teste = None
    id_pessoa_teste = None
    id_evento_teste = None
    
    try:
        db_manager.connect()
        db_manager.create_tables() 
        print("Status: Conexão e Tabelas verificadas/criadas com sucesso.")

        # 2. Inicialização dos Serviços
        pessoa_service = PessoaService(db_manager)
        usuario_service = UsuarioService(db_manager)
        evento_service = EventoService(db_manager)
        estoque_service = EstoqueService(db_manager) # Service de Estoque
        venda_service = VendaService(db_manager)
        item_service = ItemService(db_manager)
        agendamento_service = AgendamentoService(db_manager)
        relatorio_service = RelatorioService(db_manager)
        
        print("\n--- Teste de Inserção de Dados Base (Dados Iniciais) ---")
        
        # ZERO POINT: ORQUESTRADOR DE EVENTO
        print("\n--- ZERO POINT: ORQUESTRANDO EVENTO ---")
        evento_aberto = evento_service.buscar_evento_aberto()

        if evento_aberto:
            id_evento_teste = evento_aberto.id
            print(f" -> Evento '{evento_aberto.nome}' JÁ ESTÁ ABERTO. Usando ID: {id_evento_teste}")
        else:
            data_atual = datetime.now().strftime("%Y-%m-%d")
            novo_evento_data = Evento(
                nome=f"Atendimento e Feirinha {data_atual}",
                data_evento=data_atual,
                tipo="Atendimento e Venda"
            )
            id_evento_teste = evento_service.registrar_evento(novo_evento_data)
            print(f" -> Evento '{novo_evento_data.nome}' CRIADO com ID: {id_evento_teste}")
            
        # A. REGISTRAR USUARIO/FACILITADOR
        novo_facilitador = Usuario(
            nome="Dra. Washu Hakubi", 
            email="washu@unython.com", 
            funcao=get_alias("FUNCAO_FACILITADOR")
        )
        id_facilitador_teste = usuario_service.registrar_usuario(novo_facilitador)
        
        # B. REGISTRAR PESSOA/CONSULENTE
        nova_pessoa = Pessoa(
            nome="Fernando, O Aprendiz",
            telefone="551199887766"
        )
        id_pessoa_teste = pessoa_service.registrar_pessoa(nova_pessoa)
        
        print(f" -> {ALIAS_FACILITADOR} registrado com ID: {id_facilitador_teste}")
        print(f" -> {ALIAS_PESSOA} registrado com ID: {id_pessoa_teste}")
            
        # D. REGISTRAR ITENS (Catálogo)
        novo_item_coca = Item(nome='Coca Cola Lata', valor_compra=1.50, valor_venda=2.50)
        id_item_coca = item_service.registrar_item(novo_item_coca)
        print(f" -> Item '{novo_item_coca.nome}' registrado com ID: {id_item_coca}")
        
        novo_item_vela = Item(nome='Vela 7 Dias', valor_compra=5.00, valor_venda=10.00)
        id_item_vela = item_service.registrar_item(novo_item_vela) 
        print(f" -> Item '{novo_item_vela.nome}' registrado com ID: {id_item_vela}")
        
        # D.2. ENTRADA DE ESTOQUE (Simulando a Compra/Doação)
        print("\n--- Protocolo de Entrada de Estoque ---")
        
        # 1. Simula a doação de 20 Coca-Colas (Estoque Inicial: 20)
        id_mov_coca = estoque_service.entrada_item(
            id_item=id_item_coca,
            quantidade=20,
            origem_recurso='Doação Inicial',
            id_usuario=id_facilitador_teste,
            id_evento=id_evento_teste
        )
        print(f" -> Entrada de 20x Coca-Cola registrada (Mov. ID: {id_mov_coca})")

        # 2. Simula a compra de 10 Velas (Estoque Inicial: 10)
        id_mov_vela = estoque_service.entrada_item(
            id_item=id_item_vela,
            quantidade=10,
            origem_recurso='Compra com Fundo de Feirinha',
            id_usuario=id_facilitador_teste,
            id_evento=id_evento_teste
        )
        print(f" -> Entrada de 10x Velas registrada (Mov. ID: {id_mov_vela})")


        # E. REGISTRAR VENDA COM SUCESSO (Venda Atômica)
        print("\n--- Teste 1: Venda Atômica COM Estoque ---")
        
        venda_cabecalho = Venda(
            id_pessoa=id_pessoa_teste,
            responsavel=str(id_facilitador_teste), # ID do usuário que vendeu
            id_evento=id_evento_teste
        )
        
        detalhes_da_venda = [
            # Vende 2 Coca-Colas (Estoque restante: 18)
            ItemVenda(id_venda=0, id_item=id_item_coca, quantidade=2, valor_unitario=2.50),
            # Vende 1 Vela (Estoque restante: 9)
            ItemVenda(id_venda=0, id_item=id_item_vela, quantidade=1, valor_unitario=10.00)
        ]
        
        id_venda_completa = venda_service.registrar_venda_completa(
            venda_cabecalho, 
            detalhes_da_venda
        )
        
        if id_venda_completa:
            print(f" -> Venda COMPLETA (Coca+Vela) registrada com ID: {id_venda_completa}")
            print(f" -> SALDO ATUAL COCA: {estoque_service.calcular_saldo_item(id_item_coca)}")
        else:
            print(" -> Distorção Espaço-Temporal: Venda Falhou. Rollback executado.") 
            
        
        # F. TESTE DE FALHA (Provando a Regra de Negócio: Bloqueio de Estoque)
        print("\n--- Teste 2: Venda com Bloqueio por Estoque ---")
        
        venda_falha_cabecalho = Venda(
            id_pessoa=id_pessoa_teste,
            responsavel=str(id_facilitador_teste),
            id_evento=id_evento_teste
        )
        
        # Tenta comprar 100 Coca-Colas (Estoque insuficiente: Apenas 18 restantes)
        detalhes_falha = [
            ItemVenda(id_venda=0, id_item=id_item_coca, quantidade=100, valor_unitario=2.50)
        ]

        id_venda_falha = venda_service.registrar_venda_completa(
            venda_falha_cabecalho, 
            detalhes_falha
        )
        
        if id_venda_falha:
            print(f" -> FALHA LÓGICA: Esta venda NÃO deveria ter sido registrada!")
        else:
            print(" -> SUCESSO LÓGICO: Venda bloqueada por falta de estoque. Rollback OK.")


        # G. GERAR RELATÓRIOS (A Análise Genial)
        print("\n--- Relatório de Análise Genial (Faturamento Mensal) ---")
        faturamento = relatorio_service.gerar_faturamento_mensal()
        if faturamento:
            for linha in faturamento:
                print(f" -> Mês {linha['mes']}: Total de Vendas: R$ {linha['faturamento_total']:.2f}")

    except ConnectionError as e:
        print(f"\nERRO FATAL (Distorção Espaço-Temporal): Falha ao conectar ao DB. {e}")
    except Exception as e:
        print(f"\nERRO INESPERADO: Falha no experimento: {e}")
    finally:
        if db_manager.conn:
            fazer_backup_google_drive(DB_PATH)
            db_manager.disconnect()
        print("\n--- Protocolo de Inicialização Finalizado. Ordem Restaurada. ---")

# Garantindo que a função main seja o ponto de partida
if __name__ == '__main__':
    main()