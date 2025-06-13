import sqlite3
import json
import bcrypt
from datetime import datetime
from typing import Dict, List, Any, Optional
from config import DB_PATH, logger


def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Таблица для данных сенсоров
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sensor_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT NOT NULL,
        timestamp DATETIME NOT NULL,
        data JSON NOT NULL
    )
    ''')

    # Таблица для групп устройств
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS device_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        devices JSON NOT NULL
    )
    ''')

    # Таблица для автоматизаций
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS automations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        enabled BOOLEAN DEFAULT 1,
        trigger JSON NOT NULL,
        actions JSON NOT NULL
    )
    ''')

    # Таблица пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        last_name TEXT,
        first_name TEXT,
        middle_name TEXT,
        role TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Таблица лабораторных работ
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS labs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        content JSON NOT NULL,
        created_by INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users(id)
    )
    ''')

    # Таблица заданий в лабораторных работах
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lab_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lab_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        task_type TEXT NOT NULL,
        content JSON NOT NULL,
        order_index INTEGER NOT NULL,
        max_score REAL NOT NULL DEFAULT 10.0,
        FOREIGN KEY (lab_id) REFERENCES labs(id) ON DELETE CASCADE
    )
    ''')

    # Таблица для связи устройств с заданиями
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS task_devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        device_id TEXT NOT NULL,
        required_state JSON,
        FOREIGN KEY (task_id) REFERENCES lab_tasks(id) ON DELETE CASCADE
    )
    ''')

    # Таблица результатов выполнения лабораторных работ
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lab_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lab_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'in_progress',
        started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        submitted_at DATETIME,
        score REAL,
        feedback TEXT,
        reviewed_by INTEGER,
        reviewed_at DATETIME,
        FOREIGN KEY (lab_id) REFERENCES labs(id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (reviewed_by) REFERENCES users(id)
    )
    ''')

    # Таблица результатов выполнения заданий
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS task_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lab_result_id INTEGER NOT NULL,
        task_id INTEGER NOT NULL,
        answer JSON,
        score REAL,
        feedback TEXT,
        FOREIGN KEY (lab_result_id) REFERENCES lab_results(id) ON DELETE CASCADE,
        FOREIGN KEY (task_id) REFERENCES lab_tasks(id)
    )
    ''')

    # Таблица устройств (для хранения метаданных)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS devices (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        description TEXT,
        location TEXT,
        metadata JSON
    )
    ''')

    # Таблица бронирования устройств
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS device_bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        start_time DATETIME NOT NULL,
        end_time DATETIME NOT NULL,
        purpose TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (device_id) REFERENCES devices(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # Таблица сессий пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT NOT NULL,
        ip_address TEXT,
        user_agent TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # Создаем администратора по умолчанию, если его нет
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    if cursor.fetchone()[0] == 0:
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        cursor.execute('''
            INSERT INTO users (login, password_hash, role, last_name, first_name)
            VALUES (?, ?, ?, ?, ?)
        ''', ("admin", hashed, "admin", "Администратор", "Системный"))

    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")


def get_db_connection():
    """Получение соединения с базой данных"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def save_to_db(device_id, data):
    """Сохранение данных устройства в БД"""
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO sensor_data (device_id, timestamp, data) VALUES (?, ?, ?)",
        (device_id, timestamp, json.dumps(data))
    )
    conn.commit()
    conn.close()


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Получение пользователя по ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return dict(user)
    return None


def get_user_by_login(login: str) -> Optional[Dict]:
    """Получение пользователя по логину"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE login = ?", (login,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return dict(user)
    return None


def create_user(login: str, password: str, last_name: str, first_name: str, middle_name: str, role: str) -> int:
    """Создание нового пользователя"""
    hashed_password = bcrypt.hashpw(
        password.encode(), bcrypt.gensalt()).decode()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (login, password_hash, last_name, first_name, middle_name, role) VALUES (?, ?, ?, ?, ?, ?)",
        (login, hashed_password, last_name, first_name, middle_name, role)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return user_id


def update_user(user_id: int, data: Dict) -> bool:
    """Обновление данных пользователя"""
    fields = []
    values = []

    if 'login' in data and data['login']:
        fields.append("login = ?")
        values.append(data['login'])

    if 'last_name' in data and data['last_name'] is not None:
        fields.append("last_name = ?")
        values.append(data['last_name'])

    if 'first_name' in data and data['first_name'] is not None:
        fields.append("first_name = ?")
        values.append(data['first_name'])

    if 'middle_name' in data and data['middle_name'] is not None:
        fields.append("middle_name = ?")
        values.append(data['middle_name'])

    if 'role' in data and data['role']:
        fields.append("role = ?")
        values.append(data['role'])

    if 'password' in data and data['password']:
        fields.append("password_hash = ?")
        hashed = bcrypt.hashpw(
            data['password'].encode(), bcrypt.gensalt()).decode()
        values.append(hashed)

    if not fields:
        return False

    values.append(user_id)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE users SET {', '.join(fields)} WHERE id = ?",
        values
    )
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return success


def delete_user(user_id: int) -> bool:
    """Удаление пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return success


def get_all_users() -> List[Dict]:
    """Получение списка всех пользователей"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = [dict(user) for user in cursor.fetchall()]
    conn.close()

    return users


def create_user_session(user_id: int, token: str, ip_address: str, user_agent: str, expires_at: datetime) -> int:
    """Создание новой сессии пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_sessions (user_id, token, ip_address, user_agent, expires_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, token, ip_address, user_agent, expires_at.isoformat())
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return session_id


def get_session_by_token(token: str) -> Optional[Dict]:
    """Получение сессии по токену"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM user_sessions WHERE token = ? AND is_active = 1 AND expires_at > ?",
        (token, datetime.now().isoformat())
    )
    session = cursor.fetchone()
    conn.close()

    if session:
        return dict(session)
    return None


def invalidate_session(token: str) -> bool:
    """Инвалидация сессии (выход)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE user_sessions SET is_active = 0 WHERE token = ?",
        (token,)
    )
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return success


def invalidate_all_user_sessions(user_id: int) -> int:
    """Инвалидация всех сессий пользователя (выход со всех устройств)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE user_sessions SET is_active = 0 WHERE user_id = ? AND is_active = 1",
        (user_id,)
    )
    count = cursor.rowcount
    conn.commit()
    conn.close()

    return count


def save_device_metadata(device_id: str, name: str, device_type: str, description: str = None, location: str = None, metadata: Dict = None) -> bool:
    """Сохранение метаданных устройства"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Проверяем, существует ли устройство
    cursor.execute("SELECT id FROM devices WHERE id = ?", (device_id,))
    exists = cursor.fetchone() is not None

    if exists:
        # Обновляем существующее устройство
        cursor.execute(
            "UPDATE devices SET name = ?, type = ?, description = ?, location = ?, metadata = ? WHERE id = ?",
            (name, device_type, description, location, json.dumps(
                metadata) if metadata else None, device_id)
        )
    else:
        # Создаем новое устройство
        cursor.execute(
            "INSERT INTO devices (id, name, type, description, location, metadata) VALUES (?, ?, ?, ?, ?, ?)",
            (device_id, name, device_type, description, location,
             json.dumps(metadata) if metadata else None)
        )

    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return success


def get_device_metadata(device_id: str) -> Optional[Dict]:
    """Получение метаданных устройства"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
    device = cursor.fetchone()
    conn.close()

    if device:
        device_dict = dict(device)
        if device_dict.get("metadata"):
            device_dict["metadata"] = json.loads(device_dict["metadata"])
        return device_dict
    return None


def get_all_devices_metadata() -> List[Dict]:
    """Получение метаданных всех устройств"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM devices")
    devices = []
    for device in cursor.fetchall():
        device_dict = dict(device)
        if device_dict.get("metadata"):
            device_dict["metadata"] = json.loads(device_dict["metadata"])
        devices.append(device_dict)
    conn.close()

    return devices


def create_lab(title: str, description: str, content: Dict, created_by: int) -> int:
    """Создание новой лабораторной работы"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO labs (title, description, content, created_by) VALUES (?, ?, ?, ?)",
        (title, description, json.dumps(content), created_by)
    )
    lab_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return lab_id


def get_lab(lab_id: int) -> Optional[Dict]:
    """Получение лабораторной работы по ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM labs WHERE id = ?", (lab_id,))
    lab = cursor.fetchone()

    if not lab:
        conn.close()
        return None

    lab_dict = dict(lab)
    lab_dict['content'] = json.loads(lab_dict['content'])

    # Получаем задания для лабораторной работы
    cursor.execute(
        "SELECT * FROM lab_tasks WHERE lab_id = ? ORDER BY order_index", (lab_id,))
    tasks = []
    for task in cursor.fetchall():
        task_dict = dict(task)
        task_dict['content'] = json.loads(task_dict['content'])

        # Получаем устройства для задания
        cursor.execute(
            "SELECT * FROM task_devices WHERE task_id = ?", (task_dict['id'],))
        devices = []
        for device in cursor.fetchall():
            device_dict = dict(device)
            if device_dict['required_state']:
                device_dict['required_state'] = json.loads(
                    device_dict['required_state'])
            devices.append(device_dict)

        task_dict['devices'] = devices
        tasks.append(task_dict)

    lab_dict['tasks'] = tasks
    conn.close()

    return lab_dict


def get_all_labs() -> List[Dict]:
    """Получение списка всех лабораторных работ"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM labs")
    labs = []
    for lab in cursor.fetchall():
        lab_dict = dict(lab)
        lab_dict['content'] = json.loads(lab_dict['content'])
        labs.append(lab_dict)
    conn.close()

    return labs


def update_lab(lab_id: int, data: Dict) -> bool:
    """Обновление лабораторной работы"""
    fields = []
    values = []

    if 'title' in data and data['title']:
        fields.append("title = ?")
        values.append(data['title'])

    if 'description' in data and data['description'] is not None:
        fields.append("description = ?")
        values.append(data['description'])

    if 'content' in data and data['content'] is not None:
        fields.append("content = ?")
        values.append(json.dumps(data['content']))

    fields.append("updated_at = ?")
    values.append(datetime.now().isoformat())

    if not fields:
        return False

    values.append(lab_id)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE labs SET {', '.join(fields)} WHERE id = ?",
        values
    )
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return success


def delete_lab(lab_id: int) -> bool:
    """Удаление лабораторной работы"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM labs WHERE id = ?", (lab_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return success


def create_task(lab_id: int, title: str, description: str, task_type: str, content: Dict, order_index: int, max_score: float) -> int:
    """Создание нового задания для лабораторной работы"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO lab_tasks (lab_id, title, description, task_type, content, order_index, max_score) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (lab_id, title, description, task_type,
         json.dumps(content), order_index, max_score)
    )
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return task_id


def update_task(task_id: int, data: Dict) -> bool:
    """Обновление задания"""
    fields = []
    values = []

    if 'title' in data and data['title']:
        fields.append("title = ?")
        values.append(data['title'])

    if 'description' in data and data['description'] is not None:
        fields.append("description = ?")
        values.append(data['description'])

    if 'content' in data and data['content'] is not None:
        fields.append("content = ?")
        values.append(json.dumps(data['content']))

    if 'order_index' in data and data['order_index'] is not None:
        fields.append("order_index = ?")
        values.append(data['order_index'])

    if 'max_score' in data and data['max_score'] is not None:
        fields.append("max_score = ?")
        values.append(data['max_score'])

    if not fields:
        return False

    values.append(task_id)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE lab_tasks SET {', '.join(fields)} WHERE id = ?",
        values
    )
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return success


def delete_task(task_id: int) -> bool:
    """Удаление задания"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM lab_tasks WHERE id = ?", (task_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return success


def add_device_to_task(task_id: int, device_id: str, required_state: Optional[Dict] = None) -> int:
    """Добавление устройства к заданию"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO task_devices (task_id, device_id, required_state) VALUES (?, ?, ?)",
        (task_id, device_id, json.dumps(required_state) if required_state else None)
    )
    device_task_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return device_task_id


def remove_device_from_task(task_id: int, device_id: str) -> bool:
    """Удаление устройства из задания"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM task_devices WHERE task_id = ? AND device_id = ?",
        (task_id, device_id)
    )
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return success


def create_lab_result(lab_id: int, user_id: int) -> int:
    """Создание результата выполнения лабораторной работы"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO lab_results (lab_id, user_id) VALUES (?, ?)",
        (lab_id, user_id)
    )
    result_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return result_id


def get_lab_result(result_id: int) -> Optional[Dict]:
    """Получение результата выполнения лабораторной работы по ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lab_results WHERE id = ?", (result_id,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return None

    result_dict = dict(result)

    # Получаем результаты заданий
    cursor.execute(
        "SELECT * FROM task_results WHERE lab_result_id = ?", (result_id,))
    task_results = []
    for task_result in cursor.fetchall():
        task_result_dict = dict(task_result)
        if task_result_dict['answer']:
            task_result_dict['answer'] = json.loads(task_result_dict['answer'])
        task_results.append(task_result_dict)

    result_dict['task_results'] = task_results
    conn.close()

    return result_dict


def get_lab_results_by_user(user_id: int) -> List[Dict]:
    """Получение результатов выполнения лабораторных работ пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lab_results WHERE user_id = ?", (user_id,))
    results = []
    for result in cursor.fetchall():
        result_dict = dict(result)
        results.append(result_dict)
    conn.close()

    return results


def get_lab_results_by_lab(lab_id: int) -> List[Dict]:
    """Получение результатов выполнения лабораторной работы"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lab_results WHERE lab_id = ?", (lab_id,))
    results = []
    for result in cursor.fetchall():
        result_dict = dict(result)
        results.append(result_dict)
    conn.close()

    return results


def update_lab_result(result_id: int, data: Dict) -> bool:
    """Обновление результата выполнения лабораторной работы"""
    fields = []
    values = []

    if 'status' in data and data['status']:
        fields.append("status = ?")
        values.append(data['status'])

        if data['status'] == 'submitted' and 'submitted_at' not in data:
            fields.append("submitted_at = ?")
            values.append(datetime.now().isoformat())

    if 'submitted_at' in data and data['submitted_at'] is not None:
        fields.append("submitted_at = ?")
        values.append(data['submitted_at'])

    if 'score' in data and data['score'] is not None:
        fields.append("score = ?")
        values.append(data['score'])

    if 'feedback' in data and data['feedback'] is not None:
        fields.append("feedback = ?")
        values.append(data['feedback'])

    if 'reviewed_by' in data and data['reviewed_by'] is not None:
        fields.append("reviewed_by = ?")
        values.append(data['reviewed_by'])
        fields.append("reviewed_at = ?")
        values.append(datetime.now().isoformat())

    if not fields:
        return False

    values.append(result_id)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE lab_results SET {', '.join(fields)} WHERE id = ?",
        values
    )
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return success


def create_task_result(lab_result_id: int, task_id: int, answer: Optional[Dict] = None) -> int:
    """Создание результата выполнения задания"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO task_results (lab_result_id, task_id, answer) VALUES (?, ?, ?)",
        (lab_result_id, task_id, json.dumps(answer) if answer else None)
    )
    task_result_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return task_result_id


def update_task_result(task_result_id: int, data: Dict) -> bool:
    """Обновление результата выполнения задания"""
    fields = []
    values = []

    if 'answer' in data and data['answer'] is not None:
        fields.append("answer = ?")
        values.append(json.dumps(data['answer']))

    if 'score' in data and data['score'] is not None:
        fields.append("score = ?")
        values.append(data['score'])

    if 'feedback' in data and data['feedback'] is not None:
        fields.append("feedback = ?")
        values.append(data['feedback'])

    if not fields:
        return False

    values.append(task_result_id)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE task_results SET {', '.join(fields)} WHERE id = ?",
        values
    )
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return success
