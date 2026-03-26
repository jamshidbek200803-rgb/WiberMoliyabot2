from aiogram.fsm.state import State, StatesGroup

class PinState(StatesGroup):
    enter_new_pin = State()
    confirm_new_pin = State()
    check_pin = State()
