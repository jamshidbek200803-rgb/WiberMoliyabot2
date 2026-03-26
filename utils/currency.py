import aiohttp
import logging

async def get_currency_rates():
    """
    Markaziy bank (CBU) API'sidan yoki shunga o'xshash manbadan dollar, yevro, rubl va hokazolar uchun o'zbek so'midagi (UZS) kurslarni oladi.
    """
    url = "https://cbu.uz/oz/arkhiv-kursov-valyut/json/"
    rates = {}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Bizga asosan quyidagilar kerak: USD, EUR, RUB, BTC (kripto alohida bo'ladi, CBU da yo'q)
                    for currency in data:
                        if currency['Ccy'] in ['USD', 'EUR', 'RUB']:
                            rates[currency['Ccy']] = {
                                'rate': float(currency['Rate']),
                                'diff': float(currency['Diff']),
                                'date': currency['Date']
                            }
                return rates
    except Exception as e:
        logging.error(f"Error fetching CBU rates: {e}")
        return None

async def get_crypto_rates():
    """
    Binance API orqali mashhur kriptovalyutalar (BTC, ETH, TON) narxini oladi.
    """
    url = "https://api.binance.com/api/v3/ticker/price"
    symbols = '["BTCUSDT","ETHUSDT","TONUSDT"]'
    rates = {}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{url}?symbols={symbols}") as response:
                if response.status == 200:
                    data = await response.json()
                    for item in data:
                        symbol = item['symbol']
                        price = float(item['price'])
                        if 'BTC' in symbol:
                            rates['BTC'] = price
                        elif 'ETH' in symbol:
                            rates['ETH'] = price
                        elif 'TON' in symbol:
                            rates['TON'] = price
                return rates
    except Exception as e:
        logging.error(f"Error fetching Crypto rates: {e}")
        return None
