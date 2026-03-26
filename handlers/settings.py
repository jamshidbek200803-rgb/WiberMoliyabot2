from aiogram import Router, F, types
from keyboards.menu import settings_keyboard, language_keyboard, main_menu
from database.db_manager import Database
from utils.i18n import get_text

router = Router()
db = Database("finance.db")

@router.message(F.text.in_(["⚙️ Sozlamalar", "⚙️ Настройки", "⚙️ Settings"]))
async def show_settings(message: types.Message):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    await message.answer(
        get_text('settings_title', lang),
        reply_markup=settings_keyboard(lang),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "set_lang")
async def show_languages(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    await callback.message.edit_text(
        get_text('lang_select', lang),
        reply_markup=language_keyboard(lang),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("lang_"))
async def process_language(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang_code = callback.data.split("_")[1]
    
    db.set_user_language(user_id, lang_code)
    
    # Refresh stats for keyboards
    balance = db.get_real_balance(user_id)
    is_premium = db.is_user_premium(user_id)
    
    await callback.answer(get_text('lang_changed', lang_code))
    await callback.message.answer(
        get_text('welcome', lang_code, name=callback.from_user.full_name),
        reply_markup=main_menu(lang_code, balance, is_premium),
        parse_mode="HTML"
    )
    await callback.message.delete()

@router.callback_query(F.data == "back_settings")
async def back_to_settings(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    await callback.message.edit_text(
        get_text('settings_title', lang),
        reply_markup=settings_keyboard(lang),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "back_to_menu")
async def back_to_main_menu_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    balance = db.get_real_balance(user_id)
    is_premium = db.is_user_premium(user_id)
    
    await callback.message.delete()
    await callback.message.answer(
        get_text('welcome', lang, name=callback.from_user.full_name),
        reply_markup=main_menu(lang, balance, is_premium),
        parse_mode="HTML"
    )
    await callback.answer()
