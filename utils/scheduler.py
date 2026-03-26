from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.db_manager import Database
from utils.price_tracker import get_current_price
from utils.i18n import get_text
from datetime import datetime
import asyncio

db = Database("finance.db")

async def send_daily_reports(bot):
    """
    Har kuni 08:00 (Toshkent vaqti) da foydalanuvchilarga hisobot yuborish.
    """
    db.cursor.execute("SELECT user_id, full_name, language FROM users")
    users = db.cursor.fetchall()
    
    for user_id, full_name, lang in users:
        goals = db.get_goals(user_id)
        if not goals:
            continue
            
        report = get_text('daily_report_welcome', lang, name=full_name) + "\n"
        report += get_text('daily_report_status', lang) + "\n\n"
        
        total_target = 0
        total_current = 0
        
        for goal in goals:
            # goal index: 0:id, 1:user_id, 2:name, 3:target, 4:current, 5:priority, 6:url, 7:last_price, 8:status
            goal_id = goal[0]
            name = goal[2]
            target = goal[3]
            current = goal[4]
            priority = goal[5]
            url = goal[6]
            last_price = goal[7]

            if url:
                price_info = await get_current_price(url)
                if price_info and price_info.get('price'):
                    new_price = price_info['price']
                    if new_price < target:
                        db.cursor.execute("UPDATE savings_goals SET last_price = ?, target_amount = ? WHERE id = ?", (new_price, new_price, goal_id))
                        db.connection.commit()
                        report += get_text('daily_report_price_drop', lang, name=name, old=target, new=new_price) + "\n"
                        target = new_price

            percent = (current / target) * 100 if target > 0 else 0
            diff = max(0, target - current)
            
            report += f"{priority}. **{name}**\n"
            report += get_text('daily_report_progress', lang, current=current, target=target, percent=percent) + "\n"
            report += get_text('daily_report_left', lang, diff=diff) + "\n"
            
            total_target += target
            total_current += current

        report += f"\n{get_text('daily_report_total', lang)}\n"
        report += get_text('daily_report_total_target', lang, target=total_target) + "\n"
        report += get_text('daily_report_total_collected', lang, current=total_current) + "\n"
        report += get_text('daily_report_total_remaining', lang, remaining=max(0, total_target - total_current)) + "\n\n"
        report += get_text('daily_report_footer', lang)
        
        try:
            await bot.send_message(user_id, report, parse_mode="Markdown")
        except Exception as e:
            print(f"Error sending daily report to {user_id}: {e}")
        
        await asyncio.sleep(0.05) 

def setup_scheduler(bot):
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    # Har kuni 08:00 da
    scheduler.add_job(send_daily_reports, 'cron', hour=8, minute=0, args=[bot])
    scheduler.start()
    return scheduler
