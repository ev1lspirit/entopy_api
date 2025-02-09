import asyncio
import logging
from functools import wraps, partial
from typing import Callable, Coroutine, Any, TypeVar, Awaitable, Optional
import inspect
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State

T = TypeVar("T")


logger = logging.info(__name__)

def init_event_loop():
    """
    Зависимость для celery, позволяющая инициализировать EventLoop
    для работы асинхронных вызовов.
    Если EventLoop уже был создан, ничего не происходит.
    """
    try:
        asyncio.get_event_loop()
    except Exception as err:
        print(type(err))
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)


def run_sync(func: Coroutine[Any, Any, T]) -> T:
    """
    Вспомогательный метод для синхронного запуска асинхронных функций.
    """
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(func)
    return result




def ensure_event_loop(celery_task: Callable) -> Callable:
    @wraps(celery_task)
    def celery_task_wrapper(*args, **kwargs):
        init_event_loop()
        return celery_task(*args, **kwargs)
    return celery_task_wrapper