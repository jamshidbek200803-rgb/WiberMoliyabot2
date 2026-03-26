from aiogram.fsm.state import State, StatesGroup

class DebtState(StatesGroup):
    name = State()
    amount = State()
    type = State()
    due_date = State()
