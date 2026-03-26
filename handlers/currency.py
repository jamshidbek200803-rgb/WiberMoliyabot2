from aiogram import Router, F, types
from utils.currency import get_currency_rates, get_crypto_rates
from database.db_manager import Database
from utils.i18n import get_text

router = Router()
db = Database("finance.db")

@router.message(F.text.in_(["🪙 Valyuta kurslari", "🪙 Курсы валют", "🪙 Currency rates"]))
async def show_rates(message: types.Message):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    
    await message.answer(get_text('currency_loading', lang))
    
    currency = await get_currency_rates()
    crypto = await get_crypto_rates()
    
    text = f"{get_text('currency_title', lang)}\n\n"
    
    if currency:
        for ccy in ['USD', 'EUR', 'RUB']:
            if ccy in currency:
                rate = currency[ccy]['rate']
                diff = currency[ccy]['diff']
                icon = "📈" if diff >= 0 else "📉"
                diff_str = f"+{diff}" if diff >= 0 else str(diff)
                
                flag = "🇺🇸" if ccy == "USD" else "🇪🇺" if ccy == "EUR" else "🇷🇺"
                text += f"{flag} 1 <b>{ccy}</b> = {rate:,.2f} UZS ({icon} {diff_str})\n"
                
        date_str = currency.get('USD', {}).get('date', "Noma'lum")
        text += f"\n<i>{get_text('currency_update_time', lang)}: {date_str}</i>\n"
    else:
        text += f"{get_text('currency_error', lang)}\n"
        
    text += f"\n\n{get_text('crypto_title', lang)}\n\n"
    
    if crypto:
        if 'BTC' in crypto:
            text += f"🟠 <b>Bitcoin (BTC)</b>: ${crypto['BTC']:,.2f}\n"
        if 'ETH' in crypto:
            text += f"🔷 <b>Ethereum (ETH)</b>: ${crypto['ETH']:,.2f}\n"
        if 'TON' in crypto:
            text += f"💎 <b>Toncoin (TON)</b>: ${crypto['TON']:,.2f}\n"
    else:
        text += f"{get_text('crypto_error', lang)}"
        
    await message.answer(text, parse_mode="HTML")
