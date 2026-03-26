import sqlite3

def migrate():
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    
    print("Migratsiya boshlandi...")
    
    # Users jadvaliga ustunlar qo'shish
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN account_mode TEXT DEFAULT 'demo'")
        print("- users: account_mode qo'shildi")
    except sqlite3.OperationalError:
        print("- users: account_mode allaqachon bor")

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN real_balance REAL DEFAULT 0")
        print("- users: real_balance qo'shildi")
    except sqlite3.OperationalError:
        print("- users: real_balance allaqachon bor")

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'uz'")
        print("- users: language qo'shildi")
    except sqlite3.OperationalError:
        print("- users: language allaqachon bor")

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN pin_code TEXT")
        print("- users: pin_code qo'shildi")
    except sqlite3.OperationalError:
        print("- users: pin_code allaqachon bor")

    # Transactions jadvaliga ustunlar qo'shish
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN receipt_photo_id TEXT")
        print("- transactions: receipt_photo_id qo'shildi")
    except sqlite3.OperationalError:
        print("- transactions: receipt_photo_id allaqachon bor")

    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN status TEXT DEFAULT 'approved'")
        print("- transactions: status qo'shildi")
    except sqlite3.OperationalError:
        print("- transactions: status allaqachon bor")

    conn.commit()
    conn.close()
    print("Migratsiya muvaffaqiyatli yakunlandi!")

if __name__ == "__main__":
    migrate()
