import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    # Create expenses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            item TEXT NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def register_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        password_hash = generate_password_hash(password)
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                 (username, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    
    if result and check_password_hash(result[1], password):
        return result[0]  # Return user_id
    return None

def save_expenses(user_id, expenses):
    if not user_id or user_id <= 0:  # Guest user or None
        return
        
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Clear existing expenses for user
    c.execute('DELETE FROM expenses WHERE user_id = ?', (user_id,))
    
    # Insert new expenses
    for category_item, amount in expenses.items():
        category, item = category_item.split('_', 1)
        c.execute('''
            INSERT INTO expenses (user_id, category, item, amount)
            VALUES (?, ?, ?, ?)
        ''', (user_id, category, item, amount))
    
    conn.commit()
    conn.close()

def load_expenses(user_id):
    if not user_id or user_id <= 0:  # Guest user or None
        return {}
        
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('SELECT category, item, amount FROM expenses WHERE user_id = ?', (user_id,))
    results = c.fetchall()
    conn.close()
    
    expenses = {}
    for category, item, amount in results:
        expenses[f"{category}_{item}"] = amount
    
    return expenses 