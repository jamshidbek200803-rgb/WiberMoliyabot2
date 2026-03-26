from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from database.db_manager import Database
from states.debts import DebtState
from keyboards.menu import main_menu
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.i18n import get_text

router = Router()
db = Database("finance.db")

@router.message(F.text.in_(["💸 Qarzlar", "💸 Долги", "💸 Debts"]))
async def show_debts(message: types.Message):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    
    if not db.is_user_premium(user_id):
        return await message.answer(
            get_text('debts_premium_required', lang),
            parse_mode="Markdown"
        )
    
    debts = db.get_debts(user_id)
    text = f"{get_text('debts_title', lang)}\n\n"
    
    if not debts:
        text += get_text('no_debts', lang)
    else:
        for d_id, name, amount, d_type, due in debts:
            icon = "🔴" if d_type == "borrowed" else "🟢"
            type_text = get_text('type_borrowed_label' if d_type == "borrowed" else 'type_lent_label', lang)
            text += f"{icon} <b>{name}</b>: {amount:,.0f} {get_text('sum', lang)}\n"
            text += f"   - {get_text('category', lang)}: {type_text}\n"
            if due: text += f"   - {get_text('debt_due_label', lang)}: {due}\n"
            text += f"   - {get_text('btn_pay', lang)}: /pay{d_id}\n\n"
            
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text=get_text('btn_add_debt', lang), callback_data="add_debt"))
    
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data == "add_debt")
async def start_add_debt(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    await state.set_state(DebtState.name)
    await state.update_data(lang=lang)
    await callback.message.answer(get_text('ask_debt_name', lang))
    await callback.answer()

@router.message(DebtState.name)
async def process_debt_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    await state.update_data(name=message.text)
    await state.set_state(DebtState.amount)
    await message.answer(f"'{message.text}' {get_text('ask_debt_amount', lang)}")

@router.message(DebtState.amount)
async def process_debt_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    if not message.text.isdigit():
        return await message.answer(get_text('invalid_amount', lang))
    
    await state.update_data(amount=float(message.text))
    await state.set_state(DebtState.type)
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text=get_text('btn_dtype_borrowed', lang), callback_data="dtype_borrowed"))
    builder.add(types.InlineKeyboardButton(text=get_text('btn_dtype_lent', lang), callback_data="dtype_lent"))
    
    await message.answer(get_text('ask_debt_type', lang), reply_markup=builder.as_markup())

@router.callback_query(DebtState.type, F.data.startswith("dtype_"))
async def process_debt_type(callback: types.CallbackQuery, state: FSMContext):
    d_type = callback.data.split("_")[1]
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    await state.update_data(type=d_type)
    await state.set_state(DebtState.due_date)
    await callback.message.edit_text(get_text('ask_debt_due', lang))
    await callback.answer()

@router.message(DebtState.due_date)
async def process_debt_due(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    due = None if message.text.lower() in ["yo'q", "no", "нет"] else message.text
    
    db.add_debt(
        user_id=message.from_user.id,
        name=data['name'],
        amount=data['amount'],
        debt_type=data['type'],
        due_date=due
    )
    
    balance = db.get_real_balance(message.from_user.id)
    is_premium = db.is_user_premium(message.from_user.id)
    
    await state.clear()
    await message.answer(get_text('debt_saved', lang), reply_markup=main_menu(lang, balance, is_premium))

@router.message(F.text.startswith("/pay"))
async def mark_paid_handler(message: types.Message):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    
    if not db.is_user_premium(user_id):
        return
        
    try:
        debt_id = int(message.text.replace("/pay", ""))
        db.mark_debt_paid(debt_id)
        await message.answer(get_text('debt_paid_success', lang))
    except Exception:
        await message.answer(get_text('debt_invalid_id', lang))
