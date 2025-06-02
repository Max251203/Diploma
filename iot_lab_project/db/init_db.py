# db/init_db.py

import os
import sqlite3
import bcrypt
from core.permissions import RoleEnum

DB_NAME = "iot_lab_data.db"

def get_db_path() -> str:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources"))
    os.makedirs(base_dir, exist_ok=True)
    path = os.path.join(base_dir, DB_NAME)

    if not os.path.exists(path):
        open(path, "a").close()
        initialize_database(path)

    return path

def initialize_database(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ha_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            token TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            last_name TEXT,
            first_name TEXT,
            middle_name TEXT,
            role TEXT NOT NULL
        )
    """)

    # Система ролей без хардкода
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = ?", (RoleEnum.ADMIN.value,))
    if cursor.fetchone()[0] == 0:
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        cursor.execute("""
            INSERT INTO users (login, password_hash, role)
            VALUES (?, ?, ?)
        """, ("admin", hashed, RoleEnum.ADMIN.value))

    conn.commit()
    conn.close()