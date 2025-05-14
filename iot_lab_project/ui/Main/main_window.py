from PySide6.QtWidgets import QMainWindow, QPushButton, QFrame, QMessageBox, QDialog
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize

from ui.Main.main_ui import Ui_MainWindow
from ui.dialogs.login_dialog import LoginDialog
from ui.dialogs.user_dialog import UserDialog
from ui.dialogs.connection_dialog import ConnectionDialog
from ui.dialogs.device_dialog import DeviceDialog
from ui.panels.devices_panel import DevicesPanel
from ui.panels.users_panel import UsersPanel
from core.ha.device_manager import DeviceManager
from db.connection_db import HAConnectionDB
from db.users_db import UserDB
from core.logger import get_logger
from core.workers.connection_worker import ConnectionWorker
from core.workers.device_loader import DeviceLoader

class MainWindow(QMainWindow):
    def __init__(self, user_data=None):
        super().__init__()
        self.user_data = user_data or {}
        self.role = self.user_data.get("role", "student")
        self.db = HAConnectionDB()
        self.logger = get_logger()

        self.ws_client = None
        self.rest_client = None
        self.entity_manager = None
        self.device_manager = None
        self.selected_connection = None
        self.entity_widgets = {}

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

    def _init_ui(self):
        self.devices_panel = DevicesPanel()
        self.ui.layoutDeviceList.setContentsMargins(0, 0, 0, 0)
        self.ui.layoutDeviceList.addWidget(self.devices_panel)
        self.devices_panel.device_selected.connect(self._open_device_dialog)

    def _connect_signals(self):
        self.ui.btnConnect.clicked.connect(self._connect_to_selected)
        self.ui.btnGetDevices.clicked.connect(self._load_devices)
        self.ui.btnConnectSettings.clicked.connect(self._open_connection_settings)

    def _setup_top_panel(self):
        layout = self.ui.horizontalLayoutTopInfo

        # Удалить все виджеты
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        # === Снова добавить подключение и настройки ===
        layout.addWidget(self.ui.connectionStatus)
        layout.addWidget(self.ui.comboConnections)
        layout.addWidget(self.ui.btnConnectSettings)

        # === Блок пользователя ===
        name = self.user_data.get("login", "admin") if self.role == "admin" else \
            f"{self.user_data.get('last_name', '')} {self.user_data.get('first_name', '')}".strip()
        role_label = {
            "admin": "Администратор",
            "teacher": "Преподаватель",
            "student": "Студент"
        }.get(self.role, "Пользователь")

        self.user_info_btn = QPushButton(f"{name} ({role_label})")
        self.user_info_btn.setFlat(True)
        self.user_info_btn.clicked.connect(self._edit_profile)

        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)

        logout_btn = QPushButton("Выйти")
        logout_btn.setObjectName("logoutButton")
        logout_btn.clicked.connect(self._logout)

        layout.addWidget(self.user_info_btn)
        layout.addWidget(separator)
        layout.addWidget(logout_btn)

    def _edit_profile(self):
        dialog = UserDialog(mode="profile", user_data=self.user_data, parent=self)
        dialog.user_saved.connect(self.update_user_profile)
        dialog.exec()

    def update_user_profile(self, user_data):
        if user_data["id"] == self.user_data.get("id"):
            self.user_data = user_data
            self.role = user_data.get("role", "student")
            self._setup_top_panel()
            self._setup_tabs_by_role()
            self._refresh_logs()

    def _setup_tabs_by_role(self):
        tab = self.ui.tabWidgetMain
        while tab.count():
            tab.removeTab(0)

        if self.role == "admin":
            users_panel = UsersPanel(parent=self)
            tab.addTab(users_panel, QIcon(":/icon/icons/user_manage.png"), "Пользователи")
            tab.addTab(self.ui.scrollAreaDevices.parentWidget(), QIcon(":/icon/icons/devices.png"), "Устройства")
        elif self.role in ("teacher", "student"):
            tab.addTab(self._create_labs_stub(), QIcon(":/icon/icons/info.png"), "Лабораторные")
            tab.addTab(self.ui.scrollAreaDevices.parentWidget(), QIcon(":/icon/icons/devices.png"), "Устройства")

        tab.addTab(self.ui.tabLogs, QIcon(":/icon/icons/log.png"), "Журнал")

    def _create_labs_stub(self):
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addWidget(QLabel("Лабораторные работы (в разработке)"))
        return w

    def _load_connections(self):
        current_id = self.selected_connection["id"] if self.selected_connection else None
        connections = self.db.get_all_connections()

        self.ui.comboConnections.clear()
        for index, conn in enumerate(connections):
            self.ui.comboConnections.addItem(conn["name"], conn)
            if conn["id"] == current_id:
                self.ui.comboConnections.setCurrentIndex(index)

    def _open_connection_settings(self):
        if ConnectionDialog(self).exec() == QDialog.Accepted:
            self._load_connections()

    def _connect_to_selected(self):
        index = self.ui.comboConnections.currentIndex()
        conn_data = self.ui.comboConnections.itemData(index)
        if not conn_data:
            QMessageBox.warning(self, "Ошибка", "Выберите подключение.")
            return

        self.selected_connection = conn_data
        self._update_connection_status(icon="loading", tooltip="Подключение...")
        self.logger.info("Подключение к Home Assistant...")
        self._refresh_logs()

        worker = ConnectionWorker(conn_data["url"], conn_data["token"])
        worker.connection_success.connect(self._on_connected)
        worker.connection_failed.connect(self._on_connection_error)
        worker.state_changed.connect(self._on_entity_state_changed)
        worker.start()
        self.connection_worker = worker

    def _on_connected(self, ws, rest, entity, device, url):
        self.ws_client, self.rest_client = ws, rest
        self.entity_manager, self.device_manager = entity, device
        self._update_connection_status(success=True)
        self.logger.success(f"Подключено к {url}")
        self._refresh_logs()

    def _on_connection_error(self, error):
        self._update_connection_status(disconnected=True)
        self.logger.error(f"Ошибка подключения: {error}")
        self._refresh_logs()

    def _update_connection_status(self, success=False, disconnected=False, icon=None, tooltip=None):
        if icon is None:
            icon = "connected" if success else "disconnected" if disconnected else "loading"
        if tooltip is None:
            tooltip = {
                "connected": "Подключено",
                "disconnected": "Не подключено",
                "loading": "Подключение..."
            }.get(icon, "")
        self.ui.connectionStatus.setIcon(QIcon(f":/icon/icons/{icon}.png"))
        self.ui.connectionStatus.setToolTip(tooltip)

    def _load_devices(self):
        if not self.device_manager:
            self.logger.error("Нет подключения к устройствам.")
            self._refresh_logs()
            return

        self.logger.info("Загрузка устройств...")
        self._refresh_logs()

        self.devices_panel.clear_devices()
        self.devices_panel.show_loading_indicator("Загрузка устройств...")

        loader = DeviceLoader(self.device_manager)
        loader.devices_loaded.connect(self.devices_panel.update_devices)
        loader.error.connect(self._on_device_load_error)
        loader.start()
        self.device_loader = loader

    def _on_device_load_error(self, error):
        self.logger.error(f"Ошибка загрузки устройств: {error}")
        self._refresh_logs()

    def _open_device_dialog(self, device):
        dialog = DeviceDialog(device, self.entity_manager, parent=self)
        for entity in device["entities"]:
            eid = entity.get("entity_id")
            widget = dialog.entity_widgets.get(eid)
            if eid and widget:
                self.entity_widgets[eid] = widget
        dialog.exec()
        for eid in [e.get("entity_id") for e in device["entities"]]:
            self.entity_widgets.pop(eid, None)

    def _on_entity_state_changed(self, entity_id: str, new_state: dict):
        widget = self.entity_widgets.get(entity_id)
        if widget:
            widget.update_state(new_state)
            self.logger.info(f"[UI] Обновлено: {entity_id} → {new_state.get('state')}")
            self._refresh_logs()

    def _refresh_logs(self):
        self.ui.textEditLogs.setHtml(self.logger.get_text_log())
        bar = self.ui.textEditLogs.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _logout(self):
        login_dialog = LoginDialog()
        if login_dialog.exec() == QDialog.Accepted:
            self.user_data = login_dialog.user_data
            self.role = self.user_data.get("role", "student")
            
            # Сброс подключения при смене пользователя 
            # self.ws_client = None
            # self.rest_client = None
            # self.entity_manager = None
            # self.device_manager = None
            # self.selected_connection = None
            # self.entity_widgets = {}
            # self._update_connection_status(disconnected=True)
            
            self._setup_top_panel()
            self._setup_tabs_by_role()
            self.logger = get_logger()
            self._refresh_logs()
            if hasattr(self, "devices_panel"):
                self.devices_panel.clear_devices()