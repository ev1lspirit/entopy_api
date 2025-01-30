import asyncio
import logging

from aiogram import Bot, Dispatcher
from source.config import Config
from source.log import setup_logging
from contextlib import asynccontextmanager

from source.utils import include_routers
from .app_state import get_app_state



@asynccontextmanager
async def bot_lifespan():
    app_state = get_app_state()
    await app_state.startup()
    yield
    await app_state.shutdown()


setup_logging(log_filename="app.log")

bot = Bot(token=Config.BOT_TOKEN)
dispatcher = Dispatcher()
include_routers(dispatcher)


async def main():
    async with bot_lifespan():
        await dispatcher.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())