import sqlite3
import os

db_path = 'finance.db'

def add_column(cursor, table, column, type_def):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_def}")
        print(f"Added column {column} to {table}")
    except sqlite3.OperationalError:
        print(f"Column {column} already exists in {table}")

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add missing columns to users
        add_column(cursor, "users", "is_banned", "BOOLEAN DEFAULT 0")
        add_column(cursor, "users", "account_mode", "TEXT DEFAULT 'demo'")
        add_column(cursor, "users", "real_balance", "REAL DEFAULT 0")
        add_column(cursor, "users", "pin_code", "TEXT DEFAULT NULL")
        add_column(cursor, "users", "language", "TEXT DEFAULT 'uz'")
        add_column(cursor, "users", "is_premium", "BOOLEAN DEFAULT 0")
        add_column(cursor, "users", "premium_until", "DATETIME")
        add_column(cursor, "users", "prem_cancel_count", "INTEGER DEFAULT 0")
        add_column(cursor, "users", "prem_blocked_until", "DATETIME DEFAULT NULL")
        
        # Add ads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                photo_id TEXT,
                text TEXT,
                title TEXT,
                phone TEXT,
                expires_at DATETIME,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Ensured ads table exists.")
        
        conn.commit()
        conn.close()
        print("Migration finished.")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Database not found.")
