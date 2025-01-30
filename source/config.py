from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from environs import Env

PROJECT_DIR = Path(__file__).parent


env = Env()

try:
    env.read_env(Path(PROJECT_DIR, '../deployments/.env'))
except OSError:
    pass


@dataclass(frozen=True, slots=True)
class Config:
    BOT_TOKEN = env("BOT_TOKEN")

    LOGS_DIR = Path(PROJECT_DIR.parent, "logs")
    REDIS_DSN = env("REDIS_DSN")
    REDIS_PASS = env("REDIS_PASS")


@dataclass(frozen=True, slots=True)
class DatabaseSettings:
    DB_HOST: str = env("DB_HOST")
    DB_PORT: int = env.int("DB_PORT")
    DB_PASSWORD: str = env("DB_PASSWORD")
    DB_NAME: str = env("DB_NAME")
    DB_USER: str = env("DB_USER")

    @property
    def connection_link_async(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def connection_link_sync(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )