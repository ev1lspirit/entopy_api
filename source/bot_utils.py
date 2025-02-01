from aiogram import Dispatcher
from source.backend.main.routes import router as main_router
from source.backend.entropy.routes import router as entropy_router


def include_routers(dispatcher: Dispatcher):
    dispatcher.include_router(main_router)
    dispatcher.include_router(entropy_router)