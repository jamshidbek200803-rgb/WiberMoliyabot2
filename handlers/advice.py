import random
from aiogram import Router, F, types
from database.db_manager import Database
from utils.i18n import get_text

router = Router()
db = Database("finance.db")

@router.message(F.text.in_(["💡 Maslahat", "💡 Совет", "💡 Advice"]))
async def give_advice(message: types.Message):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    is_premium = db.is_user_premium(user_id)
    
    stats = db.get_user_stats(user_id, 'month')
    income = 0
    expense = 0
    for t_type, amount in stats:
        if t_type == 'income': income = amount
        else: expense = amount
            
    # Basic logic for everyone
    if income == 0:
        category = "saving"
    else:
        ratio = (expense / income) * 100
        if ratio < 40: category = "saving"
        elif ratio < 80: category = "balance"
        else: category = "danger"
            
    pool = get_text('advice_pool', lang)
    advice = random.choice(pool[category])
    
    text = f"💡 **{get_text('advice_title', lang)}**\n\n"
    
    if is_premium:
        # Premium: Advanced Analysis
        text += f"🌟 **Premium Insights:**\n\n"
        
        # 1. Top expense category
        expenses_by_cat = db.get_expenses_by_category(user_id, 'month')
        if expenses_by_cat:
            top_cat, top_amt = max(expenses_by_cat, key=lambda x: x[1])
            percent = (top_amt / expense * 100) if expense > 0 else 0
            text += f"📊 {get_text('top_expense_msg', lang).format(cat=top_cat, percent=percent)}\n"
        
        # 2. Daily average vs today
        today_stats = db.get_user_stats(user_id, 'day')
        today_expense = sum(amt for t_type, amt in today_stats if t_type == 'expense')
        
        import datetime
        day_of_month = datetime.datetime.now().day
        daily_avg = expense / day_of_month if day_of_month > 0 else 0
        
        if today_expense > daily_avg * 1.5:
            text += f"⚠️ {get_text('high_spending_today', lang)}\n"
        elif today_expense < daily_avg * 0.5:
            text += f"✅ {get_text('low_spending_today', lang)}\n"
            
        text += "\n---\n\n"
        
    text += f"{advice}\n\n"
    text += f"📈 {get_text('advice_status_line', lang)} {expense:,.0f} / {income:,.0f} {get_text('sum', lang)}."
    
    await message.answer(text, parse_mode="Markdown")
