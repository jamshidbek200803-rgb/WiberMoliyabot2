from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db_manager import Database
from utils.charts import create_expense_pie_chart
from utils.reports import create_excel_report
from utils.i18n import get_text, get_cat_text
import io

router = Router()
db = Database("finance.db")

@router.message(F.text.in_(["📊 Statistika", "📊 Статистика", "📊 Statistics"]))
async def show_stats(message: types.Message):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    stats_day = db.get_user_stats(user_id, 'day')
    stats_month = db.get_user_stats(user_id, 'month')
    is_premium = db.is_user_premium(user_id)
    
    msg = f"{get_text('stats_title', lang)}\n\n**{get_text('stats_today', lang)}:**\n"
    
    if stats_day:
        for t_type, amount in stats_day:
            t_name = get_text('type_income_label' if t_type == "income" else 'type_expense_label', lang)
            msg += f" - {t_name}: {amount:,} {get_text('sum', lang)}\n"
    else:
        msg += f" - {get_text('no_data', lang)}\n"

    msg += f"\n**{get_text('stats_this_month', lang)}:**\n"
    
    if stats_month:
        for t_type, amount in stats_month:
            t_name = get_text('type_income_label' if t_type == "income" else 'type_expense_label', lang)
            msg += f" - {t_name}: {amount:,} {get_text('sum', lang)}\n"
    else:
        msg += f" - {get_text('no_data', lang)}\n"

    kb = []
    if is_premium:
        kb.append([InlineKeyboardButton(text=get_text("report_monthly_excel", lang), callback_data="report_month")])
        kb.append([InlineKeyboardButton(text=get_text("report_all_time", lang), callback_data="report_all")])
    markup = InlineKeyboardMarkup(inline_keyboard=kb) if kb else None

    if is_premium:
        expense_data = db.get_expenses_by_category(user_id, 'month')
        if expense_data:
            # Localize category names for the chart
            localized_data = [(get_cat_text(name, lang), amount) for name, amount in expense_data]
            chart_buf = create_expense_pie_chart(localized_data, lang)
            if chart_buf:
                photo = types.BufferedInputFile(chart_buf.read(), filename="stats.png")
                await message.answer_photo(photo, caption=msg, parse_mode="Markdown", reply_markup=markup)
                return
        
        await message.answer(msg + f"\n\n*{get_text('stats_not_enough_for_chart', lang)}*", parse_mode="Markdown", reply_markup=markup)
    else:
        msg += f"\n\n🌟 **Premium status** {get_text('stats_premium_promo', lang)}"
        await message.answer(msg, parse_mode="Markdown")

@router.callback_query(F.data.startswith("report_"))
async def process_report_download(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    period = callback.data.split("_")[1]
    
    if not db.is_user_premium(user_id):
        await callback.answer(get_text("alert_premium_required", lang), show_alert=True)
        return
        
    await callback.message.answer(get_text("report_preparing_excel", lang))
    transactions = db.get_transaction_history(user_id, period)
    
    if not transactions:
        await callback.message.answer(get_text("no_data", lang))
        await callback.answer()
        return
        
    excel_buf = create_excel_report(transactions, lang)
    if excel_buf:
        document = types.BufferedInputFile(excel_buf.read(), filename=f"{get_text('report_file_name', lang)}_{period}.xlsx")
        await callback.message.answer_document(document=document, caption=get_text('report_caption', lang))
    else:
        await callback.message.answer(get_text("currency_error", lang))
    
    await callback.answer()
