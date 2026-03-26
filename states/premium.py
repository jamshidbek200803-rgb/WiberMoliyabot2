from aiogram.fsm.state import State, StatesGroup

class PremiumState(StatesGroup):
    waiting_for_receipt = State()
