from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class BotUser(SQLModel, table=True):
    __tablename__ = "user"

    id: int = Field(primary_key=True)
    username: Optional[str]
    registration_date: datetime
    last_interaction_date: Optional[datetime]
