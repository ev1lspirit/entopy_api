from __future__ import annotations
import itertools
import logging
from collections import OrderedDict
from functools import wraps, partial
import typing as tp
import librosa
import numpy as np
from itertools import chain
from scipy.ndimage import gaussian_filter
from scipy.signal import resample, stft, medfilt
from custom_types import RawWave, SignalTypes, EntropyRecord
import math
from utils import no_yield
from functools import cached_property


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def normalize_volume(*, leader: FilteredSoundwave, follower: FilteredSoundwave) -> tuple[FilteredSoundwave, FilteredSoundwave]:
    target_ratio = (leader.rms + follower.rms) / 2
    return (
        leader.from_numpy(
            data=leader.normalize_to_rms(target_ratio),
            sample_rate=leader.sample_rate,
            name=leader.name,
            label=leader.label
        ),
        follower.from_numpy(
            data=follower.normalize_to_rms(target_ratio),
            sample_rate=follower.sample_rate,
            name=follower.name,
            label=follower.label
        )
    )

def preserve_metadata(function=None, fields=()):
    if function is None:
        return partial(preserve_metadata, fields=fields)
    if not fields:
        raise TypeError("Specify fields to preserve")

    @wraps(function)
    def wrapper(self, *args, **kwargs):
        instance = function(self, *args, **kwargs)
        for field in fields:
            setattr(instance, field, getattr(self, field, None))
        return instance
    return wrapper



