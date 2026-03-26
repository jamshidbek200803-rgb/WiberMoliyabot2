from aiogram.fsm.state import State, StatesGroup

class BudgetState(StatesGroup):
    category = State()
    amount = State()
