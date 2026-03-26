from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from database.db_manager import Database
from states.subscriptions import SubscriptionState
from utils.i18n import get_text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()
db = Database("finance.db")

@router.message(F.text.in_(["📋 Obunalar", "📋 Подписки", "📋 Subscriptions"]))
async def show_subscriptions(message: types.Message):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    
    if not db.is_user_premium(user_id):
        await message.answer(get_text('alert_premium_required', lang))
        return

    subs = db.get_subscriptions(user_id)
    text = f"{get_text('sub_title', lang)}\n\n"
    
    if not subs:
        text += get_text('no_subscriptions', lang)
    else:
        for sub_id, name, amount, cycle, next_date in subs:
            cycle_text = get_text('btn_monthly' if cycle == 'monthly' else 'btn_yearly', lang)
            text += f"🔹 **{name}**: {amount:,} {get_text('sum', lang)} ({cycle_text})\n"
            text += f"   ID: /del_sub_{sub_id}\n\n"

    kb = [[InlineKeyboardButton(text=get_text('btn_add_sub', lang), callback_data="add_sub")]]
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@router.callback_query(F.data == "add_sub")
async def add_sub_start(callback: types.CallbackQuery, state: FSMContext):
    lang = db.get_user_language(callback.from_user.id)
    await callback.message.answer(get_text('ask_sub_name', lang))
    await state.set_state(SubscriptionState.waiting_for_name)
    await callback.answer()

@router.message(SubscriptionState.waiting_for_name)
async def process_sub_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    lang = db.get_user_language(message.from_user.id)
    await message.answer(get_text('ask_sub_amount', lang))
    await state.set_state(SubscriptionState.waiting_for_amount)

@router.message(SubscriptionState.waiting_for_amount)
async def process_sub_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        lang = db.get_user_language(message.from_user.id)
        return await message.answer(get_text('invalid_amount', lang))
    
    await state.update_data(amount=float(message.text))
    lang = db.get_user_language(message.from_user.id)
    
    kb = [
        [InlineKeyboardButton(text=get_text('btn_monthly', lang), callback_data="cycle_monthly")],
        [InlineKeyboardButton(text=get_text('btn_yearly', lang), callback_data="cycle_yearly")]
    ]
    await message.answer(get_text('ask_sub_cycle', lang), reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await state.set_state(SubscriptionState.waiting_for_cycle)

@router.callback_query(SubscriptionState.waiting_for_cycle, F.data.startswith("cycle_"))
async def process_sub_cycle(callback: types.CallbackQuery, state: FSMContext):
    cycle = callback.data.split("_")[1]
    data = await state.get_data()
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    
    db.add_subscription(user_id, data['name'], data['amount'], cycle)
    
    await callback.message.answer(get_text('sub_saved', lang))
    await state.clear()
    await show_subscriptions(callback.message)
    await callback.answer()

@router.message(F.text.startswith("/del_sub_"))
async def delete_sub(message: types.Message):
    sub_id = int(message.text.split("_")[2])
    db.delete_subscription(sub_id)
    lang = db.get_user_language(message.from_user.id)
    await message.answer("✅ Obuna o'chirildi.")
    await show_subscriptions(message)
