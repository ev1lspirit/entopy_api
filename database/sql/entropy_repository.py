import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import select
import numpy as np
from source.models.vectors import VectorizedVoice


class EntropyRepository:

    def __init__(self, db):
        self.db = db

    async def upload_voice_to_db(self, *, sender_id: int, sender_username: Optional[str],
                                 vector: np.ndarray, sample_rate: int) -> uuid.UUID:
        async with await self.db.get_session() as session:
            model = VectorizedVoice(
                voice_id=uuid.uuid4(),
                embedding=vector,
                detetime_sent=datetime.now(),
                sender_id=sender_id,
                sender_username=sender_username,
                sample_rate=sample_rate
            )
            session.add(model)
            await session.commit()
        return model.voice_id

    async def get_voice_by_uuid(self, *, voice_id: uuid.UUID) -> Optional[VectorizedVoice]:
        async with await self.db.get_session() as session:
            statement = select(VectorizedVoice).where(
                VectorizedVoice.voice_id == voice_id
            )
            result = await session.execute(statement)
            voice = result.fetchone()
        return voice[0] if voice else None



    