class BaseSoundwave:

    def __init__(self, raw_wave: RawWave, label: SignalTypes=None, name="None"):
        self.label = label
        self.name = name
        self.wave = raw_wave
        self.t = np.linspace(0., self.wave.duration, self.wave.data.shape[0])

    def __repr__(self):
        return f"BaseSoundwave(name={self.name}, label={self.label})"

    @staticmethod
    def equalize_waves(*waves) -> list[BaseSoundwave]:
        reference: FilteredSoundwave = max(waves, key=lambda wave: wave.points.shape[0])
        to_equalize: tp.Generator[FilteredSoundwave, None, None] = filter(lambda wave: wave != reference, waves)
        equalized_waves = []

        for wave in to_equalize:
            gap = reference.points.shape[0] - wave.points.shape[0]
            if len(wave.points) < gap:
                pass
            else:
                new_length = list(wave.points)
                new_length.extend(wave.points[:gap])
                equalized_waves.append(
                    FilteredSoundwave.from_numpy(
                        sample_rate=wave.sample_rate,
                        data=np.array(new_length),
                        name=wave.name,
                        label=wave.label
                    )
                )
        equalized_waves.append(reference)
        return sorted(equalized_waves, key=lambda wave: 1 if wave.label == SignalTypes.GENUINE else 0, reverse=True)

    @preserve_metadata(fields=("name", "label"))
    def normalize(self, target_ratio: float) -> BaseSoundwave:
        return self.from_numpy(
            sample_rate=self.sample_rate, data=self.normalize_to_rms(target_ratio)
        )

    @preserve_metadata(fields=("name",  "label"))
    def resample(self, from_wave: FilteredSoundwave):
        if len(self.points) != len(from_wave.points):
            return self.from_numpy(
                sample_rate=from_wave.sample_rate,
                data=resample(self.points, round(len(self.points) * float(from_wave.sample_rate) / self.sample_rate))
            )
        return self

    def as_plot(self):
        return self.t, self.wave.data

    def as_coordinates(self):
        return zip(self.t, self.wave.data)

    def extwrapper(self, diff_colors=False):
        increasing = False if self.wave.data[1] < self.wave.data[0] else True
        average_min = 0
        average_max = 0
        max_total, min_total = 0, 0
        minima = []
        maxima = []

        for index in range(1, len(self.wave.data)):
            if self.wave.data[index] > self.wave.data[index - 1]:
                if increasing:
                    continue
                average_min += self.wave.data[index - 1]
                min_total += 1
                increasing = True
                minima.append((self.wave.data[index - 1], index - 1))

            elif self.wave.data[index] < self.wave.data[index - 1]:
                if not increasing:
                    continue
                average_max += self.wave.data[index - 1]
                max_total += 1
                increasing = False
                maxima.append((self.wave.data[index - 1], index - 1))
            else:
                continue

        assert isinstance(diff_colors, bool)
        if diff_colors:
            maxx = list(map(lambda x: x[0], maxima))
            maxy = list(map(lambda x: self.t[x[1]], maxima))
            minx = list(map(lambda x: x[0], minima))
            miny = list(map(lambda x: self.t[x[1]], minima))
            return [maxx, maxy], [minx, miny]

        sorted_extremums = sorted(chain(minima, maxima), key=lambda x: x[1])
        return list(map(lambda x: x[0], sorted_extremums)), list(map(lambda x: self.t[x[1]], sorted_extremums))

    def extaverage(self, *, audio=None):
        if audio is None:
            audio = self.wave.data
        assert len(audio) > 2, "Sample must contain more than 2 points"
        increasing = False if audio[1] < audio[0] else True
        average_min = 0
        average_max = 0
        max_total, min_total = 0, 0

        for index in range(1, len(audio)):
            if audio[index] > audio[index - 1]:
                if increasing:
                    continue
                average_min += audio[index - 1]
                min_total += 1
                increasing = True

            elif audio[index] < audio[index - 1]:
                if not increasing:
                    continue
                average_max += audio[index - 1]
                max_total += 1
                increasing = False
            else:
                continue
        if min_total:
            average_min /= min_total
        if max_total:
            average_max /= max_total
        return average_max, average_min

    @preserve_metadata(fields=("name",  "label"))
    def filter(self, threshold, step) -> FilteredSoundwave:
        index_pairs = OrderedDict()
        recent_low = 0
        recent_high = 0
        for index in range(0, len(self.wave.data) - step - 1, step):
            avg_max, avg_min = self.extaverage(audio=self.wave.data[index: index + step])
            if avg_max < threshold and avg_min > -threshold:
                if index == recent_high:
                    recent_high = index + step
                else:
                    index_pairs[recent_low] = recent_high
                    recent_low = index
                    recent_high = index + step

        index_pairs[recent_low] = recent_high
        index_pairs[len(self.wave.data)] = 0
        ranges = list(index_pairs.items())
        result = []
        for i in range(1, len(ranges)):
            _, from_index = ranges[i - 1]
            to_index, _ = ranges[i]
            for j in range(from_index, to_index):
                result.append(self.wave.data[j])
        return FilteredSoundwave.from_numpy(self.wave.sample_rate, np.array(result))

    @preserve_metadata(fields=("name",  "label"))
    def lstrip(self, threshold, partition_size=500) -> FilteredSoundwave:
        rem = len(self.wave.data) % partition_size

        clear_till = len(self.wave.data) - rem
        intervals = zip(reversed(np.arange(0, len(self.wave.data), partition_size)),
                        reversed(np.arange(partition_size, len(self.wave.data) - partition_size, partition_size)))
        if rem:
            rems = ((len(self.wave.data), len(self.wave.data) - rem) for _ in range(1))
            intervals = chain(rems, intervals)

        for rborder, lborder in intervals:
            avg_max, avg_min = self.extaverage(audio=self.wave.data[lborder:rborder])
            if avg_max > threshold and avg_min < -threshold:
                break
            if not avg_min or not avg_max:
                part_mean = np.mean(self.wave.data[lborder:rborder])
                if part_mean > threshold or part_mean < -threshold:
                    break
            clear_till -= partition_size
        return FilteredSoundwave.from_numpy(self.wave.sample_rate, np.array(self.wave.data[:clear_till]),
                                            name=self.name)

    @preserve_metadata(fields=("name",  "label"))
    def rstrip(self, *, threshold, partition_size=500) -> FilteredSoundwave:
        rem = len(self.wave.data) % partition_size
        clear_till = 0
        remainder = ((len(self.wave.data) - rem, len(self.wave.data)) for _ in range(1))
        intervals = zip(range(0, len(self.wave.data), partition_size),
                        range(partition_size, len(self.wave.data) - partition_size, partition_size))

        for lborder, rborder in chain(intervals, remainder):
            avg_max, avg_min = self.extaverage(audio=self.wave.data[lborder:rborder])
            if avg_max > threshold or avg_min < -threshold:
                break
            if not avg_min or not avg_max:
                part_mean = np.mean(self.wave.data[lborder:rborder])
                if part_mean > threshold or part_mean < -threshold:
                    break
            clear_till += partition_size
        return FilteredSoundwave.from_numpy(self.wave.sample_rate, np.array(self.wave.data[clear_till:]))

    @classmethod
    def from_numpy(cls, sample_rate: int, data: np.ndarray, **kwargs):
        return cls(RawWave(sample_rate, data), **kwargs)

    @preserve_metadata(fields=("name",  "label"))
    def add_gaussian_noise(self, amplitude=1, mean=0, std=1) -> BaseSoundwave:
        return self.from_numpy(sample_rate=self.wave.sample_rate,
                                        data=self.wave.data + amplitude * np.random.normal(mean,std,len(self.wave.data)))

    @preserve_metadata(fields=("name",  "label"))
    def filter_gaussian_noise(self) -> BaseSoundwave:
        result = gaussian_filter(input=self.points, sigma=1)
        magnitude, phase = librosa.magphase(librosa.stft(result))
        noise_power = np.mean(magnitude[:, :int(self.sample_rate * 0.1)], axis=1)
        mask = magnitude > noise_power[:, None]
        mask = mask.astype(float)
        mask = medfilt(mask, kernel_size=(1, 5))
        clean = magnitude * mask
        return self.from_numpy(
            sample_rate=self.sample_rate,
            data=librosa.istft(clean * phase)
        )

    @cached_property
    def rms(self):
        return np.sqrt(np.sum(np.power(self.points, 2)) / self.points.shape[0])

    def normalize_to_rms(self, target_ratio):
        ratio = target_ratio / self.rms
        return self.points * ratio

    @property
    def points(self):
        return self.wave.data

    @property
    def sample_rate(self):
        return self.wave.sample_rate

    @staticmethod
    @preserve_metadata(fields=("name", "label"))
    def simulate_packet_loss(signal: BaseSoundwave, max_loss_fraction=0.05) -> FilteredSoundwave:
        """
        Удаляет случайный небольшой отрезок из сигнала, имитируя потерю пакета данных.

        :param signal: list или numpy.array, входной сигнал.
        :param max_loss_fraction: float, максимальная длина удаляемого отрезка относительно длины сигнала (от 0 до 1).
        :return: numpy.array, сигнал с удаленным отрезком.
        """
        if not 0 < max_loss_fraction <= 1:
            raise ValueError("max_loss_fraction должен быть в диапазоне (0, 1].")

        signal_length = len(signal.points)
        if signal_length == 0:
            raise ValueError("Длина сигнала должна быть больше 0.")

        # Выбираем случайную длину потерянного отрезка
        max_loss_length = int(signal_length * max_loss_fraction)
        loss_length = np.random.randint(1, max_loss_length + 1)

        # Выбираем случайное начало отрезка
        start_idx = np.random.randint(0, signal_length - loss_length)
        end_idx = start_idx + loss_length

        # Удаляем отрезок
        modified_signal = np.concatenate((signal.points[:start_idx], signal.points[end_idx:]))
        return FilteredSoundwave.from_numpy(
            sample_rate=signal.sample_rate,
            data=modified_signal
        )


    def remove_noise(self, method = ''):
        pass


