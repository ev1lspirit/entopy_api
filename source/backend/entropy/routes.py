import asyncio
import logging
from uuid import UUID

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.enums.parse_mode import ParseMode
from emoji import emojize as em

from source.app_state import get_app_state
from source.backend.entropy.string_templates import PhrasesWhileProcessing
from source.backend.entropy.utils import download_voice
from source.backend.states import EntropyCalculationStates
from source.celery.entropy_tasks import calculate_voice_entropy
from source.config import Config

router = Router(name="entropy")
logger = logging.getLogger(__name__)


@router.message(StateFilter(EntropyCalculationStates.calculating_entropy))
async def func(message: Message):
    await message.reply("Too busy calculating")


@router.message(StateFilter(None), F.voice)
async def voice_message_handler(message: Message, bot: Bot, state: FSMContext):

    if message.voice.duration > int(Config.MAX_VOICE_DURATION_LIMIT):
        await message.reply(text=f"{em(":cross_mark:")} Голосовое сообщение слишком длинное. Порог обработки ботом - 1 минута!")
        return

    app_state = get_app_state()
    file_meta = await bot.get_file(file_id=message.voice.file_id)
    await state.set_state(EntropyCalculationStates.calculating_entropy)
    replied_with: Message = await message.reply(
        text=f"{em(":microscope:")}<b>Производим анализ....</b>",
        parse_mode=ParseMode.HTML
    )
    data, sample_rate = await download_voice(file=file_meta, bot=bot)
    logger.info(f"Downloading a voice message {file_meta.file_size / 1000} kilobytes")

    await bot.send_chat_action(message.chat.id, action="typing")
    voice_id: UUID = await app_state.db.entropy_repository.upload_voice_to_db(
        sender_id=message.from_user.id,
        sender_username=message.from_user.username,
        sample_rate=sample_rate,
        vector=data
    )
    logger.info(f"Saved voice of {message.from_user.id} (username={message.from_user.username}) to the database.")
    task = calculate_voice_entropy.delay(voice_id)
    phrase_gen = PhrasesWhileProcessing.yield_phrase()

    while not task.ready():  # Check if task is still running
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        await replied_with.edit_text(
            text=next(phrase_gen),
            parse_mode=ParseMode.HTML
        )
        await asyncio.sleep(2)  # Wait before checking again
    await state.set_state(None)


