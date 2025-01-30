from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message
from source.celery.entropy_tasks import celery_task


router = Router(name="entropy")


@router.message(StateFilter(None), F.voice)
async def voice_message_handler(message: Message):
    await message.reply("voice received")
    celery_task.delay()
