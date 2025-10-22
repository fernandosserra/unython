import sqlite3
import os
from datetime import datetime

# Importa as configurações para obter o nome do DB (Genialidade Modular!)
try:
    from src.utils.config import DB_NAME
except ImportError:
    # Fallback caso o config.py ainda não exista
    DB_NAME = "unython.db" 


# Definindo o caminho do banco de dados (A Sintaxe Universal de Acesso)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Sobe dois níveis (de src/utils para o root do projeto) e desce para 'data'
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(BASE_DIR)), 
    'data', 
    DB_NAME
)

class DatabaseManager:
    """
    Controla a conexão e as operações básicas de persistência de dados.
    Este é o Repositório, a Camada de Acesso a Dados, isolada e perfeita.
    """

    def __init__(self):
        # Garante que o diretório 'data' exista antes de tentar criar o DB
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.db_path = DB_PATH
        self.conn = None
        self.cursor = None

    def connect(self):
        """Estabelece a conexão com o Universo de Dados (SQLite) e ativa Foreign Keys."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            # ATENÇÃO! Ativa as chaves estrangeiras, ESSENCIAL para integridade!
            self.cursor.execute("PRAGMA foreign_keys = ON;") 
            # print(f"Conexão ao DB '{self.db_path}' estabelecida com sucesso pela Washu!")
        except sqlite3.Error as e:
            # Que adorável anomalia!
            print(f"Anomalia na Matriz Lógica ao conectar: {e}")
            raise

    def disconnect(self):
        """Fecha a conexão para evitar Distorções Espaço-Temporais."""
        if self.conn:
            self.conn.close()
            # print("Conexão ao DB fechada. Ordem restaurada.")

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False, commit=False):
        """
        Executa qualquer comando SQL. O Centro de Comando Genial!
        Retorna (colunas, dados) para consultas SELECT, ou True/False para comandos.
        """
        if not self.conn:
            raise ConnectionError("A conexão não foi estabelecida. Chame a Washu!")

        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            if commit:
                self.conn.commit()
                # ESTE é o retorno obrigatório para INSERT/UPDATE/DELETE que usam autoincrement
                return self.cursor.lastrowid # <--- DEVE RETORNAR O ID INTEIRO

            if fetch_one or fetch_all:
                if self.cursor.description:
                    columns = [desc[0] for desc in self.cursor.description]
                    data = self.cursor.fetchone() if fetch_one else self.cursor.fetchall()
                    return columns, data
                return None, None # Se não houver descrição, retorna vazio

            return True # Para comandos como INSERT, UPDATE, DELETE
        
        except sqlite3.Error as e:
            print(f"Distorção Espaço-Temporal SQL detectada: {e}")
            self.conn.rollback() # Reverte a operação para manter a integridade universal
            return False

    def create_tables(self):
        """
        Cria as tabelas iniciais. Definindo a Sintaxe Universal do seu sistema.
        """
        
        # O Protocolo de Limpeza: Garantindo que a estrutura esteja sempre correta
        # Use APENAS para desenvolvimento inicial!
        # self.execute_query("DROP TABLE IF EXISTS agendamentos;", commit=True)
        # self.execute_query("DROP TABLE IF EXISTS vendas;", commit=True)
        # self.execute_query("DROP TABLE IF EXISTS pessoas;", commit=True)
        # self.execute_query("DROP TABLE IF EXISTS usuarios;", commit=True)


        # 1. Tabela de USUARIOS (Facilitadores, Administradores, etc.)
        usuarios_table_query = """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE,
            funcao TEXT,       -- Ex: 'Facilitador', 'Administrador', 'Voluntário'
            status TEXT DEFAULT 'Ativo'
        );
        """

        # 2. Tabela de PESSOAS (Consulentes, Assistidos, Clientes da Feirinha)
        pessoas_table_query = """
        CREATE TABLE IF NOT EXISTS pessoas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            data_cadastro TEXT NOT NULL DEFAULT (date('now'))
        );
        """
        
        # 3. Tabela de AGENDAMENTOS (Com Relacionamentos Dimensionais)
        agendamentos_table_query = """
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_pessoa INTEGER NOT NULL,
            id_facilitador INTEGER,
            data_hora TEXT NOT NULL,
            tipo_servico TEXT,
            status TEXT DEFAULT 'Agendado',
            -- Definindo os Relacionamentos Dimensionais (Foreign Keys)
            FOREIGN KEY (id_pessoa) REFERENCES pessoas(id),
            FOREIGN KEY (id_facilitador) REFERENCES usuarios(id)
        );
        """
        
        # 4. Tabela de Itens
        itens_table_query = """
        CREATE TABLE IF NOT EXISTS itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            valor_compra REAL NOT NULL,
            valor_venda REAL NOT NULL,
            status TEXT DEFAULT 'Ativo'  -- <--- CAMPO ADICIONADO!
        );
        """
        
        # 5. Tabela de VENDAS (A Transação - O cabeçalho)
        vendas_table_query = """
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_pessoa INTEGER,                      -- Quem comprou
            data_venda TEXT NOT NULL DEFAULT (date('now')),
            responsavel TEXT,                       -- Quem registrou (pode ser o nome de um Usuario)
            FOREIGN KEY (id_pessoa) REFERENCES pessoas(id)
        );
        """
        
        # 6. Tabela de LIGAÇÃO (ITENS_VENDA - O detalhe da venda)
        itens_venda_table_query = """
        CREATE TABLE IF NOT EXISTS itens_venda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_venda INTEGER NOT NULL,
            id_item INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            valor_unitario REAL NOT NULL,
            FOREIGN KEY (id_venda) REFERENCES vendas(id),
            FOREIGN KEY (id_item) REFERENCES itens(id)
        );
        """

        # Execução das consultas para estabelecer a ordem
        self.execute_query(usuarios_table_query, commit=True)
        self.execute_query(pessoas_table_query, commit=True)
        self.execute_query(agendamentos_table_query, commit=True)
        self.execute_query(itens_table_query, commit=True)
        self.execute_query(vendas_table_query, commit=True)
        self.execute_query(itens_venda_table_query, commit=True)
        
        # print("Estruturas de Dados Primárias criadas. A Washu estruturou seu universo!")