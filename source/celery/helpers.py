import pickle

from source.app_state import get_app_state
from source.entropy_finder.custom_types import RawWave


def get_vector_from_redis(*, sample_rate_key, vector_key: str) -> RawWave:
    app_state = get_app_state()
    sample_rate = int(app_state.redis_app.get(sample_rate_key))
    vector = pickle.loads(app_state.redis_app.get(vector_key))
    return RawWave(wave_id=vector_key, sample_rate=sample_rate, data=vector)
