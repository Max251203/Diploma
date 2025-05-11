import sqlite3
import bcrypt
from core.db.db_config import get_db_path


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
                role TEXT NOT NULL CHECK(role IN ('student', 'teacher', 'admin'))
            )
        """)
        self.conn.commit()

    def add_user(self, login, password, last_name, first_name, middle_name, role="student"):
        if self.get_user_by_login(login):
            raise ValueError("Пользователь с таким логином уже существует")

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        self.conn.execute("""
            INSERT INTO users (login, password_hash, last_name, first_name, middle_name, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (login, hashed, last_name, first_name, middle_name, role))
        self.conn.commit()

    def update_user_info(self, user_id, login, last_name, first_name, middle_name, new_password=None, role=None):
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

    def authenticate_user(self, login, password):
        user = self.get_user_by_login(login)
        if not user:
            return None
        if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            return user
        return None

    def get_user_by_login(self, login):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM users WHERE login = ?", (login,))
        row = cur.fetchone()
        if row:
            return {
                "id": row[0],
                "login": row[1],
                "password_hash": row[2],
                "last_name": row[3],
                "first_name": row[4],
                "middle_name": row[5],
                "role": row[6]
            }
        return None

    def get_user_by_id(self, user_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if row:
            return {
                "id": row[0],
                "login": row[1],
                "password_hash": row[2],
                "last_name": row[3],
                "first_name": row[4],
                "middle_name": row[5],
                "role": row[6]
            }
        return None

    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, login, last_name, first_name, middle_name, role FROM users")
        rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "login": row[1],
                "last_name": row[2],
                "first_name": row[3],
                "middle_name": row[4],
                "role": row[5]
            }
            for row in rows
        ]

    def delete_user(self, user_id):
        self.conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.conn.commit()

    def update_user_role(self, user_id, new_role):
        self.conn.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
        self.conn.commit()