import asyncio
import io
import logging
import pickle
from typing import Optional

import numpy as np
from aiogram import Router, F, Bot
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, File, InputFile, BufferedInputFile
from celery.result import AsyncResult
from emoji import emojize as em
from matplotlib import pyplot as plt

from source.app_state import get_app_state
from source.backend.entropy.string_templates import PhrasesWhileProcessing
from source.backend.entropy.utils import download_voice
from source.backend.states import EntropyCalculationStates
from source.celery.entropy_tasks import preprocess_voice, calculate_voice_entropy
from source.celery.helpers import get_vector_from_redis
from source.config import Config
from source.entropy_finder.entro import FilteredSoundwave

router = Router(name="entropy")
logger = logging.getLogger(__name__)


@router.message(StateFilter(EntropyCalculationStates.calculating_entropy))
async def func(message: Message):
    await message.reply("Too busy calculating")


def run_voice_preprocessing(*, file_meta: File, data: np.ndarray, sample_rate: int):
    app_state = get_app_state()
    samplerate_redis_key = f"samplerate:{file_meta.file_id}"
    app_state.redis_app.set(name=file_meta.file_id,
                            value=pickle.dumps(data))
    app_state.redis_app.set(name=samplerate_redis_key, value=sample_rate)
    task_result = preprocess_voice.delay(file_meta.file_id, samplerate_redis_key)
    return task_result


async def voice_file_handler(message: Message, bot: Bot, *, file_id: str) -> Optional[AsyncResult]:
    app_state = get_app_state()
    file_meta = await bot.get_file(file_id=file_id)
    data, sample_rate = await download_voice(file=file_meta, bot=bot)
    logger.info(f"Downloading a voice message of size {file_meta.file_size / 1000} kilobytes")

    await bot.send_chat_action(message.chat.id, action="typing")
    voice_id: str = await app_state.db.entropy_repository.check_if_sample_exists(
        voice_id=file_meta.file_id
    )

    if voice_id:
        logger.info(f"Voice already exists in the database: id={voice_id}")
        return

    result = run_voice_preprocessing(file_meta=file_meta, data=data, sample_rate=sample_rate)
    logger.info(f"Preprocessing the voice of {message.from_user.id} (username={message.from_user.username})...")
    return result


@router.message(StateFilter(None), F.voice)
@router.message(StateFilter(None),
                ((F.forward_from | F.forward_sender_chat) & F.document.file_name.endswith(".wav")))
@router.message(StateFilter(None), F.document.file_name.endswith(".wav"))
@router.message(StateFilter(None),
        ((F.forward_from | F.forward_sender_chat) & F.voice))
async def voice_message_handler(message: Message, bot: Bot, state: FSMContext):
    if message.voice:
        if message.voice.duration > int(Config.MAX_VOICE_DURATION_LIMIT):
            logger.info(f"Voice message is too long. Duration: {message.voice.duration}")
            await message.reply(text=f"{em(":cross_mark:")} Голосовое сообщение слишком длинное. Порог обработки ботом - 1 минута!")
            return
        voice_sample = message.voice
    elif message.document:
        if message.document.file_size > int(Config.MAX_FILE_SIZE):
            logger.info(f"Voice message is too big. Size: {message.document.file_size} bytes")
            await message.reply(
                text=f"{em(":cross_mark:")} Документ слишком большой. Порог обработки ботом - до 10 мб!")
            return
        voice_sample = message.document
    else:
        raise ValueError("Unexpected error occurred! Neither voice nor document were received.")

    await message.reply(f"id: {voice_sample.file_id}")
    await state.set_state(EntropyCalculationStates.calculating_entropy)
    waiting_message: Message = await message.reply(
        text=f"{em(":microscope:")}<b>Выполняем обработку сигнала c id {voice_sample.file_id}....</b>",
        parse_mode=ParseMode.HTML
    )
    preprocessing_task_result = await voice_file_handler(message=message, bot=bot, file_id=voice_sample.file_id)
    phrase_gen = PhrasesWhileProcessing.yield_phrase()

    if preprocessing_task_result is not None:
        while not preprocessing_task_result.ready():
            await bot.send_chat_action(chat_id=message.chat.id, action="typing")
            await waiting_message.edit_text(
                         text=next(phrase_gen),
                         parse_mode=ParseMode.HTML)
            await asyncio.sleep(3)

        if preprocessing_task_result.failed():
            logger.info(f"Preprocessing celery task has failed. Reason: {preprocessing_task_result.traceback}")
            await message.reply(
                "Упс! Кажется, что-то пошло не так. Свяжитесь с администрацией для устранения проблемы."
            )
            await state.clear()
            return

    logger.info(f"Starting entropy calculation task for file with id={voice_sample.file_id}")
    entropy_task: AsyncResult = calculate_voice_entropy.delay(voice_sample.file_id, f"samplerate:{voice_sample.file_id}")

    while not entropy_task.ready():
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        await waiting_message.edit_text(
            text=next(phrase_gen),
            parse_mode=ParseMode.HTML)
        await asyncio.sleep(3)

    if entropy_task.failed():
        logger.info(f"Calculating entropy celery task has failed. Reason: {preprocessing_task_result.traceback}")
        await message.reply(
            "Упс! Кажется, что-то пошло не так. Свяжитесь с администрацией для устранения проблемы."
        )
    else:
        buffer = io.BytesIO()
        hist, entropy = entropy_task.get()
        x, y = zip(*hist)
        plt.figure(figsize=(8, 7))
        plt.plot(y, x, marker='.')
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        buffer.seek(0)
        await message.reply_photo(
            caption=f"Значение энтропии: {entropy}",
            photo=BufferedInputFile(file=buffer.getvalue(), filename="plot.png")
        )

    # wave = get_vector_from_redis(sample_rate_key=f'samplerate:{voice_sample.file_id}', vector_key=voice_sample.file_id)
    # soundwave = FilteredSoundwave(wave)
    #
    # plt.plot(soundwave.points)
    # logger.info(soundwave.entropy(n=100000, k=50000))
    # plt.show()
    await state.clear()


