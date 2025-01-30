# models/user.py
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int = Field(primary_key=True)
    name: str
    email: str

