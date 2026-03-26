from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database.db_manager import Database
from utils.i18n import get_text
from aiogram.fsm.state import State, StatesGroup

router = Router()
db = Database("finance.db")

class FeedbackState(StatesGroup):
    waiting_for_msg = State()

@router.message(Command("feedback"))
async def feedback_start(message: types.Message, state: FSMContext):
    lang = db.get_user_language(message.from_user.id)
    await state.set_state(FeedbackState.waiting_for_msg)
    await message.answer(get_text('feedback_ask', lang))

@router.message(FeedbackState.waiting_for_msg)
async def process_feedback(message: types.Message, state: FSMContext):
    lang = db.get_user_language(message.from_user.id)
    db.add_feedback(message.from_user.id, message.text)
    await state.clear()
    await message.answer(get_text('feedback_received', lang))
    
    # Notify super admin
    from config import ADMIN_ID
    try:
        await message.bot.send_message(
            ADMIN_ID, 
            f"📬 **Yangi feedback!**\nFoydalanuvchi: {message.from_user.full_name}\nID: `{message.from_user.id}`\n\n{message.text}",
            parse_mode="Markdown"
        )
    except Exception: pass
