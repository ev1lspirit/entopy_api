import inspect
import logging
from functools import wraps
from typing import Callable, Optional

from redis import Redis

from database import init_database
from source.config import Config
from source.helpers import run_sync

logger = logging.getLogger(__name__)


class AppStateSingletonMeta(type):
    __instance = None

    def __call__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__call__(*args, **kwargs)
        logger.info(cls.__instance)
        return cls.__instance


class AppState(metaclass=AppStateSingletonMeta):

    def __init__(self):
        self.redis_app: Optional[Redis] = None

    async def startup(self):
        """
        Инициализация всех необходимых объектов.
        """
        self.db = await init_database()
        self.redis_app = Redis.from_url(url=Config.REDIS_DSN)

    async def shutdown(self):
        """
        Завершение работы для всех объектов, где это требуется.
        """
        await self.db.close()


def inject_app_state(celery_task: Callable = None) -> Callable:

    task_signature = inspect.signature(celery_task).parameters
    if "self" not in task_signature:
        raise TypeError(f"self parameter is not set. Signature: {task_signature}")

    @wraps(celery_task)
    def celery_wrapper(self, *args, **kwargs):
        app_state = get_app_state()
        run_sync(
            app_state.startup()
        )
        logger.info(f"Opening app state for task with id {self.request.id}")
        self.app_state = app_state
        result = celery_task(self, *args, **kwargs)
        run_sync(
            app_state.shutdown()
        )
        logger.info(f"Closing app state for task with id {self.request.id}")
        return result
    return celery_wrapper


def get_app_state():
    app_state = AppState()
    return app_state


