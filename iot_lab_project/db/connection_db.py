import sqlite3
import os


class HAConnectionDB:
    def __init__(self, db_path="iot_lab_data.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Инициализация базы данных и создание таблиц, если они не существуют"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Создаем таблицу для подключений Home Assistant
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ha_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            token TEXT NOT NULL
        )
        ''')

        # Создаем таблицу для подключений к API
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            api_key TEXT NOT NULL
        )
        ''')

        conn.commit()
        conn.close()

    def get_all_connections(self):
        """Получение всех подключений Home Assistant"""
        self._init_db()  # Убедимся, что таблицы существуют
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ha_connections")
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result

    def get_connection(self, connection_id):
        """Получение подключения Home Assistant по ID"""
        self._init_db()  # Убедимся, что таблицы существуют
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM ha_connections WHERE id = ?", (connection_id,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

    def add_connection(self, name, url, token):
        """Добавление нового подключения Home Assistant"""
        self._init_db()  # Убедимся, что таблицы существуют
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ha_connections (name, url, token) VALUES (?, ?, ?)",
            (name, url, token)
        )
        conn.commit()
        conn.close()
        return cursor.lastrowid

    def update_connection(self, connection_id, name, url, token):
        """Обновление подключения Home Assistant"""
        self._init_db()  # Убедимся, что таблицы существуют
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ha_connections SET name = ?, url = ?, token = ? WHERE id = ?",
            (name, url, token, connection_id)
        )
        conn.commit()
        conn.close()
        return cursor.rowcount > 0

    def delete_connection(self, connection_id):
        """Удаление подключения Home Assistant"""
        self._init_db()  # Убедимся, что таблицы существуют
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM ha_connections WHERE id = ?", (connection_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0

    def get_all_custom_api_connections(self):
        """Получение всех подключений к API"""
        self._init_db()  # Убедимся, что таблицы существуют
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM api_connections")
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result

    def get_custom_api_connection(self, connection_id):
        """Получение подключения к API по ID"""
        self._init_db()  # Убедимся, что таблицы существуют
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM api_connections WHERE id = ?", (connection_id,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

    def add_custom_api_connection(self, name, url, api_key):
        """Добавление нового подключения к API"""
        self._init_db()  # Убедимся, что таблицы существуют
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO api_connections (name, url, api_key) VALUES (?, ?, ?)",
            (name, url, api_key)
        )
        conn.commit()
        conn.close()
        return cursor.lastrowid

    def update_custom_api_connection(self, connection_id, name, url, api_key):
        """Обновление подключения к API"""
        self._init_db()  # Убедимся, что таблицы существуют
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE api_connections SET name = ?, url = ?, api_key = ? WHERE id = ?",
            (name, url, api_key, connection_id)
        )
        conn.commit()
        conn.close()
        return cursor.rowcount > 0

    def delete_custom_api_connection(self, connection_id):
        """Удаление подключения к API"""
        self._init_db()  # Убедимся, что таблицы существуют
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM api_connections WHERE id = ?", (connection_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
