from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QFrame, QDialog, QMessageBox, QTabWidget,
    QTableWidgetItem
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QTimer, QSettings
from ui.Main.main_ui import Ui_MainWindow
from ui.dialogs.login_dialog import LoginDialog
from ui.dialogs.user_dialog import UserDialog
from ui.dialogs.connection_dialog import ConnectionDialog
from ui.dialogs.device_dialog import DeviceDialog
from ui.dialogs.booking_dialog import BookingDialog
from ui.panels.devices_panel import DevicesPanel
from ui.panels.users_panel import UsersPanel
from ui.panels.lab.lab_browser_panel import LabBrowserPanel
from ui.panels.lab.lab_editor_panel import LabEditorPanel
from ui.panels.lab.lab_results_panel import LabResultsPanel
from core.logger import get_logger
from core.api import api_client
from core.api.api_worker import (
    GetDevicesWorker, GetDeviceWorker, SendDeviceCommandWorker
)
from core.booking import booking_manager
from core.permissions import has_permission, Permission, get_role_label
import websocket
import json
import threading


class MainWindow(QMainWindow):
    def __init__(self, user_data=None):
        super().__init__()
        self.user_data = user_data or {}
        self.role = self.user_data.get("role", "student")
        self.logger = get_logger()

        self.ws_client = None
        self.ws_thread = None
        self.entity_widgets = {}
        self._last_tabbar_state = None
        self._workers = []  # Список для хранения рабочих потоков

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setGeometry(100, 100, 900, 600)
        self.setWindowTitle("IoT Лаборатория")

        self._init_ui()
        self._connect_signals()
        self._setup_top_panel()
        self._setup_tabs_by_role()
        self._load_connections()
        self._update_connection_status(disconnected=True)

        # Запускаем WebSocket соединение, если пользователь авторизован
        if self.user_data and api_client.token:
            QTimer.singleShot(500, self._start_websocket)

    def _init_ui(self):
        self.devices_panel = DevicesPanel()
        self.ui.layoutDeviceList.setContentsMargins(0, 0, 0, 0)
        self.ui.layoutDeviceList.addWidget(self.devices_panel)
        self.devices_panel.device_selected.connect(self._open_device_dialog)

    def _connect_signals(self):
        self.ui.btnConnect.clicked.connect(self._connect_to_selected)
        self.ui.btnGetDevices.clicked.connect(self._load_devices)
        self.ui.btnConnectSettings.clicked.connect(
            self._open_connection_settings)
        self.ui.btnProfileLabel.clicked.connect(self._edit_profile)
        self.ui.btnLogout.clicked.connect(self._logout)
        self.ui.scrollAreaDevices.setVisible(True)

        # Подключаем сигналы от менеджера бронирования
        booking_manager.error_occurred.connect(self._show_error)

    def _setup_top_panel(self):
        name = self.user_data.get("login", "Пользователь")
        role = self.user_data.get("role", "student")

        if role == "admin":
            label = f"Администратор: {name}"
        else:
            last = self.user_data.get("last_name", "")
            first = self.user_data.get("first_name", "")
            middle = self.user_data.get("middle_name", "")
            initials = (first[:1] + "." if first else "") + \
                (middle[:1] + "." if middle else "")
            label = f"{get_role_label(role)}: {last} {initials}"

        self.ui.btnProfileLabel.setText(label)

    def _edit_profile(self):
        dialog = UserDialog(
            mode="profile", user_data=self.user_data, parent=self)
        dialog.user_saved.connect(self.update_user_profile)
        dialog.exec()

    def update_user_profile(self, data):
        if data["id"] == self.user_data.get("id"):
            self.user_data = data
            self.role = self.user_data.get("role", self.role)
            self._setup_top_panel()
            self._setup_tabs_by_role()
            self._refresh_logs()

    def _setup_tabs_by_role(self):
        tab = self.ui.tabWidgetMain

        # Сохраняем текущий индекс вкладки, если это не первый запуск
        current_index = tab.currentIndex()
        current_text = tab.tabText(
            current_index) if current_index >= 0 and self._last_tabbar_state else None

        tab.clear()

        # Определяем, является ли пользователь преподавателем или гостем
        is_teacher = self.role in ["admin", "teacher"]
        is_guest = self.role == "guest"

        # Добавляем вкладки в зависимости от роли
        if has_permission(self.role, Permission.ACCESS_DEVICES) or is_guest:
            tab.addTab(self.ui.scrollAreaDevices.parentWidget(),
                       QIcon(":/icon/icons/devices.png"), "Устройства")

        if has_permission(self.role, Permission.ACCESS_LABS) or is_guest:
            # Для преподавателей показываем панель редактирования и результатов
            if is_teacher:
                labs_tab = QTabWidget()
                labs_tab.addTab(LabBrowserPanel(), "Просмотр")
                labs_tab.addTab(LabEditorPanel(), "Редактирование")
                labs_tab.addTab(LabResultsPanel(), "Результаты")
                tab.addTab(labs_tab, QIcon(
                    ":/icon/icons/info.png"), "Лабораторные")
            else:
                # Для студентов и гостей только просмотр
                tab.addTab(LabBrowserPanel(), QIcon(
                    ":/icon/icons/info.png"), "Лабораторные")

        if has_permission(self.role, Permission.VIEW_LOGS) or is_guest:
            tab.addTab(self.ui.tabLogs, QIcon(
                ":/icon/icons/log.png"), "Журнал")

        if has_permission(self.role, Permission.MANAGE_USERS) and not is_guest:
            tab.addTab(UsersPanel(parent=self), QIcon(
                ":/icon/icons/user_manage.png"), "Пользователи")

        # Восстанавливаем вкладку, если возможно
        if current_text:
            for i in range(tab.count()):
                if tab.tabText(i) == current_text:
                    tab.setCurrentIndex(i)
                    break

        # Запоминаем, что табы уже были настроены
        self._last_tabbar_state = True

    def _load_connections(self):
        self.ui.comboConnections.clear()

        # Получаем сохраненные настройки подключения
        settings = self._load_connection_settings()

        if settings:
            self.ui.comboConnections.addItem(
                f"Сервер: {settings.get('url', '')}", settings)
        else:
            self.ui.comboConnections.addItem(
                "Настройте подключение к серверу", None)

    def _load_connection_settings(self):
        """Загрузка настроек подключения из локального хранилища"""
        from PySide6.QtCore import QSettings

        settings = QSettings("IoTLab", "Connection")
        url = settings.value("url", "")
        api_key = settings.value("api_key", "")

        if url and api_key:
            return {"url": url, "api_key": api_key}

        return None

    def _save_connection_settings(self, url: str, api_key: str):
        """Сохранение настроек подключения в локальное хранилище"""
        from PySide6.QtCore import QSettings

        settings = QSettings("IoTLab", "Connection")
        settings.setValue("url", url)
        settings.setValue("api_key", api_key)

    def _open_connection_settings(self):
        """Открытие диалога настроек подключения"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QHBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("Настройки подключения к серверу")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        form = QFormLayout()

        # Загружаем текущие настройки
        settings = QSettings("IoTLab", "Connection")
        url = settings.value("url", "")
        api_key = settings.value("api_key", "")

        url_edit = QLineEdit(url)
        url_edit.setPlaceholderText("http://localhost:8000")
        form.addRow("URL сервера:", url_edit)

        api_key_edit = QLineEdit(api_key)
        api_key_edit.setPlaceholderText("API ключ")
        form.addRow("API ключ:", api_key_edit)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(lambda: self._save_connection(
            dialog, url_edit.text(), api_key_edit.text()))
        buttons.addWidget(save_btn)

        test_btn = QPushButton("Проверить соединение")
        test_btn.clicked.connect(lambda: self._test_connection(
            url_edit.text(), api_key_edit.text()))
        buttons.addWidget(test_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addWidget(cancel_btn)

        layout.addLayout(buttons)

        dialog.exec()

    def _save_connection(self, dialog, url: str, api_key: str):
        """Сохранение настроек подключения"""
        if not url or not api_key:
            QMessageBox.warning(dialog, "Ошибка", "Заполните все поля")
            return

        settings = QSettings("IoTLab", "Connection")
        settings.setValue("url", url)
        settings.setValue("api_key", api_key)

        api_client.configure(url, api_key)

        dialog.accept()

        # Проверяем подключение
        if api_client.check_connection():
            self._update_connection_status(success=True)
            QMessageBox.information(
                self, "Успех", "Соединение с сервером установлено")
        else:
            self._update_connection_status(disconnected=True)
            QMessageBox.warning(
                self, "Ошибка", "Не удалось подключиться к серверу")

    def _test_connection(self, url: str, api_key: str):
        """Проверка соединения с сервером"""
        if not url or not api_key:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return

        # Временно настраиваем API клиент
        api_client.configure(url, api_key)

        # Проверяем соединение
        if api_client.check_connection():
            QMessageBox.information(
                self, "Успех", "Соединение с сервером установлено")
        else:
            QMessageBox.critical(
                self, "Ошибка", "Не удалось подключиться к серверу")

    def _connect_to_selected(self):
        """Подключение к выбранному серверу"""
        settings = self.ui.comboConnections.currentData()
        if not settings:
            QMessageBox.warning(self, "Ошибка", "Выберите подключение")
            return

        self._update_connection_status(
            icon="loading", tooltip="Подключение...")

        # Настраиваем API клиент
        api_client.configure(settings["url"], settings["api_key"])

        # Проверяем соединение
        if api_client.check_connection():
            self._update_connection_status(success=True)
            self.logger.success(f"Подключено к {settings['url']}")

            # Если пользователь авторизован, запускаем WebSocket
            if self.user_data and api_client.token:
                self._start_websocket()
        else:
            self._update_connection_status(disconnected=True)
            self.logger.error(f"Ошибка подключения к {settings['url']}")
            QMessageBox.warning(
                self, "Ошибка", "Не удалось подключиться к серверу")

        self._refresh_logs()

    def _start_websocket(self):
        """Запуск WebSocket соединения"""
        # Останавливаем предыдущее соединение, если есть
        if self.ws_client:
            try:
                self.ws_client.close()
            except:
                pass
            self.ws_client = None

        if self.ws_thread and self.ws_thread.is_alive():
            try:
                self.ws_thread.join(timeout=1)
            except:
                pass
            self.ws_thread = None

        # Получаем URL для WebSocket
        ws_url = api_client.get_websocket_url()

        # Создаем новое соединение
        self.ws_client = websocket.WebSocketApp(
            ws_url,
            on_open=self._on_ws_open,
            on_message=self._on_ws_message,
            on_error=self._on_ws_error,
            on_close=self._on_ws_close
        )

        # Запускаем WebSocket в отдельном потоке
        self.ws_thread = threading.Thread(target=self.ws_client.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()

        self.logger.info(f"WebSocket соединение запущено: {ws_url}")

    def _on_ws_open(self, ws):
        """Обработчик открытия WebSocket соединения"""
        self.logger.info("WebSocket соединение установлено")

        # Отправляем пинг для проверки соединения
        ws.send(json.dumps({"type": "ping"}))

    def _on_ws_message(self, ws, message):
        """Обработчик сообщений WebSocket"""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "pong":
                self.logger.debug("Получен pong от сервера")

            elif message_type == "device_update":
                # Обновление состояния устройства
                device_id = data.get("device_id")
                state = data.get("state")
                if device_id and state:
                    self.logger.info(
                        f"Получено обновление устройства {device_id}")
                    self.devices_panel.update_device_state(device_id, state)

            elif message_type == "booking_notification":
                # Уведомление о бронировании
                action = data.get("action")
                device_id = data.get("device_id")
                booking_data = data.get("data", {})

                if action == "created":
                    self.logger.info(f"Устройство {device_id} забронировано")
                elif action == "updated":
                    self.logger.info(
                        f"Бронирование устройства {device_id} обновлено")
                elif action == "cancelled":
                    self.logger.info(
                        f"Бронирование устройства {device_id} отменено")

                # Обновляем информацию о бронированиях
                booking_manager.get_user_bookings()

            elif message_type == "notification":
                # Системное уведомление
                title = data.get("title", "Уведомление")
                message = data.get("message", "")
                level = data.get("level", "info")

                self.logger.info(f"Получено уведомление: {title} - {message}")

                # Показываем уведомление пользователю
                icon = QMessageBox.Information
                if level == "warning":
                    icon = QMessageBox.Warning
                elif level == "error":
                    icon = QMessageBox.Critical
                elif level == "success":
                    icon = QMessageBox.Information

                QTimer.singleShot(100, lambda: QMessageBox.information(
                    self, title, message, icon))

            self._refresh_logs()

        except json.JSONDecodeError:
            self.logger.error(f"Ошибка разбора JSON: {message}")
        except Exception as e:
            self.logger.error(f"Ошибка обработки сообщения WebSocket: {e}")

    def _on_ws_error(self, ws, error):
        """Обработчик ошибок WebSocket"""
        self.logger.error(f"Ошибка WebSocket: {error}")

    def _on_ws_close(self, ws, close_status_code, close_msg):
        """Обработчик закрытия WebSocket соединения"""
        self.logger.warning(
            f"WebSocket соединение закрыто: {close_msg} (код: {close_status_code})")

    def _update_connection_status(self, success=False, disconnected=False, icon=None, tooltip=None):
        status_text = ""
        if success:
            status_text = "Подключено"
        elif disconnected:
            status_text = "Не подключено"
        else:
            status_text = "Подключение..."

        if tooltip is None:
            tooltip = status_text

        # Обновляем только текст статуса, без иконки
        self.ui.connectionStatusText.setText(status_text)
        self.ui.connectionStatusText.setToolTip(tooltip)

        # Обновляем стиль в зависимости от статуса
        if success:
            self.ui.connectionStatusText.setStyleSheet(
                "color: #00ff00;")  # Зеленый для подключено
        elif disconnected:
            self.ui.connectionStatusText.setStyleSheet(
                "color: #ff5e2c;")  # Оранжевый для не подключено
        else:
            self.ui.connectionStatusText.setStyleSheet(
                "color: #ffbc00;")  # Желтый для подключения

    def _load_devices(self):
        if not api_client.is_connected():
            QMessageBox.warning(self, "Ошибка", "Нет активного подключения.")
            return

        self.logger.info("Загрузка устройств...")
        self._refresh_logs()
        self.devices_panel.clear_devices()
        self.devices_panel.show_loading_indicator("Загрузка устройств...")

        # Используем API Worker для асинхронной загрузки
        worker = GetDevicesWorker(api_client)
        worker.result_ready.connect(self._on_devices_loaded)
        worker.error_occurred.connect(self._show_error)
        self._workers.append(worker)  # Сохраняем ссылку на поток
        worker.start()

    def _on_devices_loaded(self, devices):
        """Обработка загруженных устройств"""
        if not devices:
            self.devices_panel.clear_devices()
            self.logger.error("Не удалось загрузить устройства")
            return

        # Преобразуем устройства в формат, понятный для DevicesPanel
        categorized_devices = self._categorize_devices(devices)

        # Обновляем панель устройств
        self.devices_panel.update_devices(categorized_devices)
        self.logger.success("Устройства успешно загружены")
        self._refresh_logs()

    def _categorize_devices(self, devices):
        """Категоризация устройств"""
        categories = {
            "Датчики": [],
            "Исполнительные устройства": [],
            "Системные": [],
            "Прочее": []
        }

        for device_id, device in devices.items():
            # Добавляем ID устройства в данные
            device_data = dict(device)
            device_data["id"] = device_id

            # Определяем категорию устройства
            category = self._determine_device_category(device_data)
            categories[category].append(device_data)

        return categories

    def _determine_device_category(self, device):
        """Определение категории устройства"""
        # Проверяем по модели
        model = (device.get("model") or "").lower()
        name = (device.get("name") or "").lower()

        # Проверяем по типу устройства
        if "sensor" in model or "temp" in model or "hum" in model or "motion" in model:
            return "Датчики"

        if "switch" in model or "relay" in model or "light" in model or "plug" in model:
            return "Исполнительные устройства"

        # Проверяем по имени
        if "sensor" in name or "датчик" in name:
            return "Датчики"

        if "switch" in name or "relay" in name or "light" in name or "plug" in name:
            return "Исполнительные устройства"

        # Проверяем по состоянию
        state = device.get("state", {})
        if isinstance(state, dict):
            if "temperature" in state or "humidity" in state or "motion" in state:
                return "Датчики"

            if "state" in state and state["state"] in ["ON", "OFF"]:
                return "Исполнительные устройства"

        # По умолчанию
        return "Прочее"

    def _open_device_dialog(self, device):
        """Открытие диалога устройства"""
        # Проверяем доступность устройства для бронирования
        device_id = device.get("id")

        # Получаем информацию о доступности устройства
        worker = GetDeviceWorker(api_client, device_id)
        worker.result_ready.connect(
            lambda device_info: self._show_device_dialog(device_info))
        worker.error_occurred.connect(self._show_error)
        self._workers.append(worker)  # Сохраняем ссылку на поток
        worker.start()

    def _show_device_dialog(self, device_info):
        """Отображение диалога устройства с учетом доступности"""
        if not device_info:
            QMessageBox.warning(
                self, "Ошибка", "Не удалось получить информацию об устройстве")
            return

        # Проверяем, доступно ли устройство для текущего пользователя
        device_id = device_info.get("id")

        # Получаем информацию о доступности устройства
        booking_manager.get_device_availability(device_id)

        # Создаем диалог устройства
        dialog = DeviceDialog(device_info, api_client, self)

        # Добавляем кнопку бронирования
        from PySide6.QtWidgets import QPushButton, QHBoxLayout

        booking_layout = QHBoxLayout()
        booking_btn = QPushButton("Забронировать устройство")
        booking_btn.clicked.connect(lambda: self._book_device(device_info))
        booking_layout.addWidget(booking_btn)

        # Добавляем кнопку просмотра бронирований
        view_bookings_btn = QPushButton("Просмотр бронирований")
        view_bookings_btn.clicked.connect(
            lambda: self._view_device_bookings(device_id))
        booking_layout.addWidget(view_bookings_btn)

        # Добавляем layout с кнопками в диалог
        dialog.layout().addLayout(booking_layout)

        dialog.exec()

    def _book_device(self, device):
        """Бронирование устройства"""
        device_id = device.get("id")
        device_name = device.get("name", device_id)

        dialog = BookingDialog(device_id, device_name, self)
        dialog.exec()

    def _view_device_bookings(self, device_id):
        """Просмотр бронирований устройства"""
        # Получаем очередь бронирований
        booking_manager.get_device_queue(device_id)

        # Создаем диалог для просмотра бронирований
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Бронирования устройства {device_id}")
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("<h3>Текущие бронирования устройства:</h3>"))

        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(
            ["Пользователь", "Начало", "Окончание", "Цель"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        layout.addWidget(table)

        # Подключаем сигнал обновления очереди
        booking_manager.device_queue_updated.connect(lambda dev_id, queue: self._update_bookings_table(
            table, dev_id, queue) if dev_id == device_id else None)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def _update_bookings_table(self, table, device_id, queue):
        """Обновление таблицы бронирований"""
        table.setRowCount(len(queue))

        for i, booking in enumerate(queue):
            # Пользователь
            user_item = QTableWidgetItem(
                f"{booking.get('user_login', '')} ({booking.get('user_id', '')})"
            )
            table.setItem(i, 0, user_item)

            # Время начала
            start_time = booking.get("start_time", "")
            start_item = QTableWidgetItem(start_time)
            table.setItem(i, 1, start_item)

            # Время окончания
            end_time = booking.get("end_time", "")
            end_item = QTableWidgetItem(end_time)
            table.setItem(i, 2, end_item)

            # Цель
            purpose = booking.get("purpose", "")
            purpose_item = QTableWidgetItem(purpose)
            table.setItem(i, 3, purpose_item)

    def _control_device(self, device_id: str, command: dict):
        """Отправляет команду управления устройством"""
        if not api_client.is_connected():
            self.logger.error(
                "Нет активного подключения для управления устройством")
            return

        worker = SendDeviceCommandWorker(api_client, device_id, command)
        worker.result_ready.connect(
            lambda success: self._on_command_sent(success, device_id, command))
        worker.error_occurred.connect(self._show_error)
        self._workers.append(worker)  # Сохраняем ссылку на поток
        worker.start()

    def _on_command_sent(self, success, device_id, command):
        """Обработка результата отправки команды"""
        if success:
            self.logger.success(f"Команда отправлена: {device_id} → {command}")
        else:
            self.logger.error(
                f"Ошибка отправки команды: {device_id} → {command}")

        self._refresh_logs()

    def _refresh_logs(self):
        self.ui.textEditLogs.setHtml(self.logger.get_text_log())
        self.ui.textEditLogs.verticalScrollBar().setValue(
            self.ui.textEditLogs.verticalScrollBar().maximum()
        )

    def _logout(self):
        # Закрываем WebSocket соединение
        if self.ws_client:
            try:
                self.ws_client.close()
            except:
                pass
            self.ws_client = None

        if self.ws_thread and self.ws_thread.is_alive():
            try:
                self.ws_thread.join(timeout=1)
            except:
                pass
            self.ws_thread = None

        # Сбрасываем токен в API клиенте
        api_client.set_token("")

        dialog = LoginDialog()
        if dialog.exec() == QDialog.Accepted:
            self.user_data = dialog.user_data
            self.role = self.user_data.get("role", "student")

            # Устанавливаем токен в API клиенте
            if dialog.token:
                api_client.set_token(dialog.token)

                # Запускаем WebSocket соединение
                if api_client.is_connected():
                    self._start_websocket()

            self._setup_top_panel()
            self._setup_tabs_by_role()
            self.logger = get_logger()
            self._refresh_logs()
            self.devices_panel.clear_devices()

    def _show_error(self, error: str):
        """Отображение ошибки"""
        QMessageBox.critical(self, "Ошибка", error)
        self.logger.error(error)
        self._refresh_logs()

    def closeEvent(self, event):
        # Корректно останавливаем WebSocket поток
        if self.ws_client:
            try:
                self.ws_client.close()
            except Exception:
                pass
            self.ws_client = None

        if self.ws_thread and self.ws_thread.is_alive():
            try:
                self.ws_thread.join(timeout=2)
            except Exception:
                pass
            self.ws_thread = None

        # Очищаем рабочие потоки менеджера бронирования
        booking_manager.cleanup_workers()

        # Останавливаем все активные потоки API
        for worker in getattr(self, "_workers", []):
            if worker.isRunning():
                worker.quit()
                worker.wait(1000)
                if worker.isRunning():
                    worker.terminate()

        # Очищаем потоки устройств
        if hasattr(self.devices_panel, "_workers"):
            for worker in self.devices_panel._workers:
                if worker.isRunning():
                    worker.quit()
                    worker.wait(1000)
                    if worker.isRunning():
                        worker.terminate()

        event.accept()
