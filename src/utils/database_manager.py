# Unython - (C) 2025 siegrfried@gmail.com
# Este programa e software livre: voce pode redistribui-lo e/ou modifica-lo
# sob os termos da GNU General Public License como publicada pela Free Software Foundation,
# na versao 3 da Licenca, ou (a seu criterio) qualquer versao posterior.
import os
import sys
from typing import Any, Optional, Tuple, List
import psycopg2
from psycopg2 import pool
import toml

# Caminhos base do projeto e secrets
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
SECRETS_PATH = os.path.join(PROJECT_ROOT, "config", "secrets.toml")

_connection_pool: Optional[pool.ThreadedConnectionPool] = None
_db_checked: bool = False


def _safe_str(err: Any) -> str:
    """Decodifica com segurança mensagens de erro do PostgreSQL no Windows (evita quebra de UTF-8/CP1252)."""
    if isinstance(err, bytes):
        return err.decode("utf-8", errors="replace")
    msg = str(err)
    return msg


def load_db_config() -> dict:
    """Carrega as configurações do banco de dados do secrets.toml ou variáveis de ambiente."""
    # 1. Variáveis de ambiente têm prioridade
    env_host = os.getenv("PGHOST") or os.getenv("DB_HOST")
    if env_host:
        return {
            "type": "postgres",
            "host": env_host,
            "dbname": os.getenv("PGDATABASE") or os.getenv("DB_NAME", "unython"),
            "user": os.getenv("PGUSER") or os.getenv("DB_USER", "postgres"),
            "password": os.getenv("PGPASSWORD") or os.getenv("DB_PASS", ""),
            "port": int(os.getenv("PGPORT") or os.getenv("DB_PORT", 5432)),
        }

    # 2. Arquivo secrets.toml
    if os.path.exists(SECRETS_PATH):
        try:
            config = toml.load(SECRETS_PATH)
            db_config = config.get("database", {})
            if db_config:
                return db_config
        except Exception as e:
            print(f"Alerta ao ler secrets.toml: {_safe_str(e)}")

    # 3. Fallback padrão
    return {
        "type": "postgres",
        "host": "localhost",
        "dbname": "unython",
        "user": "postgres",
        "password": "",
        "port": 5432,
    }


DB_CONFIG = load_db_config()


def ensure_database_exists() -> bool:
    """
    Verifica se o banco de dados de destino existe no PostgreSQL.
    Caso não exista, conecta ao banco padrão 'postgres' e cria o banco automaticamente.
    """
    global _db_checked
    if _db_checked:
        return True

    cfg = load_db_config()
    target_db = cfg.get("dbname", "unython")
    host = cfg.get("host", "localhost")
    user = cfg.get("user", "postgres")
    password = cfg.get("password", "")
    port = cfg.get("port", 5432)

    try:
        # Conecta no banco de manutenção nativo do PostgreSQL ('postgres')
        conn = psycopg2.connect(
            host=host,
            database="postgres",
            user=user,
            password=password,
            port=port,
            options="-c client_encoding=UTF8",
        )
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (target_db,))
            exists = cur.fetchone()
            if not exists:
                print(f"[banco] O banco de dados '{target_db}' não existia. Criando agora no PostgreSQL...")
                safe_db_name = "".join(c for c in target_db if c.isalnum() or c == "_")
                cur.execute(f'CREATE DATABASE "{safe_db_name}";')
                print(f"[banco] Banco de dados '{safe_db_name}' criado com sucesso!")
            else:
                print(f"[banco] Banco de dados '{target_db}' verificado e pronto.")
        conn.close()
        _db_checked = True
        return True
    except Exception as e:
        err_msg = _safe_str(e)
        print(f"[banco] Aviso na verificação do banco de dados: {err_msg}")
        return False


def get_connection_pool() -> pool.ThreadedConnectionPool:
    """Obtém ou inicializa o pool de conexões com o PostgreSQL."""
    global _connection_pool
    if _connection_pool is None or _connection_pool.closed:
        ensure_database_exists()
        cfg = load_db_config()
        _connection_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=20,
            host=cfg.get("host", "localhost"),
            database=cfg.get("dbname", "unython"),
            user=cfg.get("user", "postgres"),
            password=cfg.get("password", ""),
            port=cfg.get("port", 5432),
            options="-c client_encoding=UTF8",
        )
    return _connection_pool


class DatabaseManager:
    """
    Controla a conexão e as operações básicas de persistência no PostgreSQL,
    utilizando pool de conexões para alta performance e criação automática do banco.
    """

    def __init__(self):
        self.conn = None
        self.cursor = None
        self._pool: Optional[pool.ThreadedConnectionPool] = None

        cfg = load_db_config()
        self.DB_HOST = cfg.get("host")
        self.DB_NAME = cfg.get("dbname")
        self.DB_USER = cfg.get("user")
        self.DB_PASS = cfg.get("password")
        self.DB_PORT = cfg.get("port")

    def connect(self):
        """Estabelece a conexão com o PostgreSQL (via pool com fallback direto)."""
        ensure_database_exists()
        try:
            self._pool = get_connection_pool()
            self.conn = self._pool.getconn()
            self.cursor = self.conn.cursor()
        except Exception:
            try:
                self.conn = psycopg2.connect(
                    host=self.DB_HOST,
                    database=self.DB_NAME,
                    user=self.DB_USER,
                    password=self.DB_PASS,
                    port=self.DB_PORT,
                    options="-c client_encoding=UTF8",
                )
                self.cursor = self.conn.cursor()
                self._pool = None
            except Exception as direct_err:
                print(f"ERRO FATAL: Falha ao conectar ao PostgreSQL '{self.DB_NAME}'. Erro: {_safe_str(direct_err)}")
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
                fetched = self.cursor.fetchone()
                if fetched:
                    last_id = fetched[0]
            rowcount = self.cursor.rowcount

            if commit:
                self.conn.commit()
                if return_rowcount:
                    return rowcount
                if last_id is not None:
                    return last_id
                return True

            if fetch_one or fetch_all:
                if self.cursor.description:
                    columns = [desc[0] for desc in self.cursor.description]
                    data = self.cursor.fetchone() if fetch_one else self.cursor.fetchall()
                    return columns, data
                return [], None if fetch_one else []

            if return_rowcount:
                return rowcount
            if last_id is not None:
                return last_id

            return True

        except psycopg2.Error as e:
            print(f"Erro SQL (Postgres): {_safe_str(e)}")
            if self.conn:
                self.conn.rollback()
            raise
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise

    def create_tables(self):
        """
        Cria todas as tabelas em ordem correta de dependências de Foreign Key.
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
            documento VARCHAR(50),
            preferencial BOOLEAN DEFAULT FALSE,
            observacoes TEXT,
            data_cadastro DATE NOT NULL DEFAULT NOW()
        );
        """

        organizacao_config_table_query = """
        CREATE TABLE IF NOT EXISTS organizacao_config (
            id SERIAL PRIMARY KEY,
            nome_organizacao VARCHAR(150) NOT NULL DEFAULT 'Terreiro Caboclo Pena Branca',
            tipo_organizacao VARCHAR(100) NOT NULL DEFAULT 'Terreiro de Umbanda / Centro Espírita',
            termo_assistido VARCHAR(50) NOT NULL DEFAULT 'Consulente',
            termo_assistido_plural VARCHAR(50) NOT NULL DEFAULT 'Consulentes',
            termo_atendente VARCHAR(50) NOT NULL DEFAULT 'Médium / Cambone',
            termo_servico VARCHAR(50) NOT NULL DEFAULT 'Passe / Consulta',
            termo_atividade VARCHAR(50) NOT NULL DEFAULT 'Entidade / Serviço'
        );
        """

        eventos_table_query = """
        CREATE TABLE IF NOT EXISTS eventos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            data_evento DATE NOT NULL,
            tipo VARCHAR(100),
            status VARCHAR(50) DEFAULT 'Aberto'
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
            valor_compra NUMERIC(10, 2),
            valor_venda NUMERIC(10, 2) NOT NULL,
            status VARCHAR(50) DEFAULT 'Ativo',
            id_categoria INTEGER,
            estoque_minimo INTEGER NOT NULL DEFAULT 0 CHECK (estoque_minimo >= 0),
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

        facilitadores_table_query = """
        CREATE TABLE IF NOT EXISTS facilitadores (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            especialidade VARCHAR(255),
            observacoes TEXT,
            status VARCHAR(50) NOT NULL DEFAULT 'Ativo',
            id_usuario_origem INTEGER UNIQUE REFERENCES usuarios(id)
        );
        """

        atividades_table_query = """
        CREATE TABLE IF NOT EXISTS atividades_atendimento (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            descricao TEXT,
            status VARCHAR(50) NOT NULL DEFAULT 'Ativo'
        );
        """

        agendamentos_table_query = """
        CREATE TABLE IF NOT EXISTS agendamentos (
            id SERIAL PRIMARY KEY,
            id_pessoa INTEGER NOT NULL,
            id_facilitador INTEGER,
            id_atividade INTEGER,
            data_hora TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            tipo_servico VARCHAR(100),
            status VARCHAR(50) DEFAULT 'Aguardando',
            id_evento INTEGER NOT NULL,
            compareceu VARCHAR(50) DEFAULT 'Pendente',
            numero_senha VARCHAR(20),
            preferencial BOOLEAN DEFAULT FALSE,
            ordem_chegada INTEGER DEFAULT 1,
            observacoes TEXT,
            FOREIGN KEY (id_pessoa) REFERENCES pessoas(id),
            FOREIGN KEY (id_facilitador) REFERENCES facilitadores(id),
            FOREIGN KEY (id_atividade) REFERENCES atividades_atendimento(id),
            FOREIGN KEY (id_evento) REFERENCES eventos(id)
        );
        """

        vendas_table_query = """
        CREATE TABLE IF NOT EXISTS vendas (
            id SERIAL PRIMARY KEY,
            id_pessoa INTEGER,
            data_venda DATE NOT NULL DEFAULT NOW(),
            data_hora_venda TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            id_evento INTEGER NOT NULL,
            responsavel VARCHAR(255),
            id_movimento_caixa INTEGER NOT NULL,
            FOREIGN KEY (id_pessoa) REFERENCES pessoas(id),
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
            nome_doador VARCHAR(255),
            forma_pagamento VARCHAR(100),
            status VARCHAR(50) NOT NULL DEFAULT 'Ativo',
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
            FOREIGN KEY (id_evento) REFERENCES eventos(id)
        );
        """

        alter_migrations_query = """
        -- Migrações idempotentes para tabelas existentes
        ALTER TABLE pessoas ADD COLUMN IF NOT EXISTS preferencial BOOLEAN DEFAULT FALSE;
        ALTER TABLE pessoas ADD COLUMN IF NOT EXISTS documento VARCHAR(50);
        ALTER TABLE pessoas ADD COLUMN IF NOT EXISTS observacoes TEXT;

        ALTER TABLE organizacao_config ADD COLUMN IF NOT EXISTS nome_organizacao VARCHAR(150) DEFAULT 'Terreiro Caboclo Pena Branca';
        ALTER TABLE organizacao_config ADD COLUMN IF NOT EXISTS termo_atividade VARCHAR(50) NOT NULL DEFAULT 'Entidade / Serviço';

        ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS numero_senha VARCHAR(20);
        ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS preferencial BOOLEAN DEFAULT FALSE;
        ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS ordem_chegada INTEGER DEFAULT 1;
        ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS observacoes TEXT;
        ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS id_atividade INTEGER REFERENCES atividades_atendimento(id);
        ALTER TABLE itens ADD COLUMN IF NOT EXISTS estoque_minimo INTEGER NOT NULL DEFAULT 0 CHECK (estoque_minimo >= 0);
        ALTER TABLE itens ALTER COLUMN valor_compra DROP NOT NULL;
        ALTER TABLE movimentos_financeiros ADD COLUMN IF NOT EXISTS nome_doador VARCHAR(255);
        ALTER TABLE movimentos_financeiros ADD COLUMN IF NOT EXISTS forma_pagamento VARCHAR(100);
        ALTER TABLE vendas ADD COLUMN IF NOT EXISTS data_hora_venda TIMESTAMP WITH TIME ZONE;
        ALTER TABLE vendas ALTER COLUMN data_hora_venda SET DEFAULT CURRENT_TIMESTAMP;

        -- Converte os vínculos antigos com usuários uma única vez, preservando o histórico.
        DO $$
        DECLARE antiga_fk record;
        BEGIN
            FOR antiga_fk IN
                SELECT conname FROM pg_constraint
                WHERE conrelid = 'agendamentos'::regclass
                  AND confrelid = 'usuarios'::regclass AND contype = 'f'
                  AND conkey = ARRAY[(SELECT attnum FROM pg_attribute
                                      WHERE attrelid = 'agendamentos'::regclass
                                        AND attname = 'id_facilitador')]::smallint[]
            LOOP
                INSERT INTO facilitadores (nome, especialidade, id_usuario_origem)
                SELECT u.nome, u.funcao, u.id FROM usuarios u
                WHERE EXISTS (SELECT 1 FROM agendamentos a WHERE a.id_facilitador = u.id)
                ON CONFLICT (id_usuario_origem) DO NOTHING;
                EXECUTE format('ALTER TABLE agendamentos DROP CONSTRAINT %I', antiga_fk.conname);
                UPDATE agendamentos a SET id_facilitador = f.id
                FROM facilitadores f WHERE f.id_usuario_origem = a.id_facilitador;
                ALTER TABLE agendamentos ADD CONSTRAINT agendamentos_facilitador_catalogo_fk
                    FOREIGN KEY (id_facilitador) REFERENCES facilitadores(id);
            END LOOP;
        END $$;
        """

        indexes_query = """
        CREATE INDEX IF NOT EXISTS idx_mov_caixa_caixa_id ON movimentos_caixa (id_caixa);
        CREATE INDEX IF NOT EXISTS idx_mov_caixa_status ON movimentos_caixa (status);
        CREATE INDEX IF NOT EXISTS idx_estoque_item ON estoque (id_item);
        CREATE INDEX IF NOT EXISTS idx_vendas_evento ON vendas (id_evento);
        CREATE INDEX IF NOT EXISTS idx_agendamentos_evento ON agendamentos (id_evento);
        CREATE INDEX IF NOT EXISTS idx_agendamentos_status ON agendamentos (status);
        """

        queries = [
            usuarios_table_query,
            pessoas_table_query,
            organizacao_config_table_query,
            eventos_table_query,
            caixas_table_query,
            movimentos_caixa_table_query,
            categorias_table_query,
            itens_table_query,
            estoque_table_query,
            facilitadores_table_query,
            atividades_table_query,
            agendamentos_table_query,
            vendas_table_query,
            itens_venda_table_query,
            movimentos_financeiros_table_query,
            alter_migrations_query,
            indexes_query,
        ]

        for query in queries:
            self.execute_query(query, commit=True)

        # Garante configuração padrão de organização se a tabela estiver vazia
        try:
            self.execute_query(
                """
                INSERT INTO organizacao_config (id, nome_organizacao, tipo_organizacao, termo_assistido, termo_assistido_plural, termo_atendente, termo_servico)
                SELECT 1, 'Terreiro Caboclo Pena Branca', 'Terreiro de Umbanda / Centro Espírita', 'Consulente', 'Consulentes', 'Médium / Cambone', 'Passe / Consulta'
                WHERE NOT EXISTS (SELECT 1 FROM organizacao_config WHERE id = 1);
                """,
                commit=True
            )
        except Exception as e:
            print(f"[banco] Aviso ao inicializar organizacao_config: {_safe_str(e)}")

        print("[banco] Estruturas de dados criadas ou verificadas no PostgreSQL.")

    def disconnect(self):
        """Fecha o cursor e devolve a conexão ao pool (ou fecha se direta)."""
        if self.cursor:
            try:
                self.cursor.close()
            except Exception:
                pass
            self.cursor = None

        if self.conn:
            try:
                if self._pool and not self._pool.closed:
                    self._pool.putconn(self.conn)
                else:
                    self.conn.close()
            except Exception:
                pass
            self.conn = None
