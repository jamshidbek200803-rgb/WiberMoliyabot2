from aiogram.fsm.state import State, StatesGroup

class FamilyState(StatesGroup):
    name = State()
    join_code = State()
