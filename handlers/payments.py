from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database.db_manager import Database
from config import ADMIN_ID, CARD_NUMBER, CARD_OWNER, PRICE_PREMIUM
from states.premium import PremiumState
from keyboards.admin import admin_verification_keyboard
from keyboards.menu import main_menu
from utils.i18n import get_text

router = Router()
db = Database("finance.db")

@router.callback_query(F.data == "buy_premium")
async def start_premium_buy(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    
    if db.is_user_premium(user_id):
        return await callback.answer(get_text('premium_already_active', lang), show_alert=True)

    text = (
        f"{get_text('premium_benefits', lang)}\n\n"
        f"💰 **{get_text('premium_price_label', lang)}:** {PRICE_PREMIUM} {get_text('sum', lang)} (30 {get_text('days', lang)})\n\n"
        f"💳 **{get_text('payment_info', lang)}:**\n"
        f"`{CARD_NUMBER}`\n"
        f"👤 **Egasi:** {CARD_OWNER}\n\n"
        f"{get_text('premium_receipt_instruction', lang)}"
    )
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(PremiumState.waiting_for_receipt)
    await state.update_data(lang=lang)
    
    # Add cancel button
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text('premium_cancel_btn', lang), callback_data="cancel_premium")]
    ])
    await callback.message.edit_reply_markup(reply_markup=kb)

@router.message(PremiumState.waiting_for_receipt, F.photo)
async def process_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    photo = message.photo[-1].file_id
    user = message.from_user
    
    if ADMIN_ID:
        try:
            await message.bot.send_photo(
                chat_id=int(ADMIN_ID),
                photo=photo,
                caption=(
                    f"🆕 **Yangi Premium so'rovi!**\n\n"
                    f"👤 **Foydalanuvchi:** {user.full_name} (@{user.username})\n"
                    f"🆔 **ID:** `{user.id}`"
                ),
                parse_mode="Markdown",
                reply_markup=admin_verification_keyboard(user.id)
            )
            
            balance = db.get_real_balance(user.id)
            is_premium = db.is_user_premium(user.id)
            
            await message.answer(get_text('premium_request_received', lang), reply_markup=main_menu(lang, balance, is_premium))
        except Exception:
            await message.answer("Error sending to admin. Please contact support.")
    
    await state.clear()

@router.callback_query(F.data.startswith("premium_approve_"))
async def approve_premium(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    lang = db.get_user_language(user_id)
    db.set_premium(user_id, duration_days=30)
    
    try:
        await callback.bot.send_message(
            user_id,
            f"✅ **{get_text('success', lang)}!**\n\n{get_text('premium_already_active', lang)}",
            parse_mode="Markdown"
        )
    except Exception: pass

    await callback.message.edit_caption(caption=callback.message.caption + f"\n\n✅ **{get_text('admin_approve_success', 'uz')}!**")
    await callback.answer("Premium tasdiqlandi")

@router.callback_query(F.data.startswith("premium_reject_"))
async def reject_premium(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    lang = db.get_user_language(user_id)
    
    # Kiritilgan chekni bekor qilish (rad etish) sonini oshiramiz
    count = db.increment_premium_cancel_count(user_id)
    
    if count >= 3:
        # Foydalanuvchini 3 kunga bloklaymiz
        db.set_premium_block(user_id, days=3)
        db.reset_premium_cancel_count(user_id)
        
        from datetime import datetime, timedelta
        until_date = (datetime.now() + timedelta(days=3)).strftime('%d.%m.%Y %H:%M')
        try:
            await callback.bot.send_message(
                user_id,
                get_text('premium_blocked_msg', lang, date=until_date),
                parse_mode="Markdown"
            )
        except Exception: pass
        
        await callback.message.edit_caption(caption=callback.message.caption + f"\n\n🚫 **FOYDALANUVCHI 3 KUNGA BLOKLANDI!**")
    else:
        try:
            await callback.bot.send_message(
                user_id,
                f"❌ **{get_text('admin_reject_success', lang)}**",
                parse_mode="Markdown"
            )
        except Exception: pass
        await callback.message.edit_caption(caption=callback.message.caption + f"\n\n❌ **{get_text('admin_reject_success', 'uz')}!**")
        
    await callback.answer("Rad etildi")

@router.callback_query(F.data == "cancel_premium")
async def cancel_premium(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    
    await state.clear()
    
    # Simple cancel without block
    balance = db.get_real_balance(user_id)
    is_premium = db.is_user_premium(user_id)
    await callback.message.edit_text(get_text('premium_cancel_success', lang))
    await callback.message.answer(get_text('welcome', lang, name=callback.from_user.full_name), reply_markup=main_menu(lang, balance, is_premium))
    
    await callback.answer()
