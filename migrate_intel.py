import sqlite3

def migrate():
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    
    print("Migratsiya (Goal Intel) boshlandi...")
    
    # Savings Goals jadvaliga ustunlar qo'shish
    try:
        cursor.execute("ALTER TABLE savings_goals ADD COLUMN color TEXT")
        print("- savings_goals: color qo'shildi")
    except sqlite3.OperationalError:
        print("- savings_goals: color allaqachon bor")

    try:
        cursor.execute("ALTER TABLE savings_goals ADD COLUMN description TEXT")
        print("- savings_goals: description qo'shildi")
    except sqlite3.OperationalError:
        print("- savings_goals: description allaqachon bor")

    conn.commit()
    conn.close()
    print("Migratsiya muvaffaqiyatli yakunlandi!")

if __name__ == "__main__":
    migrate()
