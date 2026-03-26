from aiogram.fsm.state import State, StatesGroup

class RealSavingsState(StatesGroup):
    amount = State()
    receipt = State()
    withdrawal_amount = State()
    withdrawal_card = State()
