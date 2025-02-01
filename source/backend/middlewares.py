# import logging
# from datetime import datetime
# from typing import Callable, Awaitable, Any
#
# from aiogram import BaseMiddleware
# from aiogram.types import TelegramObject
#
# from source.app_state import AppState
# from source.models.user import BotUser
#
# logger = logging.getLogger(__name__)
#
#
# class UserExistsMiddleware(BaseMiddleware):
#
#     def __init__(self, app_state: AppState):
#         self.app_state = app_state
#
#     async def __call__(
#         self,
#         handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
#         event: TelegramObject,
#         data: dict[str, Any]
#     ) -> Any:
#         user = data.get("event_from_user")
#         if not user:
#             logger.info("No user data in the data dict")
#             return await handler(event, data)
#         user_model = await self.app_state.db.user_repository.get_user(
#             user_id=user.id
#         )
#         if user_model is None:
#             logger.info(f"User with id {user.id} not found")
#             await self.app_state.db.user_repository.add_user(
#                 user_model=BotUser(
#                     id=user.id,
#                     username=user.username if user.username else None,
#                     registration_date=datetime.now()
#                 )
#             )
#         return await handler(event, data)