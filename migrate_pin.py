import sqlite3
import os

db_path = 'finance.db'

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'pin_code' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN pin_code TEXT DEFAULT NULL")
            conn.commit()
            print("Column 'pin_code' added successfully.")
        else:
            print("Column 'pin_code' already exists.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"Database {db_path} not found.")
