import logging
from typing import Optional, BinaryIO

import numpy as np
from aiogram import Bot
from aiogram.types import Voice, File
import io
import soundfile as sf
import wave

from pydub import AudioSegment
from pydub.utils import mediainfo

logger = logging.getLogger(__name__)


async def download_voice(bot: Bot, file: File) -> tuple[np.ndarray, int]:
    file_buffer = io.BytesIO()
    await bot.download_file(file_path=file.file_path, destination=file_buffer, seek=True)
    return sf.read(file_buffer)



async def save_voice_to_db(bot: Bot, file: Voice) -> Optional[BinaryIO]:
    pass

