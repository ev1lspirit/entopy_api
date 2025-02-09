from dataclasses import dataclass
from enum import StrEnum
from typing import Optional

import numpy as np


@dataclass
class RawWave:
    sample_rate: int
    data: np.ndarray
    wave_id: Optional[str] = None

    @property
    def duration(self):
        return self.data.shape[0] / self.sample_rate


class SignalTypes(StrEnum):
    GENUINE = "GENUINE"
    SYNTHETIC = "SYNTHETIC"


@dataclass
class EntropyMetadata:
    total_signal_values: int
    n: int
    k: int
    H: int
    frequencies: dict
    entropy_influence: list

    @property
    def probability_sum(self):
        return sum(map(lambda item: item / self.total_signal_values,
                       self.frequencies.values()))

    @property
    def total_assigned_values(self):
        return sum(self.frequencies.values()), self.total_signal_values


@dataclass(slots=True)
class EntropyRecord:
    H: int
    psum: int
    interval_mean: int
    interval_probability: float
