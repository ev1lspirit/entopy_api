from aiogram.fsm.state import StatesGroup, State


class EntropyCalculationStates(StatesGroup):
    calculating_entropy = State()