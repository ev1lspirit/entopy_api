from aiogram import Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message
from aiogram.enums.parse_mode import ParseMode

router = Router(name="main")


@router.message(CommandStart(), StateFilter(None))
async def start_handler(message: Message):
    await message.reply(
        text=
"""<b>Добро пожаловать!</b> 
EntroPie - это бот, производящий расчёт энтропии аудиосигнала и прогнозирующий вероятность того, синтезирован ли голос DL-моделями.

<i>Данный бот является дипломным проектом @sweetferrero</i>
<b>Стек:</b> 
  <i>Research</i>: Python, scipy, numpy
  <i>Backend</i>: Python, aiogram, celery, PostgreSQL, Docker, Redis
  <i>Backend LLM</i>: DeepSeek R1
""",
        parse_mode=ParseMode.HTML
    )
