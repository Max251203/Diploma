import os
import sqlite3
import bcrypt

DB_NAME = "iot_lab_data.db"

def get_db_path() -> str:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources"))
    os.makedirs(base_dir, exist_ok=True)
    db_path = os.path.join(base_dir, DB_NAME)

    if not os.path.exists(db_path):
        open(db_path, "a").close()
        initialize_database(db_path)

    return db_path

def initialize_database(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Таблица подключений к Home Assistant
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ha_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            token TEXT NOT NULL
        )
    """)

    # Таблица пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            last_name TEXT,
            first_name TEXT,
            middle_name TEXT,
            role TEXT NOT NULL CHECK(role IN ('student', 'teacher', 'admin'))
        )
    """)

    # Добавление администратора по умолчанию
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    if cursor.fetchone()[0] == 0:
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        cursor.execute("""
            INSERT INTO users (login, password_hash, role)
            VALUES (?, ?, ?)
        """, ("admin", hashed, "admin"))

    conn.commit()
    conn.close()