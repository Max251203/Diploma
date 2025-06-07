import sqlite3
from typing import List, Dict, Optional
from db.init_db import get_db_path

class HAConnectionDB:
    def __init__(self):
        self.conn = sqlite3.connect(get_db_path())
        self._create_tables()

    def _create_tables(self):
        # Таблица для HA соединений
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ha_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                token TEXT NOT NULL
            )
        """)
        # Таблица для API соединений
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS custom_api_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                api_key TEXT NOT NULL
            )
        """)
        self.conn.commit()

    # === HA CRUD ===

    def get_all_connections(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, url, token FROM ha_connections")
        return [
            {"id": row[0], "name": row[1], "url": row[2], "token": row[3]}
            for row in cursor.fetchall()
        ]

    def get_connection_by_id(self, conn_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, url, token FROM ha_connections WHERE id = ?", (conn_id,))
        row = cursor.fetchone()
        return {"id": row[0], "name": row[1], "url": row[2], "token": row[3]} if row else None

    def add_connection(self, name: str, url: str, token: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO ha_connections (name, url, token) VALUES (?, ?, ?)",
            (name, url, token)
        )
        self.conn.commit()
        return cursor.lastrowid

    def update_connection(self, conn_id: int, name: str, url: str, token: str):
        self.conn.execute("""
            UPDATE ha_connections SET name = ?, url = ?, token = ? WHERE id = ?
        """, (name, url, token, conn_id))
        self.conn.commit()

    def delete_connection(self, conn_id: int):
        self.conn.execute("DELETE FROM ha_connections WHERE id = ?", (conn_id,))
        self.conn.commit()

    # === Custom API CRUD ===

    def get_all_custom_api_connections(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, url, api_key FROM custom_api_connections")
        return [
            {"id": row[0], "name": row[1], "url": row[2], "api_key": row[3]}
            for row in cursor.fetchall()
        ]

    def get_custom_api_connection_by_id(self, conn_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, url, api_key FROM custom_api_connections WHERE id = ?", (conn_id,))
        row = cursor.fetchone()
        return {"id": row[0], "name": row[1], "url": row[2], "api_key": row[3]} if row else None

    def add_custom_api_connection(self, name: str, url: str, api_key: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO custom_api_connections (name, url, api_key) VALUES (?, ?, ?)",
            (name, url, api_key)
        )
        self.conn.commit()
        return cursor.lastrowid

    def update_custom_api_connection(self, conn_id: int, name: str, url: str, api_key: str):
        self.conn.execute("""
            UPDATE custom_api_connections SET name = ?, url = ?, api_key = ? WHERE id = ?
        """, (name, url, api_key, conn_id))
        self.conn.commit()

    def delete_custom_api_connection(self, conn_id: int):
        self.conn.execute("DELETE FROM custom_api_connections WHERE id = ?", (conn_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()