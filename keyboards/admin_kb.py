from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.i18n import get_text

def admin_menu_keyboard(lang='uz', is_maintenance=False):
    status_text = get_text('maintenance_on' if is_maintenance else 'maintenance_off', lang)
    kb = [
        [InlineKeyboardButton(text=get_text('admin_stats', lang), callback_data="admin_stats")],
        [InlineKeyboardButton(text=get_text('admin_broadcast', lang), callback_data="admin_broadcast")],
        [InlineKeyboardButton(text=get_text('admin_users', lang), callback_data="admin_users")],
        [InlineKeyboardButton(text=get_text('admin_maintenance', lang, status=status_text), callback_data="admin_maintenance")],
        [InlineKeyboardButton(text=get_text('admin_export', lang), callback_data="admin_export")],
        [InlineKeyboardButton(text=get_text('admin_categories', lang), callback_data="admin_categories")],
        [InlineKeyboardButton(text=get_text('admin_feedback', lang), callback_data="admin_feedback")],
        [InlineKeyboardButton(text=get_text('admin_admins', lang), callback_data="admin_admins")],
        [InlineKeyboardButton(text=get_text('admin_ads', lang), callback_data="admin_ads"),
         InlineKeyboardButton(text=get_text('admin_ads_history', lang), callback_data="admin_ads_history")],
        [InlineKeyboardButton(text=get_text('btn_back', lang), callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_user_action_keyboard(user_id, is_premium, is_banned, lang='uz'):
    premium_btn_text = get_text('btn_take_premium', lang) if is_premium else get_text('btn_give_premium', lang)
    block_btn_text = get_text('btn_unblock', lang) if is_banned else get_text('btn_block', lang)
    
    kb = [
        [InlineKeyboardButton(text=premium_btn_text, callback_data=f"adm_premium_{user_id}_{0 if is_premium else 1}")],
        [InlineKeyboardButton(text=block_btn_text, callback_data=f"adm_ban_{user_id}_{0 if is_banned else 1}")],
        [InlineKeyboardButton(text=get_text('btn_back', lang), callback_data="admin_users")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
