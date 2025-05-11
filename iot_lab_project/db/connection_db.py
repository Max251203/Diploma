import sqlite3
from typing import List, Dict, Optional
from db.init_db import get_db_path

class HAConnectionDB:
    def __init__(self):
        self.conn = sqlite3.connect(get_db_path())
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ha_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                token TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def get_all_connections(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, url, token FROM ha_connections")
        return [
            {"id": r[0], "name": r[1], "url": r[2], "token": r[3]} for r in cursor.fetchall()
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

    def close(self):
        self.conn.close()