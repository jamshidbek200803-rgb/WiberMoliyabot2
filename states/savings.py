from aiogram.fsm.state import State, StatesGroup

class SavingsState(StatesGroup):
    name = State()
    amount = State()
    priority = State()
    url = State()
    color = State()
    deposit = State()

class GoalIntelState(StatesGroup):
    priority = State()
