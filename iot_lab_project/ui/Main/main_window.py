from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QFrame, QDialog, QMessageBox
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from ui.Main.main_ui import Ui_MainWindow
from ui.dialogs.login_dialog import LoginDialog
from ui.dialogs.user_dialog import UserDialog
from ui.dialogs.connection_dialog import ConnectionDialog
from ui.dialogs.device_dialog import DeviceDialog
from ui.panels.devices_panel import DevicesPanel
from core.workers.device_loader import DeviceLoader
from db.connection_db import HAConnectionDB
from core.logger import get_logger
from core.workers.connection_worker import ConnectionWorker
from core.adapters.ha_adapter import HAAdapter
from core.adapters.api_adapter import APIAdapter
from core.permissions import has_permission, Permission, get_role_label


class MainWindow(QMainWindow):
    def __init__(self, user_data=None):
        super().__init__()
        self.user_data = user_data or {}
        self.role = self.user_data.get("role", "student")
        self.db = HAConnectionDB()
        self.logger = get_logger()

        self.adapter = None
        self.entity_widgets = {}
        self.connection_worker = None
        self._last_tabbar_state = None

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
        self.ui.btnConnectSettings.clicked.connect(
            self._open_connection_settings)
        self.ui.btnProfileLabel.clicked.connect(self._edit_profile)
        self.ui.btnLogout.clicked.connect(self._logout)
        self.ui.scrollAreaDevices.setVisible(True)

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

        # Добавляем вкладки как обычно
        if has_permission(self.role, Permission.MANAGE_USERS):
            from ui.panels.users_panel import UsersPanel
            tab.addTab(UsersPanel(parent=self), QIcon(
                ":/icon/icons/user_manage.png"), "Пользователи")

        if has_permission(self.role, Permission.ACCESS_LABS):
            tab.addTab(self._create_labs_stub(), QIcon(
                ":/icon/icons/info.png"), "Лабораторные")

        if has_permission(self.role, Permission.ACCESS_DEVICES):
            tab.addTab(self.ui.scrollAreaDevices.parentWidget(),
                       QIcon(":/icon/icons/devices.png"), "Устройства")

        # Специализированные вкладки для APIAdapter
        if isinstance(self.adapter, APIAdapter):
            from ui.panels.groups_panel import GroupsPanel
            from ui.panels.automations_panel import AutomationsPanel
            from ui.panels.network_panel import NetworkPanel
            from ui.panels.pairing_panel import PairingPanel

            tab.addTab(GroupsPanel(self.adapter), QIcon(
                ":/icon/icons/group.png"), "Группы")
            tab.addTab(AutomationsPanel(self.adapter), QIcon(
                ":/icon/icons/system.png"), "Автоматизации")
            tab.addTab(NetworkPanel(self.adapter), QIcon(
                ":/icon/icons/info.png"), "Сеть")
            tab.addTab(PairingPanel(self.adapter), QIcon(
                ":/icon/icons/connect.png"), "Сопряжение")

        if has_permission(self.role, Permission.VIEW_LOGS):
            tab.addTab(self.ui.tabLogs, QIcon(
                ":/icon/icons/log.png"), "Журнал")

        # Восстанавливаем вкладку, если возможно
        if current_text:
            for i in range(tab.count()):
                if tab.tabText(i) == current_text:
                    tab.setCurrentIndex(i)
                    break

        # Запоминаем, что табы уже были настроены
        self._last_tabbar_state = True

    def _create_labs_stub(self):
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addWidget(QLabel("Лабораторные работы (в разработке)"))
        return w

    def _load_connections(self):
        self.ui.comboConnections.clear()
        ha = self.db.get_all_connections()
        api = self.db.get_all_custom_api_connections()

        for conn in ha:
            self.ui.comboConnections.addItem(
                f"[HA] {conn['name']}", {"type": "ha", **conn})

        for conn in api:
            self.ui.comboConnections.addItem(
                f"[API] {conn['name']}", {"type": "api", **conn})

    def _open_connection_settings(self):
        if ConnectionDialog(self).exec() == QDialog.Accepted:
            self._load_connections()

    def _connect_to_selected(self):
        index = self.ui.comboConnections.currentIndex()
        conn_data = self.ui.comboConnections.itemData(index)
        if not conn_data or not isinstance(conn_data, dict):
            QMessageBox.warning(self, "Ошибка", "Выберите подключение.")
            return

        if self.connection_worker:
            self.connection_worker.quit()
            self.connection_worker.wait()
            self.connection_worker = None

        self.adapter = None
        self._update_connection_status(
            icon="loading", tooltip="Подключение...")

        conn_type = conn_data.get("type")

        if conn_type == "ha":
            self.logger.info("Подключение к Home Assistant...")
            worker = ConnectionWorker(conn_data["url"], conn_data["token"])
            worker.connection_success.connect(self._on_ha_connected)
            worker.connection_failed.connect(self._on_connection_error)
            self.connection_worker = worker
            worker.start()

        elif conn_type == "api":
            self.logger.info("Подключение к FastAPI")
            adapter = APIAdapter(
                conn_data["name"], conn_data["url"], conn_data["api_key"])
            if adapter.connect():
                self.adapter = adapter
                self._update_connection_status(success=True)
                self.logger.success("Подключение к API успешно.")
                self._setup_tabs_by_role()
            else:
                self._update_connection_status(disconnected=True)
                self.logger.error("Ошибка подключения к API.")

        self._refresh_logs()

    def _on_ha_connected(self, ws, rest, entity, device, url):
        self.adapter = HAAdapter(ws, rest, entity, device, url)
        # Сохраняем ссылку на device_manager для использования с DeviceLoader
        self.adapter.device_manager = device
        self._update_connection_status(success=True)
        self.logger.success(f"Подключено к {url}")
        self._setup_tabs_by_role()
        self._refresh_logs()

    def _on_connection_error(self, msg):
        self._update_connection_status(disconnected=True)
        self.logger.error(msg)
        QMessageBox.warning(self, "Ошибка при подключении", str(msg))

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
        if not self.adapter or not self.adapter.is_connected():
            QMessageBox.warning(self, "Ошибка", "Нет активного подключения.")
            return

        self.logger.info("Загрузка устройств...")
        self._refresh_logs()
        self.devices_panel.clear_devices()
        self.devices_panel.show_loading_indicator("Загрузка устройств...")

        # Используем DeviceLoader для асинхронной загрузки
        if hasattr(self.adapter, "device_manager"):
            # Для HAAdapter
            loader = DeviceLoader(self.adapter.device_manager)
            loader.devices_loaded.connect(self.devices_panel.update_devices)
            loader.error.connect(lambda e: self.logger.error(
                f"Ошибка загрузки устройств: {e}"))
            loader.start()
            self.device_loader = loader
        else:
            # Для других адаптеров
            try:
                devices = self.adapter.get_devices_by_category()
                self.devices_panel.update_devices(devices)
                self.logger.success("Устройства успешно загружены")
            except Exception as e:
                self.logger.error(f"Ошибка загрузки: {e}")
                QMessageBox.critical(self, "Ошибка загрузки", str(e))

        self._refresh_logs()

    def _open_device_dialog(self, device):
        if self.adapter:
            dialog = DeviceDialog(device, self.adapter, parent=self)
            dialog.exec()

    def _refresh_logs(self):
        self.ui.textEditLogs.setHtml(self.logger.get_text_log())
        self.ui.textEditLogs.verticalScrollBar().setValue(
            self.ui.textEditLogs.verticalScrollBar().maximum()
        )

    def _logout(self):
        if self.connection_worker:
            self.connection_worker.quit()
            self.connection_worker.wait()
            self.connection_worker = None

        dialog = LoginDialog()
        if dialog.exec() == QDialog.Accepted:
            self.user_data = dialog.user_data
            self.role = self.user_data.get("role", "student")
            self.adapter = None
            self._setup_top_panel()
            self._setup_tabs_by_role()
            self.logger = get_logger()
            self._refresh_logs()
            self.devices_panel.clear_devices()

    def closeEvent(self, event):
        if self.connection_worker:
            self.connection_worker.quit()
            self.connection_worker.wait()
            self.connection_worker = None
        event.accept()
