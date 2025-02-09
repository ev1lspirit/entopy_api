import uuid
from datetime import datetime
import pandas as pd
from typing import Optional
from sqlmodel import select
import numpy as np
from source.models.vectors import VectorizedVoice


class EntropyRepository:

    def __init__(self, db):
        self.db = db

    async def upload_voice_to_db(self, *, voice_id: str, sender_id: int, sender_username: Optional[str],
                                 vector: np.ndarray, sample_rate: int) -> str:
        async with await self.db.get_session() as session:
            model = VectorizedVoice(
                voice_id=voice_id,
                embedding=vector,
                detetime_sent=datetime.now(),
                sender_id=sender_id,
                sender_username=sender_username,
                sample_rate=sample_rate
            )
            session.add(model)
            await session.commit()
        return model.voice_id

    async def check_if_sample_exists(self, *, voice_id: str) -> Optional[str]:
        async with await self.db.get_session() as session:
            statement = select(VectorizedVoice.voice_id).where(
                VectorizedVoice.voice_id == voice_id
            )
            result = await session.execute(statement)
            voice = result.fetchone()
        return voice[0] if voice else None

    async def get_voice_by_uuid(self, *, voice_id: str) -> Optional[VectorizedVoice]:
        async with await self.db.get_session() as session:
            statement = select(VectorizedVoice).where(
                VectorizedVoice.voice_id == voice_id
            )
            result = await session.execute(statement)
            voice = result.fetchone()
        return voice[0] if voice else None



    