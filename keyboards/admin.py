from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.i18n import get_text

def admin_verification_keyboard(user_id):
    kb = [
        [
            InlineKeyboardButton(text=get_text('btn_approve', 'uz'), callback_data=f"premium_approve_{user_id}"),
            InlineKeyboardButton(text=get_text('btn_reject', 'uz'), callback_data=f"premium_reject_{user_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
