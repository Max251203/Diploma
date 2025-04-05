import os
import sqlite3
from typing import List, Dict, Optional

class HAConnectionDB:
    """Класс для работы с базой данных подключений к Home Assistant"""
    
    def __init__(self, db_path=None):
        # Определение пути к базе данных
        if not db_path:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources"))
            db_path = os.path.join(base_dir, "ha_connections.db")
        
        # Создание директории, если не существует
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Подключение к базе данных
        self.conn = sqlite3.connect(db_path)
        self._create_table()
    
    def _create_table(self):
        """Создает таблицу подключений, если она не существует"""
        query = """
        CREATE TABLE IF NOT EXISTS ha_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            token TEXT NOT NULL
        )
        """
        self.conn.execute(query)
        self.conn.commit()
    
    def get_all_connections(self) -> List[Dict]:
        """Возвращает список всех подключений"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, url, token FROM ha_connections")
        rows = cursor.fetchall()
        return [{"id": r[0], "name": r[1], "url": r[2], "token": r[3]} for r in rows]
    
    def get_connection_by_id(self, conn_id: int) -> Optional[Dict]:
        """Возвращает подключение по ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, url, token FROM ha_connections WHERE id = ?", (conn_id,))
        row = cursor.fetchone()
        if row:
            return {"id": row[0], "name": row[1], "url": row[2], "token": row[3]}
        return None
    
    def add_connection(self, name: str, url: str, token: str) -> int:
        """Добавляет новое подключение"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO ha_connections (name, url, token) VALUES (?, ?, ?)",
            (name, url, token)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def update_connection(self, conn_id: int, name: str, url: str, token: str):
        """Обновляет существующее подключение"""
        query = """
        UPDATE ha_connections
        SET name = ?, url = ?, token = ?
        WHERE id = ?
        """
        self.conn.execute(query, (name, url, token, conn_id))
        self.conn.commit()
    
    def delete_connection(self, conn_id: int):
        """Удаляет подключение"""
        self.conn.execute("DELETE FROM ha_connections WHERE id = ?", (conn_id,))
        self.conn.commit()
    
    def close(self):
        """Закрывает соединение с базой данных"""
        self.conn.close()