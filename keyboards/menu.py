from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from utils.i18n import get_text, get_cat_text

def main_menu(lang='uz', balance=0, is_premium=False):
    kb = [
        [KeyboardButton(text=get_text('menu_income', lang)), KeyboardButton(text=get_text('menu_expense', lang))],
        [KeyboardButton(text=get_text('menu_goals', lang)), KeyboardButton(text=get_text('menu_stats', lang))],
        [KeyboardButton(text=get_text('menu_limits', lang)), KeyboardButton(text=get_text('menu_debts', lang))],
        [KeyboardButton(text=get_text('menu_currency', lang)), KeyboardButton(text=get_text('menu_advice', lang))],
        [KeyboardButton(text=get_text('menu_family', lang)), KeyboardButton(text=get_text('menu_subscriptions', lang))],
        [KeyboardButton(text=get_text('menu_chat', lang)), KeyboardButton(text=get_text('menu_settings', lang))]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def category_keyboard(categories, lang='uz'):
    kb = []
    row = []
    for cat_id, name in categories:
        row.append(InlineKeyboardButton(text=get_cat_text(name, lang), callback_data=f"cat_{cat_id}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    kb.append([InlineKeyboardButton(text=get_text('btn_cancel', lang), callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def settings_keyboard(lang='uz'):
    kb = [
        [InlineKeyboardButton(text=get_text('settings_lang', lang), callback_data="set_lang")],
        [InlineKeyboardButton(text=get_text('settings_pin', lang), callback_data="set_pin")],
        [InlineKeyboardButton(text=get_text('settings_premium', lang), callback_data="buy_premium")],
        [InlineKeyboardButton(text=get_text('settings_back', lang), callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def language_keyboard(lang='uz'):
    kb = [
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton(text=get_text('settings_back', lang), callback_data="back_settings")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def account_mode_keyboard(lang='uz'):
    kb = [
        [InlineKeyboardButton(text=get_text('btn_demo', lang), callback_data="mode_demo")],
        [InlineKeyboardButton(text=get_text('btn_real', lang), callback_data="mode_real")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_verification_keyboard(transaction_id, lang='uz'):
    kb = [
        [
            InlineKeyboardButton(text=get_text('btn_approve', lang), callback_data=f"approve_{transaction_id}"),
            InlineKeyboardButton(text=get_text('btn_reject', lang), callback_data=f"reject_{transaction_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def support_keyboard(lang='uz'):
    kb = [
        [InlineKeyboardButton(text=get_text('sup_premium_btn', lang), callback_data="sup_premium")],
        [InlineKeyboardButton(text=get_text('sup_payment_btn', lang), callback_data="sup_payment")],
        [InlineKeyboardButton(text=get_text('sup_balance_btn', lang), callback_data="sup_balance")],
        [InlineKeyboardButton(text=get_text('sup_admin_btn', lang), callback_data="sup_admin")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

