import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import URL, make_url

from src.utils.database_manager import load_db_config
from src.utils.database_urls import parse_test_database_url


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _database_url() -> URL:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return make_url(database_url).set(drivername="postgresql+psycopg2")

    test_database_url = os.getenv("TEST_DATABASE_URL")
    if test_database_url:
        db_config = parse_test_database_url(test_database_url)
        return make_url(db_config["dsn"]).set(drivername="postgresql+psycopg2")
    else:
        db_config = load_db_config()

    return URL.create(
        drivername="postgresql+psycopg2",
        username=db_config.get("user"),
        password=db_config.get("password"),
        host=db_config.get("host"),
        port=db_config.get("port"),
        database=db_config.get("dbname"),
    )


url = _database_url().render_as_string(hide_password=False)
config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
target_metadata = None


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
