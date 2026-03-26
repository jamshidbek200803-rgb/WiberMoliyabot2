from aiogram.fsm.state import State, StatesGroup

class AdminState(StatesGroup):
    broadcast_msg = State()
    manage_user = State()
    add_cat_name = State()
    add_cat_type = State()
    del_cat_id = State()
    add_admin_id = State()
    del_admin_id = State()
    audit_user_id = State()

class AdState(StatesGroup):
    waiting_for_has_photo = State()
    waiting_for_photo = State()
    waiting_for_text = State()
    waiting_for_details = State()
    waiting_for_duration = State()
    waiting_for_confirmation = State()

class AdHistoryState(StatesGroup):
    view_history = State()
    ask_edit = State()
    choose_edit_part = State()
    edit_photo = State()
    edit_text = State()
    edit_details = State()
    waiting_for_duration = State()

