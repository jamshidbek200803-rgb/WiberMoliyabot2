import sqlite3
import os

db_path = 'finance.db'
admin_id = 7049858267

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Unban the admin
        cursor.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (admin_id,))
        print(f"Unbanned user {admin_id}")
        
        # 2. Add as admin if not exists
        cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (admin_id,))
        print(f"Ensured {admin_id} is in admins table")
        
        # 3. Disable maintenance mode
        cursor.execute("UPDATE settings SET value = '0' WHERE key = 'maintenance_mode'")
        print("Disabled maintenance mode")
        
        # 4. Clear sessions to force re-auth if needed
        cursor.execute("DELETE FROM sessions WHERE user_id = ?", (admin_id,))
        
        conn.commit()
        conn.close()
        print("Fix applied successfully!")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Database not found.")
