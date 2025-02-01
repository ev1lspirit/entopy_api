# models/user.py
import uuid
from datetime import datetime
from typing import Optional

import numpy as np
from sqlalchemy import UUID as SA_UUID, ARRAY, Column, Float
from sqlalchemy.orm import reconstructor
from sqlmodel import SQLModel, Field


class VectorizedVoice(SQLModel, table=True):
    __tablename__ = "voice"

    voice_id: uuid.UUID = Field(SA_UUID(as_uuid=True), primary_key=True)
    embedding: list[float] = Field(sa_column=Column(ARRAY(Float)))
    sample_rate: int = Field(nullable=False)
    detetime_sent: datetime
    sender_id: int = Field(nullable=False)
    sender_username: Optional[str]

    @reconstructor  # This runs after SQLAlchemy loads the object
    def convert_embedding(self):
        if isinstance(self.embedding, list):  # Ensure it's a list before conversion
            self.embedding = np.array(self.embedding, dtype=np.float32)


class AnalyzedVoice(SQLModel, table=True):
    voice_id: uuid.UUID = Field(primary_key=True, foreign_key="voice.voice_id")
    entropy: float = Field(nullable=False)
    average_entropy: Optional[float]
    overlapping_entropy: Optional[float]
    predicted_label: bool = Field(nullable=False)
    actual_label: Optional[bool]


