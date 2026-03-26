from aiogram.fsm.state import State, StatesGroup

class Transaction(StatesGroup):
    type = State()
    amount = State()
    category = State()
    comment = State()
