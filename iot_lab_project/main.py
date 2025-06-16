from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, QTextStream
from ui.dialogs.login_dialog import LoginDialog
from ui.dialogs.server_connection_dialog import ServerConnectionDialog
from ui.Main.main_window import MainWindow
from core.api import api_client
from core.logger import get_logger
from db.connection_db import HAConnectionDB
import sys

logger = get_logger()


def load_stylesheet():
    file = QFile(":/style/style.qss")
    if file.open(QFile.ReadOnly | QFile.Text):
        return QTextStream(file).readAll()
    return ""


def load_connection_settings():
    """Загрузка настроек подключения из базы данных"""
    db = HAConnectionDB()
    api_connections = db.get_all_custom_api_connections()

    if api_connections:
        # Берем первое подключение из списка
        conn = api_connections[0]
        url = conn["url"]
        api_key = conn["api_key"]

        # Настраиваем API клиент
        api_client.configure(url, api_key)
        return True
    return False


if __name__ == "__main__":
    logger.info("Запуск приложения")
    app = QApplication(sys.argv)
    app.setStyleSheet(load_stylesheet())

    # Инициализируем базу данных
    db = HAConnectionDB()

    # Загружаем настройки подключения
    has_connection = load_connection_settings()

    # Показываем диалог подключения к серверу
    logger.info("Отображение диалога подключения к серверу")
    connection_dialog = ServerConnectionDialog()
    if connection_dialog.exec() != ServerConnectionDialog.Accepted:
        # Если пользователь отменил подключение, завершаем приложение
        logger.info(
            "Пользователь отменил подключение к серверу, завершение приложения")
        sys.exit(0)

    # Проверяем соединение с сервером
    if not api_client.check_connection():
        logger.error("Не удалось подключиться к серверу")
        sys.exit(0)

    # Если подключение успешно, показываем диалог входа
    logger.info("Отображение диалога входа")
    login_dialog = LoginDialog()
    if login_dialog.exec() == LoginDialog.Accepted:
        user = login_dialog.user_data
        token = login_dialog.token

        logger.info(f"Вход пользователя: {user.get('login')}")

        # Устанавливаем токен в API клиенте
        if token:
            api_client.set_token(token)

        logger.info("Создание и отображение главного окна")
        window = MainWindow(user_data=user)
        window.show()

        # Запускаем главный цикл приложения
        logger.info("Запуск главного цикла приложения")
        sys.exit(app.exec())
    else:
        # Если пользователь отменил вход, завершаем приложение
        logger.info("Пользователь отменил вход, завершение приложения")
        sys.exit(0)
