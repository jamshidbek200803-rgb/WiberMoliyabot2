from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from states.transaction import Transaction
from database.db_manager import Database
from keyboards.menu import category_keyboard, main_menu
from utils.i18n import get_text

router = Router()
db = Database("finance.db")

@router.message(F.text.in_(["📥 Kirim", "📥 Доход", "📥 Income"]))
async def start_income(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    await state.set_state(Transaction.type)
    await state.update_data(type="income", lang=lang)
    await state.set_state(Transaction.amount)
    await message.answer(get_text('enter_amount', lang))

@router.message(F.text.in_(["📤 Chiqim", "📤 Расход", "📤 Expense"]))
async def start_expense(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    await state.set_state(Transaction.type)
    await state.update_data(type="expense", lang=lang)
    await state.set_state(Transaction.amount)
    await message.answer(get_text('enter_amount', lang))

@router.message(Transaction.amount)
async def process_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    
    if not message.text.isdigit():
        return await message.answer(get_text('invalid_amount', lang))
    
    await state.update_data(amount=float(message.text))
    categories = db.get_categories(data['type'])
    
    await state.set_state(Transaction.category)
    await message.answer(get_text('select_category', lang), reply_markup=category_keyboard(categories, lang))

@router.callback_query(Transaction.category, F.data.startswith("cat_"))
async def process_category(callback: types.CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split("_")[1])
    await state.update_data(category_id=cat_id)
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    
    await state.set_state(Transaction.comment)
    await callback.message.edit_text(get_text('enter_comment', lang))

@router.message(Transaction.comment)
async def process_comment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    
    triggers = get_text('no_comment_triggers', lang)
    comment = None if message.text.lower() in triggers else message.text
    
    db.add_transaction(
        user_id=message.from_user.id,
        amount=data['amount'],
        category_id=data['category_id'],
        t_type=data['type'],
        comment=comment
    )
    
    balance = db.get_real_balance(message.from_user.id)
    is_premium = db.is_user_premium(message.from_user.id)
    
    await state.clear()
    await message.answer(get_text('saved_successfully', lang), reply_markup=main_menu(lang, balance, is_premium))

    if data['type'] == 'expense':
        budget_status = db.get_budget_status(message.from_user.id, data['category_id'])
        if budget_status and budget_status[0]:
            limit_amount, current_total = budget_status
            if current_total >= limit_amount:
                await message.answer(get_text('budget_warning_100', lang, target=limit_amount, current=current_total), parse_mode="Markdown")
            elif current_total >= limit_amount * 0.8:
                await message.answer(get_text('budget_warning_80', lang, target=limit_amount, current=current_total), parse_mode="Markdown")

@router.callback_query(F.data == "cancel")
async def cancel_handler(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    balance = db.get_real_balance(user_id)
    is_premium = db.is_user_premium(user_id)
    
    await state.clear()
    await callback.message.edit_text(get_text('action_cancelled', lang))
    await callback.message.answer(get_text('main_menu_label', lang), reply_markup=main_menu(lang, balance, is_premium))
