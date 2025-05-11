from PySide6.QtWidgets import (
    QMainWindow, QDialog, QWidget, QPushButton, QLabel,
    QVBoxLayout, QFrame, QMessageBox
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize

from ui.windows.Main.main_ui import Ui_MainWindow
from ui.windows.Connection.connection_dialog import ConnectionDialog
from ui.windows.Device.device_dialog import DeviceDialog
from ui.windows.User.login_dialog import LoginDialog
from ui.windows.User.user_dialog import UserDialog  # универсальный диалог

from ui.panels.devices_panel import DevicesPanel
from ui.panels.users_panel import UsersPanel

from core.db.connection_db import HAConnectionDB
from core.workers.connection_worker import ConnectionWorker
from core.workers.device_loader import DeviceLoader
from utils.logger import get_logger
from ui.widgets.entity_widget import EntityWidget
from core.db.users_db import UserDB


class MainWindow(QMainWindow):
    def __init__(self, user_data=None):
        super().__init__()
        self.user_data = user_data or {}
        self.role = self.user_data.get("role", "student")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setGeometry(100, 100, 900, 600)
        self.setWindowTitle("IoT Лаборатория")

        self.logger = get_logger()
        self.db = HAConnectionDB()

        self.ws_client = None
        self.entity_manager = None
        self.device_manager = None
        self.selected_connection = None
        self.entity_widgets = {}

        self.setup_ui()
        self.load_connections()
        self.update_connection_status(disconnected=True)
        self.setup_tabs_by_role()

    def setup_ui(self):
        self.ui.btnConnectSettings.clicked.connect(self.open_connection_settings)
        self.ui.btnConnect.clicked.connect(self.connect_to_selected)
        self.ui.btnGetDevices.clicked.connect(self.load_devices)

        # 👤 Кнопка профиля
        self.user_info_btn = QPushButton()
        self.user_info_btn.setObjectName("userInfoButton")
        self.user_info_btn.setFlat(True)
        self.user_info_btn.clicked.connect(self.edit_profile)

        # Имя пользователя
        if self.role == "admin":
            name = self.user_data.get("login", "admin")
        else:
            name = f"{self.user_data.get('last_name', '')} {self.user_data.get('first_name', '')}".strip()

        role_label = {
            "admin": "Администратор",
            "teacher": "Преподаватель",
            "student": "Студент"
        }.get(self.role, "Пользователь")

        self.user_info_btn.setText(f"{name} ({role_label})")
        self.ui.horizontalLayoutTopInfo.addWidget(self.user_info_btn)

        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.ui.horizontalLayoutTopInfo.addWidget(separator)

        # 🔓 Кнопка "Выйти"
        self.logout_btn = QPushButton("Выйти")
        self.logout_btn.setObjectName("logoutButton")
        self.logout_btn.clicked.connect(self.logout)
        self.ui.horizontalLayoutTopInfo.addWidget(self.logout_btn)

    def edit_profile(self):
        dialog = UserDialog(mode="profile", user_data=self.user_data, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.user_data = UserDB().get_user_by_login(self.user_data["login"])
            QMessageBox.information(self, "Профиль", "Данные обновлены")

    def logout(self):
        login_dialog = LoginDialog()
        if login_dialog.exec() == QDialog.Accepted:
            user = login_dialog.user_data
            self.__init__(user_data=user)
            self.show()

    def setup_tabs_by_role(self):
        tab_widget = self.ui.tabWidgetMain
        while tab_widget.count():
            tab_widget.removeTab(0)

        if self.role == "admin":
            self.add_users_tab()
            self.add_devices_tab()  # 👈 вернуть устройства админу
            self.add_log_tab()
        elif self.role in ("teacher", "student"):
            self.add_labs_tab()
            self.add_devices_tab()
            self.add_log_tab()
        else:
            self.add_log_tab()

    def add_users_tab(self):
        users_tab = UsersPanel()
        self.ui.tabWidgetMain.addTab(users_tab, QIcon(":/icon/icons/user_manage.png"), "Пользователи")

    def add_labs_tab(self):
        labs_tab = QWidget()
        layout = QVBoxLayout(labs_tab)
        layout.addWidget(QLabel("Лабораторные работы (в разработке)"))
        self.ui.tabWidgetMain.addTab(labs_tab, QIcon(":/icon/icons/info.png"), "Лабораторные")

    def add_devices_tab(self):
        self.setup_devices_panel()
        self.ui.tabWidgetMain.addTab(self.ui.scrollAreaDevices.parentWidget(), QIcon(":/icon/icons/devices.png"), "Устройства")

    def add_log_tab(self):
        self.ui.tabWidgetMain.addTab(self.ui.tabLogs, QIcon(":/icon/icons/log.png"), "Журнал")

    def setup_devices_panel(self):
        layout = self.ui.layoutDeviceList
        layout.setContentsMargins(0, 0, 0, 0)

        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.devices_panel = DevicesPanel()
        self.devices_panel.device_selected.connect(self.open_device_details)
        layout.addWidget(self.devices_panel)

    def load_connections(self):
        current_id = self.selected_connection["id"] if self.selected_connection else None
        connections = self.db.get_all_connections()

        self.ui.comboConnections.clear()
        selected_index = 0

        for index, conn in enumerate(connections):
            self.ui.comboConnections.addItem(conn["name"], conn)
            if conn["id"] == current_id:
                selected_index = index

        self.ui.comboConnections.setCurrentIndex(selected_index)

    def open_connection_settings(self):
        dialog = ConnectionDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.load_connections()

    def connect_to_selected(self):
        index = self.ui.comboConnections.currentIndex()
        if index == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите подключение из списка.")
            return

        connection_data = self.ui.comboConnections.itemData(index)
        if not connection_data:
            QMessageBox.warning(self, "Ошибка", "Данные подключения не найдены.")
            return

        self.selected_connection = connection_data
        self._set_connection_status_icon("loading.png", "Подключение...")

        self.logger.info("Подключение к Home Assistant...")
        self._update_logs()

        self.connection_worker = ConnectionWorker(
            self.selected_connection["url"],
            self.selected_connection["token"]
        )
        self.connection_worker.connection_success.connect(self.on_connected)
        self.connection_worker.connection_failed.connect(self.on_connection_error)
        self.connection_worker.state_changed.connect(self.on_entity_state_changed)
        self.connection_worker.start()

    def on_connected(self, ws_client, rest_client, entity_manager, device_manager, ws_url):
        self.ws_client = ws_client
        self.rest_client = rest_client
        self.entity_manager = entity_manager
        self.device_manager = device_manager

        self.update_connection_status(success=True)
        self.logger.success(f"Подключение успешно установлено: {ws_url}")
        self._update_logs()

    def on_connection_error(self, error_message):
        self.update_connection_status(disconnected=True)
        self.logger.error(f"Ошибка подключения: {error_message}")
        self._update_logs()

    def update_connection_status(self, success=False, disconnected=False):
        if disconnected:
            self._set_connection_status_icon("disconnected.png", "Не подключено")
        elif success:
            self._set_connection_status_icon("connected.png", "Подключено")
        else:
            self._set_connection_status_icon("loading.png", "Подключение...")

    def _set_connection_status_icon(self, icon_file: str, tooltip: str):
        icon = QIcon(f":/icon/icons/{icon_file}")
        self.ui.connectionStatus.setIcon(icon)
        self.ui.connectionStatus.setToolTip(tooltip)

    def load_devices(self):
        if not self.device_manager:
            self.logger.error("Устройства не загружены — нет подключения")
            self._update_logs()
            return

        self.logger.info("Загрузка устройств...")
        self._update_logs()

        self.devices_panel.clear_devices()
        self.devices_panel.show_loading_indicator("Загрузка устройств...")

        self.device_loader = DeviceLoader(self.device_manager)
        self.device_loader.devices_loaded.connect(self.display_devices)
        self.device_loader.error.connect(self.on_device_load_error)
        self.device_loader.start()

    def display_devices(self, categorized):
        self.devices_panel.update_devices(categorized)

        total_devices = sum(len(devices) for devices in categorized.values())
        self.logger.success(f"Устройства загружены ({total_devices} шт.)")
        self._update_logs()

    def on_device_load_error(self, error):
        self.logger.error(f"Ошибка загрузки устройств: {error}")
        self._update_logs()

    def open_device_details(self, device):
        dialog = DeviceDialog(device, self.entity_manager, parent=self)

        for entity in device["entities"]:
            entity_id = entity.get("entity_id")
            widget = dialog.entity_widgets.get(entity_id)
            if entity_id and widget:
                self.entity_widgets[entity_id] = widget

        dialog.exec()

        for entity in device["entities"]:
            entity_id = entity.get("entity_id")
            if entity_id in self.entity_widgets:
                del self.entity_widgets[entity_id]

    def on_entity_state_changed(self, entity_id: str, new_state: dict):
        widget = self.entity_widgets.get(entity_id)
        if widget:
            widget.update_state(new_state)
            self.logger.info(f"[UI] Обновлено состояние: {entity_id} → {new_state.get('state')}")
            self._update_logs()

    def _update_logs(self):
        self.ui.textEditLogs.setHtml(self.logger.get_text_log())
        self.ui.textEditLogs.verticalScrollBar().setValue(
            self.ui.textEditLogs.verticalScrollBar().maximum()
        )