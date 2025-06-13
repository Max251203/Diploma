from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, QTextStream, QSettings
from ui.dialogs.login_dialog import LoginDialog
from ui.Main.main_window import MainWindow
from core.api import api_client
from core.logger import get_logger

logger = get_logger()


def load_stylesheet():
    file = QFile(":/style/style.qss")
    if file.open(QFile.ReadOnly | QFile.Text):
        return QTextStream(file).readAll()
    return ""


def load_connection_settings():
    """Загрузка настроек подключения"""
    settings = QSettings("IoTLab", "Connection")
    url = settings.value("url", "")
    api_key = settings.value("api_key", "")

    if url and api_key:
        # Настраиваем API клиент
        api_client.configure(url, api_key)
        return True
    return False


def load_saved_auth():
    """Загрузка сохраненных данных аутентификации"""
    settings = QSettings("IoTLab", "Auth")
    token = settings.value("token", "")
    user_id = settings.value("user_id", 0)

    if token and user_id and load_connection_settings():
        # Устанавливаем токен
        api_client.set_token(token)

        # Проверяем соединение
        if api_client.check_connection():
            # Получаем информацию о пользователе
            user = api_client.get_current_user()
            if user:
                return user

    return None


if __name__ == "__main__":
    app = QApplication([])
    app.setStyleSheet(load_stylesheet())

    # Загружаем настройки подключения в любом случае
    load_connection_settings()

    # Пытаемся загрузить сохраненные данные аутентификации
    user_data = load_saved_auth()

    if user_data:
        # Если есть сохраненные данные, сразу открываем главное окно
        logger.info(
            f"Автоматический вход пользователя: {user_data.get('login')}")
        window = MainWindow(user_data=user_data)
        window.show()
    else:
        # Иначе показываем диалог входа
        login = LoginDialog()
        if login.exec() == LoginDialog.Accepted:
            user = login.user_data
            token = login.token
            is_guest = login.is_guest_mode

            if is_guest:
                logger.info("Вход в режиме гостя")
            else:
                logger.info(f"Вход пользователя: {user.get('login')}")

            # Устанавливаем токен в API клиенте, если не гостевой режим
            if token and not is_guest:
                api_client.set_token(token)

            window = MainWindow(user_data=user)
            window.show()
        else:
            # Если пользователь отменил вход, завершаем приложение
            app.quit()
            exit(0)

    app.exec()
