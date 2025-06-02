# db/users_db.py

import sqlite3
import bcrypt
from typing import Optional, List, Dict
from db.init_db import get_db_path
from core.permissions import get_all_roles

class UserDB:
    def __init__(self):
        self.conn = sqlite3.connect(get_db_path())
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
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
        self.conn.commit()

    def add_user(self, login, password, last_name, first_name, middle_name, role="student"):
        if role not in get_all_roles():
            raise ValueError("Недопустимая роль")

        if self.get_user_by_login(login):
            raise ValueError("Пользователь с таким логином уже существует")

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        self.conn.execute("""
            INSERT INTO users (login, password_hash, last_name, first_name, middle_name, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (login, hashed, last_name, first_name, middle_name, role))
        self.conn.commit()

    def update_user_info(self, user_id, login, last_name, first_name, middle_name, new_password=None, role=None):
        if role and role not in get_all_roles():
            raise ValueError("Недопустимая роль")

        existing = self.get_user_by_login(login)
        if existing and existing["id"] != user_id:
            raise ValueError("Пользователь с таким логином уже существует")

        cursor = self.conn.cursor()
        if new_password:
            hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            cursor.execute("""
                UPDATE users
                SET login=?, last_name=?, first_name=?, middle_name=?, password_hash=?, role=COALESCE(?, role)
                WHERE id=?
            """, (login, last_name, first_name, middle_name, hashed, role, user_id))
        else:
            cursor.execute("""
                UPDATE users
                SET login=?, last_name=?, first_name=?, middle_name=?, role=COALESCE(?, role)
                WHERE id=?
            """, (login, last_name, first_name, middle_name, role, user_id))
        self.conn.commit()

    def authenticate_user(self, login: str, password: str) -> Optional[Dict]:
        user = self.get_user_by_login(login)
        if user and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            return user
        return None

    def get_user_by_login(self, login: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE login = ?", (login,))
        row = cursor.fetchone()
        return self._row_to_dict(row) if row else None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return self._row_to_dict(row) if row else None

    def get_all_users(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, login, last_name, first_name, middle_name, role FROM users")
        return [
            {
                "id": row[0],
                "login": row[1],
                "last_name": row[2],
                "first_name": row[3],
                "middle_name": row[4],
                "role": row[5]
            }
            for row in cursor.fetchall()
        ]

    def delete_user(self, user_id: int):
        self.conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.conn.commit()

    def update_user_role(self, user_id: int, new_role: str):
        if new_role not in get_all_roles():
            raise ValueError("Недопустимая роль")
        self.conn.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
        self.conn.commit()

    def _row_to_dict(self, row) -> Dict:
        return {
            "id": row[0],
            "login": row[1],
            "password_hash": row[2],
            "last_name": row[3],
            "first_name": row[4],
            "middle_name": row[5],
            "role": row[6]
        }