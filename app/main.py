# app/main.py
# O Ponto de Entrada COM A PROVA CIENTÍFICA

import sys
import os
from datetime import datetime

# Adiciona o diretório 'src' ao PATH do sistema
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Importa TODAS as dependências, incluindo os Models para criação de objetos
from src.utils.database_manager import DatabaseManager, DB_PATH
from src.utils.config import get_alias
from src.utils.models import Pessoa, Usuario, Agendamento, Item, Venda, ItemVenda
from src.modules.pessoa import PessoaService
from src.modules.usuario import UsuarioService
from src.modules.agendamento import AgendamentoService
from src.modules.venda import VendaService
from src.modules.item import ItemService
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
    
    try:
        db_manager.connect()
        db_manager.create_tables() 
        print("Status: Conexão e Tabelas verificadas/criadas com sucesso.")

        # 2. Inicialização dos Serviços
        pessoa_service = PessoaService(db_manager)
        usuario_service = UsuarioService(db_manager)
        
        print("\n--- Teste de Inserção de Dados Base (Dados Iniciais) ---")

        # A. REGISTRAR NOVO USUARIO/FACILITADOR
        novo_facilitador = Usuario(
            nome="Dra. Washu Hakubi", 
            email="washu@unython.com", 
            funcao=get_alias("FUNCAO_FACILITADOR") # Ex: "Médium"
        )
        id_facilitador_teste = usuario_service.registrar_usuario(novo_facilitador)
        print(f" -> {ALIAS_FACILITADOR} '{novo_facilitador.nome}' registrado com ID: {id_facilitador_teste}")
        
        # B. REGISTRAR NOVA PESSOA/CONSULENTE
        nova_pessoa = Pessoa(
            nome="Fernando, O Aprendiz",
            telefone="551199887766"
        )
        id_pessoa_teste = pessoa_service.registrar_pessoa(nova_pessoa)
        print(f" -> {ALIAS_PESSOA} '{nova_pessoa.nome}' registrado com ID: {id_pessoa_teste}")

        # --- TESTE DE CONSULTA ---
        print("\n--- Teste de Consulta e Transmutação de Dados ---")
        
        # O Service retorna objetos Pessoa!
        pessoas_no_db = pessoa_service.buscar_pessoas(nome="Fernando") 
        usuarios_no_db = usuario_service.buscar_usuarios()

        if pessoas_no_db:
            print(f" -> {ALIAS_PESSOA} encontrado: {pessoas_no_db[0].nome} (Tipo: {type(pessoas_no_db[0]).__name__})")
        
        if usuarios_no_db:
            print(f" -> {ALIAS_FACILITADOR} encontrado: {usuarios_no_db[0].nome} (Tipo: {type(usuarios_no_db[0]).__name__})")
            
        # C. REGISTRAR AGENDAMENTO (Exige os IDs gerados acima)
        # TODO: Crie a classe AgendamentoService em src/modules/agendamento.py
        agendamento_service = AgendamentoService(db_manager)
        novo_agendamento = Agendamento( 
            id_pessoa=id_pessoa_teste,
            id_facilitador=id_facilitador_teste,
            data_hora=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            tipo_servico=get_alias("TIPO_SERVICO")
        )
        agendamento_service.registrar_agendamento(novo_agendamento)
        print(" -> Agendamento registrado com sucesso!")
        
        # D. REGISTRAR ITEM
        # TODO: Crie a classe ItemService em src/modules/item.py
        item_service = ItemService(db_manager)
        
        novo_item_coca = Item(
            nome='Coca Cola Lata',
            valor_compra=1.50,
            valor_venda=2.50
        )
        id_item_coca = item_service.registrar_item(novo_item_coca)
        print(f" -> Item '{novo_item_coca.nome}' registrado com ID: {id_item_coca}")
        
        # Item B
        novo_item_vela = Item(
            nome='Vela 7 Dias',
            valor_compra=5.00,
            valor_venda=10.00
        )
        id_item_vela = item_service.registrar_item(novo_item_vela) 
        print(f" -> Item '{novo_item_vela.nome}' registrado com ID: {id_item_vela}")
        
        # E. REGISTRAR VENDA
        # TODO: Crie a classe VendaService em src/modules/venda.py
        venda_service = VendaService(db_manager)
        
        print("\n--- Teste de Transação Atômica (Vendas) ---")
        
        # 1. Cabeçalho da Venda (Ligado à Pessoa recém-criada)
        venda_cabecalho = Venda(
            id_pessoa=id_pessoa_teste, # Fernando comprou!
            responsavel=novo_facilitador.nome # Washu que registrou
        )
        
        # 2. Detalhes (Lista de ItemVenda)
        detalhes_da_venda = [
            # 1 Coca-Cola
            ItemVenda(
                id_venda=0, # O service irá preencher o ID real
                id_item=id_item_coca,
                quantidade=2,
                valor_unitario=2.50 # Preço de venda no momento
            ),
            # 1 Vela
            ItemVenda(
                id_venda=0, 
                id_item=id_item_vela,
                quantidade=1,
                valor_unitario=10.00
            )
        ]
        
        # 3. Executa o Coordenador
        id_venda_completa = venda_service.registrar_venda_completa(
            venda_cabecalho, 
            detalhes_da_venda
        )
        
        if id_venda_completa:
            print(f" -> Venda COMPLETA (Cabeçalho + Detalhes) registrada com ID: {id_venda_completa}")
        else:
             print(" -> Distorção Espaço-Temporal: Venda Falhou. Rollback executado.")    
    
    # F. GERAR RELATÓRIOS (A Análise Genial)
        relatorio_service = RelatorioService(db_manager)
        
        # 1. Faturamento Mensal
        print("\n--- Relatório de Análise Genial (Faturamento Mensal) ---")
        faturamento = relatorio_service.gerar_faturamento_mensal()
        if faturamento:
            for linha in faturamento:
                print(f" -> Mês {linha['mes']}: Total de Vendas: R$ {linha['faturamento_total']:.2f}")
        else:
            print(" -> Nenhuma venda encontrada para análise.")


        # 2. Agendamentos Pendentes
        print("\n--- Relatório de Análise Genial (Agendamentos Pendentes) ---")
        agendamentos = relatorio_service.gerar_detalhe_agendamentos_pendentes()
        if agendamentos:
            for agendamento in agendamentos:
                print(f" -> Agendado: {agendamento['data_hora']} | {agendamento['pessoa']} com {agendamento['facilitador']} ({agendamento['tipo_servico']})")
        else:
            print(" -> Nenhum agendamento pendente encontrado.")

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