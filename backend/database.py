import sqlite3
import os

DB_NAME = "quality_control.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table (Workers/Admins)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        shop_id INTEGER
    )
    ''')
    
    # Employees table (Maintenance staff)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        is_available BOOLEAN DEFAULT 1
    )
    ''')
    
    # Devices table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        shop_id INTEGER
    )
    ''')

    # Requests table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        device_id INTEGER,
        description TEXT,
        photo_path TEXT,
        status TEXT DEFAULT 'Pending',
        assigned_employee_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (device_id) REFERENCES devices (id),
        FOREIGN KEY (assigned_employee_id) REFERENCES employees (id)
    )
    ''')
    
    # Insert default user if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'worker'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password_hash, full_name, shop_id) VALUES ('worker', 'password', 'Иван Рабочий', 1)")
        print("Default user 'worker' created.")

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
