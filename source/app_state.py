from database import init_database


class AppStateSingletonMeta(type):
    __instance = None

    def __call__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__call__(*args, **kwargs)
        return cls.__instance


class AppState(metaclass=AppStateSingletonMeta):

    async def startup(self):
        """
        Инициализация всех необходимых объектов.
        """
        self.db = await init_database()


    async def shutdown(self):
        """
        Завершение работы для всех объектов, где это требуется.
        """
        await self.db.close()


def get_app_state():
    app_state = AppState()
    return app_state
