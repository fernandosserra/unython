# src/utils/database_manager.py (NOVO - Adaptado para PostgreSQL com SECRETS)

import psycopg2
import os
import toml # IMPORT CRÍTICO
from typing import Optional, Any, List, Tuple

# --- LÓGICA DE CARREGAMENTO DE SECRETS ---

# Resolve o caminho para a raiz do projeto (como fizemos no backup.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
SECRETS_PATH = os.path.join(PROJECT_ROOT, 'config', 'secrets.toml')

def load_db_config():
    """Carrega as configurações do banco de dados do arquivo secrets.toml."""
    if not os.path.exists(SECRETS_PATH):
        raise FileNotFoundError(
            f"ERRO DE SEGURANÇA: Arquivo de segredos não encontrado em {SECRETS_PATH}. "
            "Crie o 'secrets.toml' na pasta 'app/' e preencha as credenciais do PostgreSQL."
        )
    try:
        config = toml.load(SECRETS_PATH)
        db_config = config.get('database', {})
        if db_config.get('type') != 'postgres':
             raise ValueError("O tipo de banco de dados no secrets.toml não é 'postgres'.")
        return db_config
    except Exception as e:
        raise Exception(f"Erro ao ler secrets.toml: {e}")


# Carregando as configurações uma vez
DB_CONFIG = load_db_config()

# --- CLASSE DatabaseManager USANDO AS CONFIGURAÇÕES ---

