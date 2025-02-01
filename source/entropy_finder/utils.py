import os
from functools import wraps
import typing as tp
from custom_types import RawWave
import scipy.io.wavfile as wav
import numpy as np


def audioread(address: str) -> RawWave:
    if not os.path.exists(address):
        raise FileExistsError("No such wav. file: %s" % address)
    base, ext = os.path.splitext(address)
    if ext != '.wav':
        raise TypeError("Invalid extension, expected .wav, got %s" % ext)
    fs_, signal_ = wav.read(address)
    signal_ = np.transpose(signal_)
    if signal_.ndim > 1:
            signal_ = signal_[0]
    return RawWave(fs_, (signal_ / 32767))


def as_plot(iterable):
    y, x = [], []
    for item in iterable:
        y.append(item.interval_mean)
        x.append(item.interval_probability)
    return y, x


class ValueKeepingGenerator(object):
    def __init__(self, g):
        self.g = g
        self.value = None

    def __iter__(self):
        self.value = yield from self.g




def no_yield(f):
    @wraps(f)
    def g(*args, **kwargs):
        obj = ValueKeepingGenerator(f(*args, **kwargs))
        for _ in obj: pass
        return obj.value
    return g





