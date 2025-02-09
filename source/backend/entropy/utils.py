import io
import logging
import os
import tempfile
from typing import Optional, BinaryIO

import librosa
import numpy as np
import scipy.io.wavfile as wav
import soundfile as sf
from aiogram import Bot
from aiogram.types import Voice, File

from source.app_state import get_app_state
from source.config import Config

logger = logging.getLogger(__name__)


async def download_voice(bot: Bot, file: File) -> tuple[np.ndarray, int]:
    file_buffer = io.BytesIO()
    await bot.download_file(file_path=file.file_path, destination=file_buffer)
    file_buffer.seek(0)
    return sf.read(file_buffer)

    # with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
    #     tmp.write(file_buffer.getbuffer())
    #     tmp.flush()
    #     # Read WAV using scipy
    #     samplerate, data = wav.read(tmp.name)
    #
    # os.unlink(tmp.name)
    # data = np.transpose(data)
    # if data.ndim > 1:
    #     data = data[0]
    # return (data / 32767), samplerate
