import httpx
from bs4 import BeautifulSoup
import re
import json

async def get_current_price(url):
    """
    Uzum Market va boshqa saytlardan real narx va ma'lumotlarni olish.
    Qaytaradi: {'price': float, 'color': str, 'name': str} yoki None
    """
    if not url:
        return None
        
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.34 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.34"
        }
        
        async with httpx.AsyncClient(timeout=10.0, headers=headers, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Uzum Market uchun maxsus mantiq
            if "uzum.uz" in url:
                # Meta teglarni tekshirish
                price_meta = soup.find("meta", property="product:price:amount")
                price = float(price_meta['content']) if price_meta else None
                
                title_meta = soup.find("meta", property="og:title")
                name = title_meta['content'] if title_meta else None
                
                # Rangi: yanada kengroq qidiruv
                color = None
                
                # 1. Kengaytirilgan ranglar ro'yxati
                colors_uz = [
                    'Qora', 'Oq', 'Ko\'k', 'Yashil', 'Sariq', 'Qizil', 'Kulrang', 
                    'Tilla', 'Kumush', 'Pushti', 'Binafsharang', 'Jigarrang', 
                    'Och ko\'k', 'To\'q ko\'k', 'Havo rang', 'Grafid', 'Moviy'
                ]
                
                # 2. Butun text ichidan "Rangi: ..." patternini qidirish
                page_text = soup.get_text()
                match = re.search(r'(?:Rangi|Цвет):\s*([^\n,.]+)', page_text, re.IGNORECASE)
                if match:
                    color = match.group(1).strip()
                
                # 3. Agar hali ham topilmasa, title ichidan qidirish
                if not color and name:
                    for c in colors_uz:
                        if c.lower() in name.lower():
                            color = c
                            break
                
                # 4. Agar narx meta tegda yo'q bo'lsa
                if not price:
                    # Uzum narxni ko'pincha "price__value" yoki shunga o'xshash klasslarda yuritadi
                    price_text = soup.find("span", class_="price__value") or soup.find("span", class_="p-0")
                    if price_text:
                        price = float(re.sub(r'[^\d]', '', price_text.text))

                return {
                    'price': price,
                    'color': color,
                    'name': name
                }
            
            return None
    except Exception as e:
        print(f"Scraping error: {e}")
        return None
