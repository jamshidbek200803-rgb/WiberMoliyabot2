import sqlite3
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        # Users table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                username TEXT,
                is_premium BOOLEAN DEFAULT 0,
                premium_until DATETIME,
                is_banned BOOLEAN DEFAULT 0,
                account_mode TEXT DEFAULT 'demo', -- 'demo' or 'real'
                real_balance REAL DEFAULT 0,
                pin_code TEXT DEFAULT NULL,
                language TEXT DEFAULT 'uz',
                prem_cancel_count INTEGER DEFAULT 0,
                prem_blocked_until DATETIME DEFAULT NULL,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sessions table for PIN authentication
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                user_id INTEGER PRIMARY KEY,
                last_auth_at REAL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        # Categories table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL -- 'income' or 'expense'
            )
        """)
        # Transactions table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                category_id INTEGER,
                type TEXT, -- 'income' or 'expense'
                comment TEXT,
                receipt_photo_id TEXT, -- For real mode manual verification
                status TEXT DEFAULT 'approved', -- 'pending', 'approved', 'rejected'
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        """)

        # Budgets table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category_id INTEGER,
                amount REAL,
                period TEXT DEFAULT 'month',
                UNIQUE(user_id, category_id, period),
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        """)

        # Savings Goals (Orzu Banki) table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS savings_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL DEFAULT 0,
                priority INTEGER DEFAULT 1,
                item_url TEXT,
                color TEXT, -- For Goal Intel
                description TEXT,
                last_price REAL,
                status TEXT DEFAULT 'active', -- 'active', 'completed'
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)

        # Debts Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL, -- 'borrowed' (biz qarzmiz), 'lent' (bizdan qarz)
                due_date TEXT,
                status TEXT DEFAULT 'active', -- 'active', 'paid'
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Subscriptions Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                billing_cycle TEXT DEFAULT 'monthly', -- 'monthly', 'yearly'
                next_billing_date DATE,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Families Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS families (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                creator_id INTEGER,
                join_code TEXT UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Family Members Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS family_members (
                family_id INTEGER,
                user_id INTEGER PRIMARY KEY,
                role TEXT DEFAULT 'member', -- 'admin', 'member'
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (family_id) REFERENCES families (id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Add family_id to transactions if NOT exists
        self.cursor.execute("PRAGMA table_info(transactions)")
        columns = [col[1] for col in self.cursor.fetchall()]
        if 'family_id' not in columns:
            self.cursor.execute("ALTER TABLE transactions ADD COLUMN family_id INTEGER REFERENCES families(id)")

        # Settings table (Maintenance mode, etc.)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        # Initialize default settings
        self.cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('maintenance_mode', '0')")

        # Extra Admins table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Feedback table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT 0
            )
        """)
        
        # Initial categories if empty
        self.cursor.execute("SELECT COUNT(*) FROM categories")
        if self.cursor.fetchone()[0] == 0:
            initial_categories = [
                ('Oylik', 'income'),
                ('Sotuv', 'income'),
                ('Boshqa', 'income'),
                ('Ovqat', 'expense'),
                ('Transport', 'expense'),
                ('Ijara', 'expense'),
                ('Kommunal', 'expense'),
                ('O\'yin-kulgi', 'expense'),
                ('Boshqa', 'expense')
            ]
            self.cursor.executemany("INSERT INTO categories (name, type) VALUES (?, ?)", initial_categories)
        
        # Ads table
        self.cursor.execute("""
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
        
        self.connection.commit()

    def add_user(self, user_id, full_name, username):
        self.cursor.execute("INSERT OR IGNORE INTO users (user_id, full_name, username) VALUES (?, ?, ?)", (user_id, full_name, username))
        self.connection.commit()

    def add_transaction(self, user_id, amount, category_id, t_type, comment=None, photo_id=None, status='approved'):
        self.cursor.execute("INSERT INTO transactions (user_id, amount, category_id, type, comment, receipt_photo_id, status) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                            (user_id, amount, category_id, t_type, comment, photo_id, status))
        self.connection.commit()
        return self.cursor.lastrowid

    def get_user_mode(self, user_id):
        self.cursor.execute("SELECT account_mode FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 'demo'

    def set_user_mode(self, user_id, mode):
        self.cursor.execute("UPDATE users SET account_mode = ? WHERE user_id = ?", (mode, user_id))
        self.connection.commit()

    def update_real_balance(self, user_id, amount):
        self.cursor.execute("UPDATE users SET real_balance = real_balance + ? WHERE user_id = ?", (amount, user_id))
        self.connection.commit()

    def get_real_balance(self, user_id):
        self.cursor.execute("SELECT real_balance FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0

    def set_pin_code(self, user_id, pin):
        self.cursor.execute("UPDATE users SET pin_code = ? WHERE user_id = ?", (pin, user_id))
        self.connection.commit()

    def get_pin_code(self, user_id):
        self.cursor.execute("SELECT pin_code FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    # --- Language Management ---
    def set_user_language(self, user_id, lang):
        self.cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, user_id))
        self.connection.commit()

    def get_user_language(self, user_id):
        self.cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 'uz'

    # --- Session Management ---
    def update_session(self, user_id, timestamp):
        self.cursor.execute("INSERT OR REPLACE INTO sessions (user_id, last_auth_at) VALUES (?, ?)", (user_id, timestamp))
        self.connection.commit()

    def get_session(self, user_id):
        self.cursor.execute("SELECT last_auth_at FROM sessions WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def clear_session(self, user_id):
        self.cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        self.connection.commit()

    def get_categories(self, t_type):
        self.cursor.execute("SELECT id, name FROM categories WHERE type = ?", (t_type,))
        return self.cursor.fetchall()

    def get_user_stats(self, user_id, period='day'):
        if period == 'day':
            query = "SELECT type, SUM(amount) FROM transactions WHERE user_id = ? AND status = 'approved' AND date(created_at) = date('now') GROUP BY type"
        elif period == 'month':
            query = "SELECT type, SUM(amount) FROM transactions WHERE user_id = ? AND status = 'approved' AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now') GROUP BY type"
        
        self.cursor.execute(query, (user_id,))
        return self.cursor.fetchall()

    def get_transaction_history(self, user_id, period='month'):
        if period == 'month':
            query = """
                SELECT t.created_at, c.name, t.type, t.amount, t.comment
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = ? AND t.status = 'approved' AND strftime('%Y-%m', t.created_at) = strftime('%Y-%m', 'now')
                ORDER BY t.created_at DESC
            """
        else: # all time
            query = """
                SELECT t.created_at, c.name, t.type, t.amount, t.comment
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = ? AND t.status = 'approved'
                ORDER BY t.created_at DESC
            """
        self.cursor.execute(query, (user_id,))
        return self.cursor.fetchall()

    def is_user_premium(self, user_id):
        self.cursor.execute("SELECT is_premium, premium_until FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        if not result:
            return False
        
        is_premium, premium_until = result
        if not is_premium:
            return False
            
        if premium_until:
            from datetime import datetime
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if premium_until < now:
                # Premium expired
                self.cursor.execute("UPDATE users SET is_premium = 0 WHERE user_id = ?", (user_id,))
                self.connection.commit()
                return False
        
        return True

    def set_premium(self, user_id, duration_days=30):
        from datetime import datetime, timedelta
        premium_until = (datetime.now() + timedelta(days=duration_days)).strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute("UPDATE users SET is_premium = 1, premium_until = ? WHERE user_id = ?", (premium_until, user_id))
        self.connection.commit()

    def get_expenses_by_category(self, user_id, period='month'):
        if period == 'month':
            query = """
                SELECT c.name, SUM(t.amount) 
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = ? AND t.type = 'expense' AND t.status = 'approved'
                AND strftime('%Y-%m', t.created_at) = strftime('%Y-%m', 'now')
                GROUP BY c.name
            """
        else: # day
            query = """
                SELECT c.name, SUM(t.amount) 
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = ? AND t.type = 'expense' AND t.status = 'approved'
                AND date(t.created_at) = date('now')
                GROUP BY c.name
            """
            
        self.cursor.execute(query, (user_id,))
        return self.cursor.fetchall()

    # --- Savings Goals (Orzu Banki) ---
    def add_goal(self, user_id, name, target_amount, priority=1, item_url=None, color=None, description=None):
        self.cursor.execute("""
            INSERT INTO savings_goals (user_id, name, target_amount, priority, item_url, color, description, last_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, target_amount, priority, item_url, color, description, target_amount))
        self.connection.commit()

    def get_goal_by_priority(self, user_id, priority):
        self.cursor.execute("""
            SELECT name, target_amount, current_amount, priority, item_url, color, description, last_price 
            FROM savings_goals 
            WHERE user_id = ? AND priority = ? AND status = 'active'
        """, (user_id, priority))
        return self.cursor.fetchone()

    def update_goal_intel(self, user_id, priority, color=None, last_price=None):
        if color:
            self.cursor.execute("UPDATE savings_goals SET color = ? WHERE user_id = ? AND priority = ? AND status = 'active'", (color, user_id, priority))
        if last_price:
            self.cursor.execute("UPDATE savings_goals SET last_price = ? WHERE user_id = ? AND priority = ? AND status = 'active'", (last_price, user_id, priority))
        self.connection.commit()

    def get_goals(self, user_id, status='active'):
        self.cursor.execute("SELECT * FROM savings_goals WHERE user_id = ? AND status = ? ORDER BY priority ASC", (user_id, status))
        return self.cursor.fetchall()

    def deposit_to_goal(self, user_id, amount):
        # Sequential funding logic: find the first active goal by priority
        self.cursor.execute("""
            SELECT id, target_amount, current_amount 
            FROM savings_goals 
            WHERE user_id = ? AND status = 'active' 
            ORDER BY priority ASC LIMIT 1
        """, (user_id,))
        goal = self.cursor.fetchone()
        
        if not goal:
            return False
            
        goal_id, target, current = goal
        new_amount = current + amount
        
        if new_amount >= target:
            self.cursor.execute("UPDATE savings_goals SET current_amount = ?, status = 'completed' WHERE id = ?", (target, goal_id))
            # If there's leftover money, put it in the next goal
            leftover = new_amount - target
            if leftover > 0:
                self.deposit_to_goal(user_id, leftover)
        else:
            self.cursor.execute("UPDATE savings_goals SET current_amount = ? WHERE id = ?", (new_amount, goal_id))
        
        self.connection.commit()
        return True

    # --- Budgets ---
    def set_budget(self, user_id, category_id, amount, period='month'):
        self.cursor.execute("""
            INSERT OR REPLACE INTO budgets (user_id, category_id, amount, period)
            VALUES (?, ?, ?, ?)
        """, (user_id, category_id, amount, period))
        self.connection.commit()

    def get_budget_status(self, user_id, category_id):
        self.cursor.execute("""
            SELECT b.amount, COALESCE(SUM(t.amount), 0)
            FROM budgets b
            LEFT JOIN transactions t ON b.user_id = t.user_id 
                AND b.category_id = t.category_id
                AND t.type = 'expense' 
                AND t.status = 'approved'
                AND strftime('%Y-%m', t.created_at) = strftime('%Y-%m', 'now')
            WHERE b.user_id = ? AND b.category_id = ?
        """, (user_id, category_id))
        return self.cursor.fetchone()

    # --- Debts ---
    def add_debt(self, user_id, name, amount, debt_type, due_date=None):
        self.cursor.execute("""
            INSERT INTO debts (user_id, name, amount, type, due_date)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, amount, debt_type, due_date))
        self.connection.commit()

    def get_debts(self, user_id, status='active'):
        self.cursor.execute("SELECT id, name, amount, type, due_date FROM debts WHERE user_id = ? AND status = ?", (user_id, status))
        return self.cursor.fetchall()

    def mark_debt_paid(self, debt_id):
        self.cursor.execute("UPDATE debts SET status = 'paid' WHERE id = ?", (debt_id,))
        self.connection.commit()

    def delete_debt(self, debt_id):
        self.cursor.execute("DELETE FROM debts WHERE id = ?", (debt_id,))
        self.connection.commit()

    # --- Subscriptions ---
    def add_subscription(self, user_id, name, amount, billing_cycle='monthly', next_date=None):
        self.cursor.execute("""
            INSERT INTO subscriptions (user_id, name, amount, billing_cycle, next_billing_date)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, amount, billing_cycle, next_date))
        self.connection.commit()

    def get_subscriptions(self, user_id, status='active'):
        self.cursor.execute("SELECT id, name, amount, billing_cycle, next_billing_date FROM subscriptions WHERE user_id = ? AND status = ?", (user_id, status))
        return self.cursor.fetchall()

    def delete_subscription(self, sub_id):
        self.cursor.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))
        self.connection.commit()
    # --- Family Wallet ---
    def create_family(self, creator_id, name, join_code):
        self.cursor.execute("INSERT INTO families (name, creator_id, join_code) VALUES (?, ?, ?)", (name, creator_id, join_code))
        family_id = self.cursor.lastrowid
        self.cursor.execute("INSERT INTO family_members (family_id, user_id, role) VALUES (?, ?, ?)", (family_id, creator_id, 'admin'))
        self.connection.commit()
        return family_id

    def get_user_family(self, user_id):
        self.cursor.execute("""
            SELECT f.id, f.name, f.creator_id, f.join_code, m.role 
            FROM families f
            JOIN family_members m ON f.id = m.family_id
            WHERE m.user_id = ?
        """, (user_id,))
        return self.cursor.fetchone()

    def join_family(self, user_id, join_code):
        self.cursor.execute("SELECT id FROM families WHERE join_code = ?", (join_code,))
        family = self.cursor.fetchone()
        if not family:
            return False
        
        self.cursor.execute("INSERT OR REPLACE INTO family_members (family_id, user_id, role) VALUES (?, ?, ?)", (family[0], user_id, 'member'))
        self.connection.commit()
        return True

    def get_family_members(self, family_id):
        self.cursor.execute("""
            SELECT u.user_id, u.full_name, m.role 
            FROM users u
            JOIN family_members m ON u.user_id = m.user_id
            WHERE m.family_id = ?
        """, (family_id,))
        return self.cursor.fetchall()

    def get_family_stats(self, family_id, period='month'):
        # Aggregate stats for all family members
        if period == 'month':
            query = """
                SELECT u.full_name, SUM(t.amount), t.type
                FROM transactions t
                JOIN users u ON t.user_id = u.user_id
                JOIN family_members m ON u.user_id = m.user_id
                WHERE m.family_id = ? AND t.status = 'approved'
                AND strftime('%Y-%m', t.created_at) = strftime('%Y-%m', 'now')
                GROUP BY u.user_id, t.type
            """
        self.cursor.execute(query, (family_id,))
        return self.cursor.fetchall()

    def leave_family(self, user_id):
        self.cursor.execute("DELETE FROM family_members WHERE user_id = ?", (user_id,))
        self.connection.commit()

    # --- Admin Methods ---
    def get_admin_stats(self):
        self.cursor.execute("SELECT COUNT(*) FROM users")
        total_users = self.cursor.fetchone()[0]
        
        self.cursor.execute("""
            SELECT SUM(amount) FROM transactions 
            WHERE type = 'income' AND status = 'approved' 
            AND date(created_at) = date('now')
        """)
        income_today = self.cursor.fetchone()[0] or 0
        
        self.cursor.execute("""
            SELECT SUM(amount) FROM transactions 
            WHERE type = 'expense' AND status = 'approved' 
            AND date(created_at) = date('now')
        """)
        expense_today = self.cursor.fetchone()[0] or 0
        
        return total_users, income_today, expense_today

    def get_all_users_list(self):
        self.cursor.execute("SELECT user_id, full_name, username, is_premium FROM users ORDER BY joined_at DESC")
        return self.cursor.fetchall()

    def update_user_premium(self, user_id, is_premium):
        self.cursor.execute("UPDATE users SET is_premium = ? WHERE user_id = ?", (1 if is_premium else 0, user_id))
        self.connection.commit()

    def update_user_ban_status(self, user_id, is_banned):
        self.cursor.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (1 if is_banned else 0, user_id))
        self.connection.commit()

    def is_user_banned(self, user_id):
        self.cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
        res = self.cursor.fetchone()
        return res[0] if res else 0

    def get_all_user_ids(self):
        self.cursor.execute("SELECT user_id FROM users")
        return [row[0] for row in self.cursor.fetchall()]

    # --- Super Admin Methods ---
    def get_maintenance_mode(self):
        try:
            self.cursor.execute("SELECT value FROM settings WHERE key = 'maintenance_mode'")
            res = self.cursor.fetchone()
            return res[0] == '1' if res else False
        except: return False

    def set_maintenance_mode(self, status):
        self.cursor.execute("UPDATE settings SET value = ? WHERE key = 'maintenance_mode'", ('1' if status else '0',))
        self.connection.commit()

    def add_extra_admin(self, user_id):
        self.cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
        self.connection.commit()

    def remove_extra_admin(self, user_id):
        self.cursor.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        self.connection.commit()

    def is_extra_admin(self, user_id):
        try:
            self.cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
            return self.cursor.fetchone() is not None
        except: return False

    def add_feedback(self, user_id, message):
        self.cursor.execute("INSERT INTO feedback (user_id, message) VALUES (?, ?)", (user_id, message))
        self.connection.commit()

    def get_unread_feedback(self):
        self.cursor.execute("SELECT f.id, f.user_id, f.message, f.created_at, u.full_name FROM feedback f JOIN users u ON f.user_id = u.user_id WHERE f.is_read = 0 ORDER BY f.created_at DESC")
        return self.cursor.fetchall()

    def mark_feedback_read(self, feedback_id):
        self.cursor.execute("UPDATE feedback SET is_read = 1 WHERE id = ?", (feedback_id,))
        self.connection.commit()

    def get_user_audit(self, user_id):
        self.cursor.execute("""
            SELECT t.amount, c.name, t.type, t.created_at 
            FROM transactions t 
            LEFT JOIN categories c ON t.category_id = c.id 
            WHERE t.user_id = ? 
            ORDER BY t.created_at DESC LIMIT 10
        """, (user_id,))
        return self.cursor.fetchall()

    def get_all_categories_admin(self):
        self.cursor.execute("SELECT id, name, type FROM categories")
        return self.cursor.fetchall()

    def delete_category(self, cat_id):
        self.cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        self.connection.commit()

    def add_category(self, name, cat_type):
        self.cursor.execute("INSERT INTO categories (name, type) VALUES (?, ?)", (name, cat_type))
        self.connection.commit()

    def increment_premium_cancel_count(self, user_id):
        self.cursor.execute("UPDATE users SET prem_cancel_count = prem_cancel_count + 1 WHERE user_id = ?", (user_id,))
        self.connection.commit()
        
        # Get current count
        self.cursor.execute("SELECT prem_cancel_count FROM users WHERE user_id = ?", (user_id,))
        count = self.cursor.fetchone()[0]
        return count

    def reset_premium_cancel_count(self, user_id):
        self.cursor.execute("UPDATE users SET prem_cancel_count = 0 WHERE user_id = ?", (user_id,))
        self.connection.commit()

    def set_premium_block(self, user_id, days=3):
        until = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute("UPDATE users SET prem_blocked_until = ? WHERE user_id = ?", (until, user_id))
        self.connection.commit()

    def is_premium_blocked(self, user_id):
        self.cursor.execute("SELECT prem_blocked_until FROM users WHERE user_id = ?", (user_id,))
        row = self.cursor.fetchone()
        if row and row[0]:
            until = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
            if datetime.now() < until:
                return until
        return None

    # --- Ads Management ---
    def add_ad(self, photo_id, text, title, phone, duration_hours):
        expires_at = (datetime.now() + timedelta(hours=duration_hours)).strftime('%Y-%m-%d %H:%M:%S')
        # Deactivate previous active ads
        self.cursor.execute("UPDATE ads SET is_active = 0 WHERE is_active = 1")
        self.cursor.execute("""
            INSERT INTO ads (photo_id, text, title, phone, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (photo_id, text, title, phone, expires_at))
        self.connection.commit()

    def get_active_ad(self):
        # Auto-deactivate expired
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute("UPDATE ads SET is_active = 0 WHERE expires_at < ? AND is_active = 1", (now,))
        self.connection.commit()
        
        self.cursor.execute("SELECT photo_id, text, title, phone, expires_at FROM ads WHERE is_active = 1 ORDER BY id DESC LIMIT 1")
        return self.cursor.fetchone()

    def get_all_users_for_broadcast(self):
        self.cursor.execute("SELECT user_id FROM users")
        return [row[0] for row in self.cursor.fetchall()]
        
    def clear_active_ad(self):
        self.cursor.execute("UPDATE ads SET is_active = 0 WHERE is_active = 1")
        self.connection.commit()

    def get_ads_history(self, limit=10):
        self.cursor.execute("SELECT id, title, phone, created_at, is_active FROM ads ORDER BY id DESC LIMIT ?", (limit,))
        return self.cursor.fetchall()

    def get_ad_by_id(self, ad_id):
        self.cursor.execute("SELECT id, photo_id, text, title, phone, expires_at, is_active FROM ads WHERE id = ?", (ad_id,))
        return self.cursor.fetchone()