class DatabaseManager:
    """
    Controla a conexão e as operações básicas de persistência no PostgreSQL.
    """
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        
        # Atribuindo variáveis do arquivo TOML
        self.DB_HOST = DB_CONFIG.get("host")
        self.DB_NAME = DB_CONFIG.get("dbname")
        self.DB_USER = DB_CONFIG.get("user")
        self.DB_PASS = DB_CONFIG.get("password")
        self.DB_PORT = DB_CONFIG.get("port")

    def connect(self):
        """Estabelece a conexão com o PostgreSQL."""
        try:
            self.conn = psycopg2.connect(
                host=self.DB_HOST,
                database=self.DB_NAME,
                user=self.DB_USER,
                password=self.DB_PASS,
                port=self.DB_PORT
            )
            self.cursor = self.conn.cursor()
            print(f"Conexão ao DB PostgreSQL '{self.DB_NAME}' estabelecida com sucesso pela Washu!")
        except Exception as e:
            # Captura exceções do psycopg2 de forma mais genérica
            print(f"ERRO FATAL: Anomalia ao conectar ao PostgreSQL. Verifique o secrets.toml. Erro: {e}")
            raise
    
    def execute_query(self, query: str, params: Optional[Tuple[Any, ...]] = None, fetch_one: bool = False, fetch_all: bool = False, commit: bool = False) -> Any:
        
        # OBTÉM O TIPO DE DB PARA DECISÃO
        db_type = DB_CONFIG.get('type', 'postgres')  
        
        if not self.conn:
            raise ConnectionError("A conexão com o PostgreSQL não foi estabelecida. Chame a Washu!")

        try:
            # 1. Pré-processamento: Adapta INSERT/UPDATE/DELETE para RETORNAR o ID
            is_insert_update_delete = query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE'))
            last_id = None
            
            # 2. Execução da Query
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            # 3. Tratamento de IDs (CRÍTICO para PostgreSQL)
            # A forma de obter o ID após um INSERT no Postgres é usar 'RETURNING id' no SQL.
            # Se o último comando foi um INSERT e o cursor tem dados, ele retornou o ID.
            if is_insert_update_delete and self.cursor.description:
                # Assume que o INSERT/UPDATE usou 'RETURNING id' e obtém o valor.
                last_id = self.cursor.fetchone()[0]
            
            # 4. Commit
            if commit:
                self.conn.commit()
                # Se comitou e foi um INSERT/UPDATE, retorna o ID capturado.
                if last_id is not None:
                    return last_id
                
            # 5. Tratamento de SELECT
            if fetch_one or fetch_all:
                if self.cursor.description:
                    columns = [desc[0] for desc in self.cursor.description]
                    data = self.cursor.fetchone() if fetch_one else self.cursor.fetchall()
                    return columns, data
                return None, None 

            # 6. Retorno final para INSERT/UPDATE/DELETE SEM commit
            if last_id is not None:
                return last_id
            
            return True # Retorno padrão de sucesso
        
        except psycopg2.Error as e:
            print(f"Distorção Espaço-Temporal SQL detectada (Postgres): {e}")
            self.conn.rollback() # Reverte a operação
            return False
        except Exception as e:
            # Captura outros erros, garantindo o rollback
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Erro inesperado durante a execução da query: {e}")

    def create_tables(self):
        """
        Cria todas as tabelas, adaptando a sintaxe para PostgreSQL.
        """
        
        # Sequência CRÍTICA: Se o banco de dados for novo, você precisa de um CREATE SCHEMA,
        # mas por simplicidade, assumimos que o banco 'unython_db' já existe no servidor.
        
        # 1. Tabela de USUARIOS (Facilitadores)
        usuarios_table_query = """
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE,
            funcao VARCHAR(100),
            role VARCHAR(50) DEFAULT 'Vendedor',      
            status VARCHAR(50) DEFAULT 'Ativo',
            hashed_password VARCHAR(128)
        );
        """

        # 2. Tabela de PESSOAS (Consulentes)
        pessoas_table_query = """
        CREATE TABLE IF NOT EXISTS pessoas (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            telefone VARCHAR(50),
            data_cadastro DATE NOT NULL DEFAULT NOW()
        );
        """
        
        # 3. Tabela de EVENTOS (Contexto Fiscal)
        eventos_tabel_query = """
        CREATE TABLE IF NOT EXISTS eventos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            data_evento DATE NOT NULL,
            tipo VARCHAR(100),
            status VARCHAR(50) DEFAULT 'Aberto'
        );
        """
        
        # 4. Tabela de AGENDAMENTOS (Relacionamentos)
        agendamentos_table_query = """
        CREATE TABLE IF NOT EXISTS agendamentos (
            id SERIAL PRIMARY KEY,
            id_pessoa INTEGER NOT NULL,
            id_facilitador INTEGER,
            data_hora TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            tipo_servico VARCHAR(100),
            status VARCHAR(50) DEFAULT 'Agendado',
            id_evento INTEGER NOT NULL,
            compareceu VARCHAR(50) DEFAULT 'Pendente',
            
            FOREIGN KEY (id_pessoa) REFERENCES pessoas(id),
            FOREIGN KEY (id_facilitador) REFERENCES usuarios(id),
            FOREIGN KEY (id_evento) REFERENCES eventos(id)
        );
        """
        
        # 5. Tabela de CATEGORIAS (Nova Tabela)
        categorias_table_query = """
        CREATE TABLE IF NOT EXISTS categorias (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL UNIQUE,
            descricao TEXT,
            status VARCHAR(50) DEFAULT 'Ativo'
        );
        """
        self.execute_query(categorias_table_query, commit=True)
        
        # 6. Tabela de ITENS (Catálogo)
        itens_table_query = """
        CREATE TABLE IF NOT EXISTS itens (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL UNIQUE,
            valor_compra NUMERIC(10, 2) NOT NULL,
            valor_venda NUMERIC(10, 2) NOT NULL,
            status VARCHAR(50) DEFAULT 'Ativo',
            id_categoria INTEGER,
            
            FOREIGN KEY (id_categoria) REFERENCES categorias(id)
        );
        """
        
        # 7. Tabela de MOVIMENTO ESTOQUE (Rastreamento)
        estoque_table_query = """
        CREATE TABLE IF NOT EXISTS estoque (
            id SERIAL PRIMARY KEY,
            id_item INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            tipo_movimento VARCHAR(50) NOT NULL,
            data_movimento DATE NOT NULL DEFAULT NOW(),
            origem_recurso VARCHAR(100) DEFAULT 'Doação',
            id_usuario INTEGER,
            id_evento INTEGER,
            
            FOREIGN KEY (id_item) REFERENCES itens(id),
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
            FOREIGN KEY (id_evento) REFERENCES eventos(id)
        );
        """ 
        
        # 8. Tabela de VENDAS (Cabeçalho)
        vendas_table_query = """
        CREATE TABLE IF NOT EXISTS vendas (
            id SERIAL PRIMARY KEY,
            id_pessoa INTEGER, 
            data_venda DATE NOT NULL DEFAULT NOW(),
            id_evento INTEGER NOT NULL, 
            responsavel VARCHAR(255),
            
            FOREIGN KEY (id_pessoa) REFERENCES pessoas(id),
            FOREIGN KEY (id_evento) REFERENCES eventos(id)
        );
        """
        
        # 9. Tabela de LIGAÇÃO (ITENS_VENDA)
        itens_venda_table_query = """
        CREATE TABLE IF NOT EXISTS itens_venda (
            id SERIAL PRIMARY KEY,
            id_venda INTEGER NOT NULL,
            id_item INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            valor_unitario NUMERIC(10, 2) NOT NULL,
            
            FOREIGN KEY (id_venda) REFERENCES vendas(id),
            FOREIGN KEY (id_item) REFERENCES itens(id)
        );
        """
        
        # 10. Tabela de MOVIMENTOS FINANCEIROS (Fluxo de Caixa)
        movimentos_financeiros_table_query = """
        CREATE TABLE IF NOT EXISTS movimentos_financeiros (
            id SERIAL PRIMARY KEY,
            data_registro TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            id_usuario INTEGER NOT NULL,
            tipo_movimento VARCHAR(50) NOT NULL CHECK(tipo_movimento IN ('Receita', 'Despesa')),
            valor NUMERIC(10, 2) NOT NULL,
            descricao TEXT,
            categoria VARCHAR(100),
            id_evento INTEGER,
            status VARCHAR(50) NOT NULL DEFAULT 'Ativo',
            
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
            FOREIGN KEY (id_evento) REFERENCES eventos(id)
        );
        """

        # Execução das consultas
        queries = [
            usuarios_table_query, pessoas_table_query, eventos_tabel_query, 
            agendamentos_table_query, itens_table_query, estoque_table_query, 
            vendas_table_query, itens_venda_table_query, movimentos_financeiros_table_query
        ]
        
        # Executa query por query com commit imediato (para DDL)
        for query in queries:
            self.execute_query(query, commit=True)
            
        print("Estruturas de Dados Primárias criadas no PostgreSQL. A Ordem está completa!")      
        
    def disconnect(self):
        """Fecha a conexão."""
        if self.conn:
            self.conn.close()
            print("Conexão ao DB PostgreSQL fechada. Ordem restaurada.")