import logging
from asyncio import current_task

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, async_sessionmaker, \
    async_scoped_session

from source.config import DatabaseSettings


class Database:

    def __init__(self, config: DatabaseSettings):
        self.config = config
        self.engine = None
        self.session_maker = None
        self.scoped_session = None

    async def create(self):
        self.engine = AsyncEngine(
            create_engine(url=self.config.connection_link_async,
                          echo=True,
                          pool_size=20,
                          max_overflow=20,
                          pool_recycle=3600,
                          pool_pre_ping=True,
                          future=True
                          )
        )

        # Create an async sessionmaker
        self.session_maker = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        self.scoped_session = async_scoped_session(
            self.session_maker,
            scopefunc=current_task
        )

    async def close(self):
        """Закрываем движок базы данных."""
        if self.engine is None:
            raise Exception("Database is not initialized")
        await self.engine.dispose()

    async def __aenter__(self):
        """Вход в асинхронный контекст (инициализация сессии)."""
        if self.scoped_session is None:
            raise Exception("Database is not initialized")
        self.session = self.scoped_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Выход из асинхронного контекста (закрытие сессии)."""
        await self.session.close()

    async def get_session(self):
        """Возвращаем асинхронную сессию."""
        if self.scoped_session is None:
            raise Exception("Database is not initialized")
        return self.scoped_session()