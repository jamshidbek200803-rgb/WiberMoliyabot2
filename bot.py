import asyncio
import logging
import sys
import os
from aiohttp import web

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database.db_manager import Database
from keyboards.menu import main_menu
from handlers.transactions import router as trans_router
from handlers.stats import router as stats_router
from handlers.payments import router as payments_router
from handlers.settings import router as settings_router
from handlers.savings import router as savings_router
from handlers.budget import router as budget_router
from handlers.admin import router as admin_router
from handlers.advice import router as advice_router
from handlers.debts import router as debt_router
from handlers.chat import router as chat_router
from handlers.currency import router as currency_router
from handlers.security import router as security_router
from handlers.subscriptions import router as sub_router
from handlers.family import router as family_router
from handlers.feedback import router as feedback_router
from middlewares.security import SecurityMiddleware
from utils.scheduler import setup_scheduler

# Bot va Dispetcherni sozlash
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
middleware_db = Database("finance.db")
dp.message.middleware(SecurityMiddleware(db=middleware_db))
dp.callback_query.middleware(SecurityMiddleware(db=middleware_db))
dp.include_router(security_router)
dp.include_router(trans_router)
dp.include_router(stats_router)
dp.include_router(payments_router)
dp.include_router(settings_router)
dp.include_router(savings_router)
dp.include_router(budget_router)
dp.include_router(admin_router)
dp.include_router(advice_router)
dp.include_router(debt_router)
dp.include_router(chat_router)
dp.include_router(currency_router)
dp.include_router(sub_router)
dp.include_router(family_router)
dp.include_router(feedback_router)
from utils.i18n import get_text
db = middleware_db

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user = message.from_user
    db.add_user(user.id, user.full_name, user.username)
    
    # Refresh user data
    lang = db.get_user_language(user.id)
    balance = db.get_real_balance(user.id)
    is_premium = db.is_user_premium(user.id)
    
    start_text = get_text('welcome', lang, name=user.full_name)
    
    active_ad = db.get_active_ad()
    if active_ad:
        ad_title = active_ad[2]
        ad_phone = active_ad[3]
        ad_msg = active_ad[1]
        start_text += f"\n\n📣 <b>{ad_title}</b>\n📞 {ad_phone}\n\n{ad_msg}"
    
    photo_path = "logo.jpg"
    if os.path.exists(photo_path):
        await message.answer_photo(
            photo=types.FSInputFile(photo_path),
            caption=start_text,
            reply_markup=main_menu(lang, balance, is_premium),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            start_text,
            reply_markup=main_menu(lang, balance, is_premium),
            parse_mode="HTML"
        )


# handle_webapp_data has been removed as per the new plan


# health_check for Render
async def health_check(request):
    return web.Response(text="Bot is running")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render sets the PORT environment variable automatically
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Health check server started on port {port}")

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    # Bot tavsiflarini o'rnatish (Set bot descriptions)
    descriptions = {
        'uz': {
            'full': "🤖 Bu bot nima qila oladi?\n\n🏦 Kirim va chiqimlarni nazorat qilish\n🎯 Jamg'arma maqsadlarini belgilash (Orzu Banki)\n📊 Moliyaviy statistika va grafiklar\n📉 Xarajatlar uchun limitlar o'rnatish\n💸 Qarzlar va obunalar hisobini yuritish\n👥 Oila a'zolari bilan umumiy hamyon\n🤖 AI yordamida aqlli maslahatlar\n\nMablag'laringizni biz bilan aqlli boshqaring! 🚀",
            'short': "Shaxsiy moliyaviy yordamchingiz. Kirim-chiqim, budjet, qarzlar va AI maslahatlar! 💸"
        },
        'ru': {
            'full': "🤖 Что может этот бот?\n\n🏦 Контроль доходов и расходов\n🎯 Установка целей накопления (Копилка)\n📊 Финансовая статистика и графики\n📉 Установка лимитов на расходы\n💸 Учет долгов и подписок\n👥 Общий кошелек с членами семьи\n🤖 Умные советы с помощью ИИ\n\nУправляйте своими финансами с нами! 🚀",
            'short': "Ваш личный финансовый помощник. Доходы, расходы, бюджет и советы ИИ! 💸"
        },
        'en': {
            'full': "🤖 What can this bot do?\n\n🏦 Income and expense tracking\n🎯 Saving goals (Goal Bank)\n📊 Financial statistics and charts\n📉 Setting spending limits\n💸 Debt and subscription tracking\n👥 Shared wallet with family members\n🤖 Smart financial advice with AI\n\nManage your funds wisely with us! 🚀",
            'short': "Your personal financial assistant. Income, expenses, budget and AI advice! 💸"
        }
    }

    # Standart tavsifni (default) o'rnatish - O'zbek tili
    try:
        await bot.set_my_description(description=descriptions['uz']['full'])
        await bot.set_my_short_description(short_description=descriptions['uz']['short'])
    except Exception as e:
        logging.error(f"Error setting default description: {e}")

    for lang_code, desc in descriptions.items():
        try:
            await bot.set_my_description(description=desc['full'], language_code=lang_code)
            await bot.set_my_short_description(short_description=desc['short'], language_code=lang_code)
        except Exception as e:
            logging.error(f"Error setting description for {lang_code}: {e}")

    setup_scheduler(bot)
    
    # Start health check server for Render
    await start_web_server()
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi")
