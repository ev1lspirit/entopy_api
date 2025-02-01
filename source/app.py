import asyncio
import inspect
import logging
from functools import partial, wraps
from typing import Callable

from aiogram import Bot, Dispatcher
from source.config import Config
from source.helpers import run_sync
from source.log import setup_logging
from contextlib import asynccontextmanager

from source.bot_utils import include_routers
from .app_state import get_app_state


logger = logging.getLogger(__name__)


@asynccontextmanager
async def bot_lifespan(bot: Bot):
    app_state = get_app_state(bot)
    await app_state.startup()
    logging.info("App state was initialized...")
    yield
    await app_state.shutdown()


setup_logging(log_filename="app.log")

bot = Bot(token=Config.BOT_TOKEN)
dispatcher = Dispatcher()
include_routers(dispatcher)



async def main():
    async with bot_lifespan(bot=bot):
        await dispatcher.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())