class FilteredSoundwave(BaseSoundwave):

    def _get_nk_intervals(self, n, k):
        fn_max = max(self.wave.data)
        fn_min = min(self.wave.data)
        avg_max, avg_min = self.extaverage()
        avg_min_to_max = np.linspace(avg_min, avg_max, n+1, dtype=np.double)
        from_min_to_avg_min = np.linspace(fn_min, avg_min, k // 2 + 1, dtype=np.double)
        from_avg_max_to_max = np.linspace(avg_max, fn_max, k // 2 + 1, dtype=np.double)
        total = np.concatenate([from_min_to_avg_min[:-1], avg_min_to_max[:-1], from_avg_max_to_max])
        return tuple(map(lambda i: (total[i-1], total[i]), range(1, len(total))))

    def _get_n_intervals(self, n):
        fn_max = max(self.wave.data)
        fn_min = min(self.wave.data)
        total = np.linspace(fn_min, fn_max, n, dtype=np.double)
        return tuple(map(lambda i: (total[i - 1], total[i]), range(1, len(total))))

    def get_intervals(self, n=None, k=None):
        if isinstance(n, int) and k is None:
            return self._get_n_intervals(n)
        elif isinstance(n, int) and isinstance(k, int):
            return self._get_nk_intervals(n, k)
        raise ValueError("n cannot be None or nonint")

    def _calculate_entropy(self, sample, *, n, k):
        intervals = self.get_intervals(n=n, k=k)
        audio = np.array(sorted(sample))
        index = 0
        frequency = 0
        psum = 0
        interval_index = 0
        total_processed = 0

        # freqs = defaultdict(float)
        probability_sum = 0

        while index < len(audio):
            if intervals[interval_index][0] <= audio[index] <= intervals[interval_index][1]:
                frequency += 1
            else:
                if frequency > 0:
                    p = frequency / len(audio)
                    probability_sum += p
                    total_processed += frequency
                    #freqs[intervals[interval_index]] = frequency
                    psum -= p * math.log2(p)
                    frequency = 0
                    yield EntropyRecord(psum, probability_sum, np.mean((intervals[interval_index][0], intervals[interval_index][1])),
                                        interval_probability=p)
                interval_index += 1
                continue
            index += 1

        if frequency > 0:
            p = frequency / len(audio)
            probability_sum += p
            total_processed += frequency
            psum -= p * math.log2(p)
            yield EntropyRecord(psum, probability_sum, np.mean((intervals[interval_index][0], intervals[interval_index][1])),
                                interval_probability=p)
        assert total_processed == len(audio), ("%d != %d" % (total_processed, len(audio)))
        assert probability_sum >= 1 - 1 / 10**7
        return psum

    def entropy_over_time(self, every_index, n=None, k=None):
        yield from itertools.islice(
            self._calculate_entropy(self.wave.data, n=n, k=k),
            0, None, every_index
        )

    def entropy(self, n=None, k=None):

        return no_yield(self._calculate_entropy)(self.wave.data, n=n, k=k)

    @property
    def spectrum(self) -> Spectrum:
        return Spectrum(wave=self)


class Spectrum:

    def __init__(self, wave: BaseSoundwave):
        self.wave = wave

    @cached_property
    def stft(self):
        return stft(self.wave.points, fs=self.wave.sample_rate, nperseg=1024)

    def amplitude_spectrum(self):
        fft_result = np.fft.fft(self.wave.points)
        amplitude_spectrum = np.abs(fft_result) / len(self.wave.points)
        frequencies = np.fft.fftfreq(len(self.wave.points), d=1 / self.wave.sample_rate)
        positive_indices = frequencies >= 0
        return frequencies[positive_indices], amplitude_spectrum[positive_indices]

    def phase_spectrum(self):
        *_, Zxx = self.stft
        return np.angle(Zxx)

    def spectrogram(self):
        *_, Zxx = self.stft
        return 10 * np.log10(np.abs(Zxx) ** 2 + 1e-10)





