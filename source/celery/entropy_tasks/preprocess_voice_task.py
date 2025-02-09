import logging
import pickle
import librosa
from source.app_state import inject_app_state, AppState
from source.celery.helpers import get_vector_from_redis
from source.celery.worker import celery_app
from source.config import Config
from source.entropy_finder.custom_types import RawWave
from source.entropy_finder.entro import BaseSoundwave, FilteredSoundwave
from source.helpers import ensure_event_loop


def preprocess_signal(wave: RawWave) -> FilteredSoundwave:
    raw_voice = BaseSoundwave(wave)
    cut_sample_len = int(0.05 * len(raw_voice.points))
    avg_max, avg_min = raw_voice.average_extremum
    threshold = (abs(avg_max) + abs(avg_min)) / 4
    filtered_voice = raw_voice.filter(threshold=threshold, step=cut_sample_len)
    return filtered_voice.normalize(target_ratio=Config.UNIVERSAL_VOLUME_RATIO)


@celery_app.task(bind=True)
@ensure_event_loop
@inject_app_state
def preprocess_voice(self, redis_vector_key: str, redis_samplerate_key: str) -> None:
    app_state: AppState = self.app_state
    raw_wave = get_vector_from_redis(sample_rate_key=redis_samplerate_key, vector_key=redis_vector_key)
    preprocessed_wave = preprocess_signal(raw_wave)

    app_state.redis_app.set(name=redis_vector_key, value=pickle.dumps(preprocessed_wave.points))
    app_state.redis_app.set(name=redis_samplerate_key, value=preprocessed_wave.sample_rate)




