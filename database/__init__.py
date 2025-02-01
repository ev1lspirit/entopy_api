import asyncio
import logging
from _socket import gaierror
from .db import Database
from source.config import DatabaseSettings

logger = logging.getLogger(__name__)


async def init_database():
    db_config = DatabaseSettings()
    logger.info(type(db_config.DB_PORT))
    db = Database(db_config)
    connected = False
    while not connected:
        try:
            logger.debug('Attempting to connect to the database...')
            await db.create()
            await db.init_repo()
            logger.info('Successfully connected to the database!')
            break
        except gaierror as e:
            logger.error(f'Failed to connect to the database. Retrying in 5 seconds...')
            logger.info(f"Conn link: {db_config.connection_link_async()}")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Failed to connect to the database. Error: {e}")
            raise e
    return db