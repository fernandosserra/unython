"""Create the current Unython PostgreSQL schema.

Revision ID: 20261117_01
Revises:
"""
from alembic import op


revision = "20261117_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    statements = [
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE,
            funcao VARCHAR(100),
            require_password_change BOOLEAN DEFAULT FALSE,
            role VARCHAR(50) DEFAULT 'Vendedor',
            status VARCHAR(50) DEFAULT 'Ativo',
            hashed_password VARCHAR(128)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS pessoas (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            telefone VARCHAR(50),
            documento VARCHAR(50),
            preferencial BOOLEAN DEFAULT FALSE,
            observacoes TEXT,
            data_cadastro DATE NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS organizacao_config (
            id SERIAL PRIMARY KEY,
            nome_organizacao VARCHAR(150) NOT NULL DEFAULT 'Terreiro Caboclo Pena Branca',
            tipo_organizacao VARCHAR(100) NOT NULL DEFAULT 'Terreiro de Umbanda / Centro Espírita',
            termo_assistido VARCHAR(50) NOT NULL DEFAULT 'Consulente',
            termo_assistido_plural VARCHAR(50) NOT NULL DEFAULT 'Consulentes',
            termo_atendente VARCHAR(50) NOT NULL DEFAULT 'Médium / Cambone',
            termo_servico VARCHAR(50) NOT NULL DEFAULT 'Passe / Consulta',
            termo_atividade VARCHAR(50) NOT NULL DEFAULT 'Entidade / Serviço'
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS eventos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            data_evento DATE NOT NULL,
            tipo VARCHAR(100),
            status VARCHAR(50) DEFAULT 'Aberto'
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS caixas (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) UNIQUE NOT NULL,
            descricao VARCHAR(255),
            status VARCHAR(50) DEFAULT 'Ativo'
        )
        """,
        """
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
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS categorias (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL UNIQUE,
            descricao TEXT,
            status VARCHAR(50) DEFAULT 'Ativo'
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS itens (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL UNIQUE,
            valor_compra NUMERIC(10, 2),
            valor_venda NUMERIC(10, 2) NOT NULL,
            status VARCHAR(50) DEFAULT 'Ativo',
            id_categoria INTEGER,
            estoque_minimo INTEGER NOT NULL DEFAULT 0 CHECK (estoque_minimo >= 0),
            FOREIGN KEY (id_categoria) REFERENCES categorias(id)
        )
        """,
        """
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
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS facilitadores (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            especialidade VARCHAR(255),
            observacoes TEXT,
            status VARCHAR(50) NOT NULL DEFAULT 'Ativo',
            id_usuario_origem INTEGER UNIQUE REFERENCES usuarios(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS atividades_atendimento (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            descricao TEXT,
            status VARCHAR(50) NOT NULL DEFAULT 'Ativo'
        )
        """,
        """
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
        )
        """,
        """
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
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS itens_venda (
            id SERIAL PRIMARY KEY,
            id_venda INTEGER NOT NULL,
            id_item INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            valor_unitario NUMERIC(10, 2) NOT NULL,
            FOREIGN KEY (id_venda) REFERENCES vendas(id),
            FOREIGN KEY (id_item) REFERENCES itens(id)
        )
        """,
        """
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
        )
        """,
        """
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
        ALTER TABLE vendas ALTER COLUMN data_hora_venda SET DEFAULT CURRENT_TIMESTAMP
        """,
        """
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
        END $$
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_mov_caixa_caixa_id ON movimentos_caixa (id_caixa);
        CREATE INDEX IF NOT EXISTS idx_mov_caixa_status ON movimentos_caixa (status);
        CREATE INDEX IF NOT EXISTS idx_estoque_item ON estoque (id_item);
        CREATE INDEX IF NOT EXISTS idx_vendas_evento ON vendas (id_evento);
        CREATE INDEX IF NOT EXISTS idx_agendamentos_evento ON agendamentos (id_evento);
        CREATE INDEX IF NOT EXISTS idx_agendamentos_status ON agendamentos (status)
        """,
        """
        INSERT INTO organizacao_config (
            id, nome_organizacao, tipo_organizacao, termo_assistido,
            termo_assistido_plural, termo_atendente, termo_servico
        )
        SELECT 1, 'Terreiro Caboclo Pena Branca',
               'Terreiro de Umbanda / Centro Espírita', 'Consulente',
               'Consulentes', 'Médium / Cambone', 'Passe / Consulta'
        WHERE NOT EXISTS (SELECT 1 FROM organizacao_config WHERE id = 1)
        """,
    ]

    for statement in statements:
        op.execute(statement)


def downgrade():
    for table in (
        "itens_venda",
        "vendas",
        "agendamentos",
        "movimentos_financeiros",
        "estoque",
        "movimentos_caixa",
        "itens",
        "facilitadores",
        "atividades_atendimento",
        "eventos",
        "pessoas",
        "usuarios",
        "categorias",
        "caixas",
        "organizacao_config",
    ):
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
