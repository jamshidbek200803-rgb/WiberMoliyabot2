import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PAYMENTS_TOKEN = os.getenv("PAYMENTS_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID", "7049858267")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

CARD_NUMBER = "5440 8103 0565 4732"
CARD_OWNER = "Durdiboyev Jamshidbek"
PRICE_PREMIUM = "50 000"

if not BOT_TOKEN:
    exit("BOT_TOKEN topilmadi! .env faylini tekshiring.")

if not GEMINI_API_KEY:
    print("OGOHLANTIRISH: GEMINI_API_KEY topilmadi! AI funksiyalari ishlamasligi mumkin.")
