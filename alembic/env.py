
import logging
import alembic.config
import sqlalchemy
from alembic import context
from sqlalchemy import create_engine, pool
from sqlmodel import SQLModel

from source.config import DatabaseSettings
from source.log import setup_logging
from source.models.vectors import *


# Загружаем конфигурацию Alembic
alembic_cfg = alembic.config.Config("alembic/alembic.ini")
alembic_cfg.set_main_option("script_location", "alembic")
alembic_cfg.set_main_option("sqlalchemy.url", DatabaseSettings().connection_link_sync)

target_metadata = SQLModel.metadata
setup_logging("alembic.log")


def run_migrations():
    """Запуск миграций Alembic."""
    engine = create_engine(
        DatabaseSettings().connection_link_sync,
        poolclass=pool.NullPool,
        future=True,
    )

    with engine.connect() as connection:
        context.configure(connection=connection,
                          target_metadata=target_metadata)
        logging.info("Starting migration process...")
        with context.begin_transaction():
            context.run_migrations()
        logging.info("Migration process completed.")

run_migrations()