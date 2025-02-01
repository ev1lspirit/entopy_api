from typing import Optional

from sqlalchemy import insert
from sqlmodel import select
from source.models.user import BotUser


class UserRepository:

    def __init__(self, db):
        self.db = db

    async def get_user(self, user_id: int) -> Optional[BotUser]:
        async with await self.db.get_session() as session:
            statement = select(BotUser).where(BotUser.id == user_id)
            result = await session.execute(statement)
            user = result.fetchone()
        return user[0] if user else None

    async def add_user(self, user_model: BotUser) -> None:
        async with await self.db.get_session() as session:
            session.add(user_model)
            await session.commit()