# Unython - (C) 2025 siegrfried@gmail.com
# Este programa e software livre: voce pode redistribui-lo e/ou modifica-lo
# sob os termos da GNU General Public License como publicada pela Free Software Foundation,
# na versao 3 da Licenca, ou (a seu criterio) qualquer versao posterior.
import os
from typing import Any, Optional, Tuple

import psycopg2
import toml

# Caminhos base do projeto e secrets
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
SECRETS_PATH = os.path.join(PROJECT_ROOT, "config", "secrets.toml")


def load_db_config():
    """Carrega as configurações do banco de dados do arquivo secrets.toml."""
    if not os.path.exists(SECRETS_PATH):
        raise FileNotFoundError(
            f"ERRO DE SEGURANCA: Arquivo de segredos não encontrado em {SECRETS_PATH}. "
            "Crie o 'secrets.toml' na pasta 'config/' e preencha as credenciais do PostgreSQL."
        )
    try:
        config = toml.load(SECRETS_PATH)
        db_config = config.get("database", {})
        if db_config.get("type") != "postgres":
            raise ValueError("O tipo de banco de dados no secrets.toml não é 'postgres'.")
        return db_config
    except Exception as e:
        raise Exception(f"Erro ao ler secrets.toml: {e}")


# Config carregada uma vez
DB_CONFIG = load_db_config()


