import logging

import numpy as np

from source.app_state import inject_app_state, AppState
from source.celery.helpers import get_vector_from_redis
from source.celery.worker import celery_app
from source.entropy_finder.entro import FilteredSoundwave
from source.entropy_finder.utils import as_plot
from source.helpers import ensure_event_loop

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
@ensure_event_loop
@inject_app_state
def calculate_voice_entropy(self, redis_vector_key, redis_samplerate_key) -> list[tuple[float, float]]:
    raw_wave = get_vector_from_redis(sample_rate_key=redis_samplerate_key, vector_key=redis_vector_key)
    wave = FilteredSoundwave(raw_wave)
    divisions = np.fromiter(
        map(round, np.linspace(10, len(wave.points) - 1, 25)), dtype=np.int64)

    result = []
    entropy = 0
    for item in wave.entropy_over_time(every_index=10, n=100000, k=50000):
        result.append((item.interval_probability, item.interval_mean))
        entropy = item.H
    return result, entropy







