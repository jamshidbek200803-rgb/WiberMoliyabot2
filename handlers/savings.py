from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from states.savings import SavingsState, GoalIntelState
from states.real_savings import RealSavingsState
from database.db_manager import Database
from keyboards.menu import main_menu, admin_verification_keyboard, account_mode_keyboard
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import ADMIN_ID, CARD_NUMBER, CARD_OWNER
from utils.price_tracker import get_current_price
from utils.i18n import get_text

router = Router()
db = Database("finance.db")

@router.message(F.text.in_(["🎯 Orzu Banki", "🎯 Копилка желаний", "🎯 Dream Bank"]))
async def show_savings_menu(message: types.Message):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    mode = db.get_user_mode(user_id)
    goals = db.get_goals(user_id)
    
    status_text = get_text('demo_mode_title' if mode == "demo" else 'real_mode_title', lang)
    
    if not goals:
        text = f"{status_text}\n\n{get_text('no_goals', lang)}"
    else:
        text = f"{status_text}\n{get_text('goals_title', lang)}\n\n"
        total_target = 0
        total_current = 0
        for goal in goals:
            percent = (goal[4] / goal[3]) * 100 if goal[3] > 0 else 0
            text += f"{goal[5]}. **{goal[2]}**\n"
            text += f"   - {get_text('goal_progress', lang)}: {goal[4]:,.0f} / {goal[3]:,.0f} {get_text('sum', lang)} ({percent:.1f}%)\n"
            total_target += goal[3]
            total_current += goal[4]
            
        text += f"\n**{get_text('total_goals_cost', lang)}:** {total_target:,.0f} {get_text('sum', lang)}\n"
        text += f"**{get_text('total_collected', lang)}:** {total_current:,.0f} {get_text('sum', lang)}"
        
        if mode == "real":
            real_bal = db.get_real_balance(user_id)
            text += f"\n\n💳 **{get_text('real_balance_title', lang)}:** {real_bal:,.0f} {get_text('sum', lang)}"

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text=get_text('btn_new_goal', lang), callback_data="add_goal"))
    if goals:
        builder.row(types.InlineKeyboardButton(text=get_text('btn_deposit', lang), callback_data="deposit_savings"))
        builder.row(types.InlineKeyboardButton(text=get_text('btn_goal_info', lang), callback_data="goal_intel"))
    
    if mode == "real":
        builder.row(types.InlineKeyboardButton(text=get_text('btn_withdraw', lang), callback_data="withdraw_real"))
    
    builder.row(types.InlineKeyboardButton(text=get_text('btn_change_mode', lang), callback_data="change_mode"))
    
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data == "change_mode")
async def start_change_mode(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    await callback.message.answer(get_text('select_mode', lang), reply_markup=account_mode_keyboard(lang))
    await callback.answer()

@router.callback_query(F.data.startswith("mode_"))
async def process_change_mode(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    mode = callback.data.split("_")[1]
    db.set_user_mode(user_id, mode)
    
    balance = db.get_real_balance(user_id)
    is_premium = db.is_user_premium(user_id)
    
    await callback.message.answer(
        f"{get_text('mode_changed', lang)}",
        parse_mode="Markdown",
        reply_markup=main_menu(lang, balance, is_premium)
    )
    await callback.answer()

# --- Goal Creation ---
@router.callback_query(F.data == "add_goal")
async def start_add_goal(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    await state.set_state(SavingsState.name)
    await state.update_data(lang=lang)
    await callback.message.answer(get_text('enter_goal_name', lang))
    await callback.answer()

@router.message(SavingsState.name)
async def process_goal_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    await state.update_data(name=message.text)
    await state.set_state(SavingsState.amount)
    await message.answer(f"'{message.text}' {get_text('enter_goal_price', lang)}")

@router.message(SavingsState.amount)
async def process_goal_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    if not message.text.isdigit():
        return await message.answer(get_text('invalid_amount', lang))
    await state.update_data(amount=float(message.text))
    await state.set_state(SavingsState.priority)
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.add(types.InlineKeyboardButton(text=str(i), callback_data=f"priority_{i}"))
    await message.answer(get_text('select_priority', lang), reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("priority_"))
async def process_priority(callback: types.CallbackQuery, state: FSMContext):
    priority = int(callback.data.split("_")[1])
    await state.update_data(priority=priority)
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    await state.set_state(SavingsState.url)
    await callback.message.edit_text(get_text('ask_goal_url', lang))
    await callback.answer()

@router.message(SavingsState.url)
async def process_goal_url(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    url = None if message.text.lower() in ["yo'q", "no", "нет"] else message.text
    await state.update_data(url=url)
    
    if url and "uzum.uz" in url:
        scraped_info = await get_current_price(url)
        if scraped_info:
            await state.update_data(
                scraped_color=scraped_info.get('color'),
                scraped_price=scraped_info.get('price')
            )
            msg = f"{get_text('scraped_uzum_info', lang)}\n"
            if scraped_info.get('color'): 
                msg += f"{get_text('color_label', lang)} {scraped_info['color']}\n"
            if scraped_info.get('price'): 
                msg += f"{get_text('price_label', lang)} {scraped_info['price']:,.0f} {get_text('sum', lang)}\n"
            await message.answer(msg)

    await state.set_state(SavingsState.color)
    await message.answer(get_text('ask_goal_color', lang))

@router.message(SavingsState.color)
async def process_goal_color(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    color_input = message.text.lower()
    
    color = None
    if color_input in ["ha", "yes", "da", "да"] and data.get('scraped_color'):
        color = data['scraped_color']
    elif color_input not in ["yo'q", "no", "нет"]:
        color = message.text

    db.add_goal(
        user_id=message.from_user.id, 
        name=data['name'], 
        target_amount=data['amount'], 
        priority=data['priority'], 
        item_url=data.get('url'),
        color=color
    )
    
    balance = db.get_real_balance(message.from_user.id)
    is_premium = db.is_user_premium(message.from_user.id)
    
    await state.clear()
    await message.answer(get_text('goal_added_full', lang, name=data['name']), reply_markup=main_menu(lang, balance, is_premium))

# --- Deposits ---
@router.callback_query(F.data == "deposit_savings")
async def start_deposit(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    mode = db.get_user_mode(user_id)
    await state.update_data(lang=lang)
    
    if mode == "demo":
        await state.set_state(SavingsState.deposit)
        await callback.message.answer(get_text('deposit_amount_ask', lang))
    else:
        await state.set_state(RealSavingsState.amount)
        await callback.message.answer(get_text('deposit_amount_ask', lang))
    await callback.answer()

@router.message(SavingsState.deposit)
async def process_demo_deposit(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    if not message.text.isdigit(): return await message.answer(get_text('invalid_amount', lang))
    amount = float(message.text)
    db.deposit_to_goal(message.from_user.id, amount)
    
    balance = db.get_real_balance(message.from_user.id)
    is_premium = db.is_user_premium(message.from_user.id)
    
    await message.answer(get_text('deposit_success_full', lang, amount=amount, unit=get_text('sum', lang)), reply_markup=main_menu(lang, balance, is_premium))
    await state.clear()

@router.message(RealSavingsState.amount)
async def process_real_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    if not message.text.isdigit(): return await message.answer(get_text('invalid_amount', lang))
    await state.update_data(amount=float(message.text))
    await state.set_state(RealSavingsState.receipt)
    await message.answer(
        f"{get_text('payment_info', lang)}\n\n"
        f"{get_text('btn_card', lang)}: `{CARD_NUMBER}`\n"
        f"{get_text('card_owner_label', lang) if 'card_owner_label' in get_text('all_keys', lang) else 'Ega'}: **{CARD_OWNER}**\n\n"
        f"{get_text('amount_label', lang)} {message.text} {get_text('sum', lang)}\n\n"
        f"{get_text('send_screenshot_label', lang)}",
        parse_mode="Markdown"
    )

@router.message(RealSavingsState.receipt, F.photo)
async def process_real_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    photo_id = message.photo[-1].file_id
    
    trans_id = db.add_transaction(
        user_id=message.from_user.id,
        amount=data['amount'],
        category_id=1, 
        t_type='income',
        comment="Real Savings Deposit",
        photo_id=photo_id,
        status='pending'
    )
    
    balance = db.get_real_balance(message.from_user.id)
    is_premium = db.is_user_premium(message.from_user.id)
    
    await state.clear()
    await message.answer(get_text('receipt_received', lang), reply_markup=main_menu(lang, balance, is_premium))
    
    try:
        await message.bot.send_photo(
            ADMIN_ID,
            photo_id,
            caption=f"🔔 **Yangi to'lov so'rovi!**\n\n"
                    f"Foydalanuvchi: {message.from_user.full_name} ({message.from_user.id})\n"
                    f"Summa: {data['amount']:,.0f} so'm",
            reply_markup=admin_verification_keyboard(trans_id), 
            parse_mode="Markdown"
        )
    except Exception: pass

# --- Withdrawals ---
@router.callback_query(F.data == "withdraw_real")
async def start_withdrawal(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    bal = db.get_real_balance(user_id)
    if bal <= 0:
        return await callback.answer(get_text('withdraw_no_funds', lang), show_alert=True)
    
    await state.set_state(RealSavingsState.withdrawal_amount)
    await state.update_data(lang=lang)
    await callback.message.answer(f"{get_text('withdraw_amount_ask', lang)} (Mavjud: {bal:,.0f} so'm):")
    await callback.answer()

@router.message(RealSavingsState.withdrawal_amount)
async def process_withdraw_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    if not message.text.isdigit(): return await message.answer(get_text('invalid_amount', lang))
    amount = float(message.text)
    bal = db.get_real_balance(message.from_user.id)
    
    if amount > bal:
        return await message.answer(get_text('insufficient_funds_full', lang, bal=bal, unit=get_text('sum', lang)))
        
    await state.update_data(amount=amount)
    await state.set_state(RealSavingsState.withdrawal_card)
    await message.answer(get_text('withdraw_card_ask', lang))

@router.message(RealSavingsState.withdrawal_card)
async def process_withdraw_card(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    card = message.text
    
    try:
        await message.bot.send_message(
            ADMIN_ID,
            f"🆘 **PUL YECHIB OLISH SO'ROVI!**\n\n"
            f"Foydalanuvchi: {message.from_user.full_name} ({message.from_user.id})\n"
            f"Summa: {data['amount']:,.0f} so'm\n"
            f"Karta: `{card}`",
            parse_mode="Markdown"
        )
        db.update_real_balance(message.from_user.id, -data['amount'])
        
        balance = db.get_real_balance(message.from_user.id)
        is_premium = db.is_user_premium(message.from_user.id)
        
        await message.answer(get_text('withdraw_request_sent', lang), reply_markup=main_menu(lang, balance, is_premium))
    except Exception:
        await message.answer(get_text('error_try_again', lang))
        
    await state.clear()

# --- Goal Intel ---
@router.callback_query(F.data == "goal_intel")
async def start_goal_intel(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    await state.set_state(GoalIntelState.priority)
    await state.update_data(lang=lang)
    await callback.message.answer(get_text('goal_intel_ask', lang))
    await callback.answer()

@router.message(GoalIntelState.priority)
async def process_goal_intel(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'uz')
    if not message.text.isdigit():
        return await message.answer(get_text('invalid_amount', lang))
    
    priority = int(message.text)
    goal = db.get_goal_by_priority(message.from_user.id, priority)
    
    if not goal:
        return await message.answer(get_text('goal_not_found', lang))

    name, target, current, prio, url, color, desc, last_price = goal
    sum_unit = get_text('sum', lang)
    
    if url:
        await message.answer(get_text('checking_market_prices', lang))
        scraped = await get_current_price(url)
        if scraped and scraped.get('price'):
            last_price = scraped['price']
            new_color = color if color else scraped.get('color')
            db.update_goal_intel(message.from_user.id, priority, color=new_color, last_price=last_price)
            color = new_color

    price_status = get_text('price_stable', lang)
    if last_price < target:
        diff = target - last_price
        price_status = f"{get_text('price_cheaper', lang)}\n" \
                       f"{get_text('target_label', lang)} {target:,.0f} {sum_unit}\n" \
                       f"{get_text('current_label', lang)} {last_price:,.0f} {sum_unit}\n" \
                       f"{get_text('diff_label', lang)} {diff:,.0f} {get_text('cheaper_label', lang)}."
    elif last_price > target:
        diff = last_price - target
        price_status = f"{get_text('price_expensive', lang)}\n" \
                       f"{get_text('target_label', lang)} {target:,.0f} {sum_unit}\n" \
                       f"{get_text('current_label', lang)} {last_price:,.0f} {sum_unit}\n" \
                       f"{get_text('diff_label', lang)} {diff:,.0f} {get_text('expensive_label', lang)}."
    
    text = f"{get_text('goal_intel_title', lang)} (ID: {prio})\n\n"
    text += f"📦 {name}\n"
    text += f"🎨 {color if color else '?'}\n"
    text += f"💰 {price_status}\n\n"
    
    progress = (current / target) * 100 if target > 0 else 0
    text += f"{get_text('progress_status', lang)} {current:,.0f} / {target:,.0f} ({progress:.1f}%)\n"
    
    if url:
        text += f"🔗 [{get_text('uzum_link', lang)}]({url})\n"
    
    balance = db.get_real_balance(message.from_user.id)
    is_premium = db.is_user_premium(message.from_user.id)

    await message.answer(text, parse_mode="Markdown", reply_markup=main_menu(lang, balance, is_premium))
    await state.clear()
