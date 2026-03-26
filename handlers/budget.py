from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from states.budget import BudgetState
from database.db_manager import Database
from keyboards.menu import category_keyboard, main_menu
from utils.i18n import get_text, get_cat_text

router = Router()
db = Database("finance.db")

@router.message(F.text.in_(["📉 Limitlar", "📉 Лимиты", "📉 Limits"]))
async def show_budget_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    categories = db.get_categories("expense")
    await state.set_state(BudgetState.category)
    await state.update_data(lang=lang)
    await message.answer(get_text('budget_select_cat', lang), reply_markup=category_keyboard(categories, lang))

@router.callback_query(BudgetState.category, F.data.startswith("cat_"))
async def process_budget_category(callback: types.CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split("_")[1])
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    
    # Find category name for display
    categories = db.get_categories("expense")
    cat_name = next((c[1] for c in categories if c[0] == cat_id), get_text('unknown_category', lang))
    
    await state.update_data(category_id=cat_id, category_name=cat_name)
    await state.set_state(BudgetState.amount)
    await callback.message.edit_text(f"'{cat_name}' {get_text('budget_enter_amount', lang)}")
    await callback.answer()

@router.message(BudgetState.amount)
async def process_budget_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    
    if not message.text.isdigit():
        return await message.answer(get_text('invalid_amount', lang))
    
    amount = float(message.text)
    user_id = message.from_user.id
    
    db.set_budget(
        user_id=user_id,
        category_id=data['category_id'],
        amount=amount
    )
    
    balance = db.get_real_balance(user_id)
    is_premium = db.is_user_premium(user_id)
    
    await state.clear()
    await message.answer(
        f"✅ {get_text('budget_set_success', lang)} {get_cat_text(data['category_name'], lang)}: {amount:,} {get_text('sum', lang)}",
        reply_markup=main_menu(lang, balance, is_premium)
    )