class DatabaseManager:
    """
    Controla a conexão e as operações básicas de persistência no PostgreSQL.
    """

    def __init__(self):
        self.conn = None
        self.cursor = None

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
                port=self.DB_PORT,
            )
            self.cursor = self.conn.cursor()
            print(f"Conexão ao DB PostgreSQL '{self.DB_NAME}' estabelecida.")
        except Exception as e:
            print(f"ERRO FATAL: Falha ao conectar ao PostgreSQL. Verifique o secrets.toml. Erro: {e}")
            raise

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple[Any, ...]] = None,
        fetch_one: bool = False,
        fetch_all: bool = False,
        commit: bool = False,
        return_rowcount: bool = False,
    ) -> Any:
        """
        Executa comandos SQL com suporte a fetch, retorno de ID (via RETURNING) e rowcount.
        """
        if not self.conn:
            raise ConnectionError("A conexão com o PostgreSQL não foi estabelecida.")

        try:
            is_dml = query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE"))
            last_id = None

            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            if is_dml and self.cursor.description:
                last_id = self.cursor.fetchone()[0]
            rowcount = self.cursor.rowcount

            if commit:
                self.conn.commit()
                if return_rowcount:
                    return rowcount
                if last_id is not None:
                    return last_id

            if fetch_one or fetch_all:
                if self.cursor.description:
                    columns = [desc[0] for desc in self.cursor.description]
                    data = self.cursor.fetchone() if fetch_one else self.cursor.fetchall()
                    return columns, data
                return None, None

            if return_rowcount:
                return rowcount
            if last_id is not None:
                return last_id

            return True

        except psycopg2.Error as e:
            print(f"Erro SQL (Postgres): {e}")
            self.conn.rollback()
            return False
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Erro inesperado durante a execução da query: {e}")

    def create_tables(self):
        """
        Cria todas as tabelas, adaptando a sintaxe para PostgreSQL.
        """
        usuarios_table_query = """
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE,
            funcao VARCHAR(100),
            require_password_change BOOLEAN DEFAULT FALSE,
            role VARCHAR(50) DEFAULT 'Vendedor',
            status VARCHAR(50) DEFAULT 'Ativo',
            hashed_password VARCHAR(128)
        );
        """

        pessoas_table_query = """
        CREATE TABLE IF NOT EXISTS pessoas (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            telefone VARCHAR(50),
            data_cadastro DATE NOT NULL DEFAULT NOW()
        );
        """

        eventos_tabel_query = """
        CREATE TABLE IF NOT EXISTS eventos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            data_evento DATE NOT NULL,
            tipo VARCHAR(100),
            status VARCHAR(50) DEFAULT 'Aberto'
        );
        """

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

        categorias_table_query = """
        CREATE TABLE IF NOT EXISTS categorias (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL UNIQUE,
            descricao TEXT,
            status VARCHAR(50) DEFAULT 'Ativo'
        );
        """

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

        estoque_table_query = """
        CREATE TABLE IF NOT EXISTS estoque (
            id SERIAL PRIMARY KEY,
            id_item INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            tipo_movimento VARCHAR(50) NOT NULL,
            data_movimento DATE NOT NULL DEFAULT NOW(),
            origem_recurso VARCHAR(100) DEFAULT 'Doacao',
            id_usuario INTEGER,
            id_evento INTEGER,
            FOREIGN KEY (id_item) REFERENCES itens(id),
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
            FOREIGN KEY (id_evento) REFERENCES eventos(id)
        );
        """

        vendas_table_query = """
        CREATE TABLE IF NOT EXISTS vendas (
            id SERIAL PRIMARY KEY,
            id_pessoa INTEGER,
            data_venda DATE NOT NULL DEFAULT NOW(),
            id_evento INTEGER NOT NULL,
            responsavel VARCHAR(255),
            id_movimento_caixa INTEGER NOT NULL,
            FOREIGN KEY (id_pessoa) REFERENCES usuarios(id),
            FOREIGN KEY (id_evento) REFERENCES eventos(id),
            FOREIGN KEY (id_movimento_caixa) REFERENCES movimentos_caixa(id)
        );
        """

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

        caixas_table_query = """
        CREATE TABLE IF NOT EXISTS caixas (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) UNIQUE NOT NULL,
            descricao VARCHAR(255),
            status VARCHAR(50) DEFAULT 'Ativo'
        );
        """

        movimentos_caixa_table_query = """
        CREATE TABLE IF NOT EXISTS movimentos_caixa (
            id SERIAL PRIMARY KEY,
            id_caixa INT NOT NULL,
            id_usuario_abertura INT NOT NULL,
            id_evento INT,
            valor_abertura NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
            status VARCHAR(50) NOT NULL DEFAULT 'Aberto',
            data_abertura TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            data_fechamento TIMESTAMP WITHOUT TIME ZONE,
            FOREIGN KEY (id_caixa) REFERENCES caixas(id),
            FOREIGN KEY (id_usuario_abertura) REFERENCES usuarios(id),
            FOREIGN KEY (id_evento) REFERENCES eventos(id)
        );
        """

        indexes_query = """
        CREATE INDEX IF NOT EXISTS idx_mov_caixa_caixa_id ON movimentos_caixa (id_caixa);
        CREATE INDEX IF NOT EXISTS idx_mov_caixa_status ON movimentos_caixa (status);
        """

        queries = [
            usuarios_table_query,
            pessoas_table_query,
            eventos_tabel_query,
            agendamentos_table_query,
            itens_table_query,
            estoque_table_query,
            vendas_table_query,
            itens_venda_table_query,
            movimentos_financeiros_table_query,
            caixas_table_query,
            movimentos_caixa_table_query,
            indexes_query,
        ]

        for query in queries:
            self.execute_query(query, commit=True)

        # Ajuste para bases já existentes: adiciona coluna se não existir
        self.execute_query(
            "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS require_password_change BOOLEAN DEFAULT FALSE;",
            commit=True,
        )
        # Ajuste FK de vendas.id_pessoa -> usuarios.id
        self.execute_query(
            """
            DO $$
            DECLARE
                exists_fk BOOLEAN;
            BEGIN
                SELECT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'vendas_id_pessoa_fkey'
                ) INTO exists_fk;

                IF exists_fk THEN
                    ALTER TABLE vendas DROP CONSTRAINT vendas_id_pessoa_fkey;
                END IF;

                ALTER TABLE vendas
                ADD CONSTRAINT IF NOT EXISTS vendas_id_pessoa_fkey
                FOREIGN KEY (id_pessoa) REFERENCES usuarios(id);
            END$$;
            """,
            commit=True,
        )
        self.execute_query(
            "ALTER TABLE movimentos_caixa ADD COLUMN IF NOT EXISTS id_evento INT NULL;",
            commit=True,
        )
        self.execute_query(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'fk_movimento_evento'
                ) THEN
                    ALTER TABLE movimentos_caixa
                        ADD CONSTRAINT fk_movimento_evento
                        FOREIGN KEY (id_evento) REFERENCES eventos(id);
                END IF;
            END$$;
            """,
            commit=True,
        )

        print("Estruturas de dados criadas ou verificadas no PostgreSQL.")

    def disconnect(self):
        """Fecha a conexão."""
        if self.conn:
            self.conn.close()
            print("Conexão ao DB PostgreSQL fechada.")
