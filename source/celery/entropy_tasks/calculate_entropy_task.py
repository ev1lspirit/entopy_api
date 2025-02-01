import logging
import time
from uuid import UUID

import numpy as np

from source.app_state import inject_app_state, AppState
from source.celery.worker import celery_app
from source.helpers import ensure_event_loop, run_sync
from source.models.vectors import VectorizedVoice

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
@ensure_event_loop
@inject_app_state
def calculate_voice_entropy(self, voice_id: UUID):
    app_state: AppState = self.app_state

    voice: VectorizedVoice = run_sync(
        app_state.db.entropy_repository.get_voice_by_uuid(
            voice_id=voice_id
        )
    )
    logger.info(f"Received voice: {voice}")
