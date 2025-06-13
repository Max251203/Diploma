from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QDateTimeEdit, QTextEdit, QPushButton, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QDateTime
from datetime import datetime, timedelta
from core.booking import booking_manager
from core.logger import get_logger


class BookingDialog(QDialog):
    """Диалог для бронирования устройства"""

    def __init__(self, device_id: str, device_name: str, parent=None):
        super().__init__(parent)
        self.device_id = device_id
        self.device_name = device_name
        self.logger = get_logger()

        self.setWindowTitle(f"Бронирование устройства: {device_name}")
        self.setMinimumSize(600, 500)

        self._build_ui()
        self._connect_signals()

        # Загружаем информацию о доступности устройства и очереди
        booking_manager.get_device_availability(device_id)
        booking_manager.get_device_queue(device_id)

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Информация об устройстве
        device_info = QLabel(f"<h3>Устройство: {self.device_name}</h3>")
        device_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(device_info)

        # Информация о доступности
        self.availability_label = QLabel(
            "Загрузка информации о доступности...")
        self.availability_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.availability_label)

        # Форма бронирования
        form_layout = QVBoxLayout()
        form_layout.setContentsMargins(20, 10, 20, 10)

        # Время начала и окончания
        time_layout = QHBoxLayout()

        start_layout = QVBoxLayout()
        start_layout.addWidget(QLabel("Время начала:"))
        self.start_time_edit = QDateTimeEdit()
        self.start_time_edit.setDateTime(
            QDateTime.currentDateTime().addSecs(300))  # +5 минут
        self.start_time_edit.setCalendarPopup(True)
        self.start_time_edit.setMinimumDateTime(QDateTime.currentDateTime())
        start_layout.addWidget(self.start_time_edit)
        time_layout.addLayout(start_layout)

        end_layout = QVBoxLayout()
        end_layout.addWidget(QLabel("Время окончания:"))
        self.end_time_edit = QDateTimeEdit()
        self.end_time_edit.setDateTime(
            QDateTime.currentDateTime().addSecs(3600))  # +1 час
        self.end_time_edit.setCalendarPopup(True)
        self.end_time_edit.setMinimumDateTime(
            QDateTime.currentDateTime().addSecs(300))
        end_layout.addWidget(self.end_time_edit)
        time_layout.addLayout(end_layout)

        form_layout.addLayout(time_layout)

        # Цель бронирования
        form_layout.addWidget(QLabel("Цель бронирования:"))
        self.purpose_edit = QTextEdit()
        self.purpose_edit.setMaximumHeight(80)
        form_layout.addWidget(self.purpose_edit)

        # Кнопки быстрого выбора времени
        quick_time_layout = QHBoxLayout()
        quick_time_layout.addWidget(QLabel("Быстрый выбор:"))

        btn_30min = QPushButton("30 минут")
        btn_30min.clicked.connect(lambda: self._set_duration(30))
        quick_time_layout.addWidget(btn_30min)

        btn_1hour = QPushButton("1 час")
        btn_1hour.clicked.connect(lambda: self._set_duration(60))
        quick_time_layout.addWidget(btn_1hour)

        btn_2hours = QPushButton("2 часа")
        btn_2hours.clicked.connect(lambda: self._set_duration(120))
        quick_time_layout.addWidget(btn_2hours)

        form_layout.addLayout(quick_time_layout)

        # Кнопки действий
        buttons_layout = QHBoxLayout()

        self.book_btn = QPushButton("Забронировать")
        self.book_btn.clicked.connect(self._book_device)
        buttons_layout.addWidget(self.book_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        form_layout.addLayout(buttons_layout)

        layout.addLayout(form_layout)

        # Таблица очереди бронирований
        layout.addWidget(QLabel("<h4>Текущая очередь бронирований:</h4>"))

        self.queue_table = QTableWidget(0, 4)
        self.queue_table.setHorizontalHeaderLabels(
            ["Пользователь", "Начало", "Окончание", "Цель"])
        self.queue_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.queue_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.queue_table.setAlternatingRowColors(True)
        layout.addWidget(self.queue_table)

    def _connect_signals(self):
        # Подключаем сигналы от менеджера бронирования
        booking_manager.device_availability_updated.connect(
            self._update_availability)
        booking_manager.device_queue_updated.connect(self._update_queue)
        booking_manager.booking_created.connect(self._on_booking_created)
        booking_manager.error_occurred.connect(self._show_error)

        # Подключаем сигналы от элементов формы
        self.start_time_edit.dateTimeChanged.connect(self._validate_times)
        self.end_time_edit.dateTimeChanged.connect(self._validate_times)

    def _validate_times(self):
        """Проверка корректности выбранного времени"""
        start_time = self.start_time_edit.dateTime().toPython()
        end_time = self.end_time_edit.dateTime().toPython()

        # Проверяем, что время начала раньше времени окончания
        if start_time >= end_time:
            self.end_time_edit.setDateTime(
                self.start_time_edit.dateTime().addSecs(1800))  # +30 минут
            return

        # Проверяем, что время начала не в прошлом
        now = datetime.now()
        if start_time < now:
            self.start_time_edit.setDateTime(
                QDateTime.currentDateTime().addSecs(300))  # +5 минут

    def _set_duration(self, minutes: int):
        """Установка длительности бронирования"""
        start_time = self.start_time_edit.dateTime()
        self.end_time_edit.setDateTime(start_time.addSecs(minutes * 60))

    def _update_availability(self, device_id: str, data: dict):
        """Обновление информации о доступности устройства"""
        if device_id != self.device_id:
            return

        is_available = data.get("is_available", False)
        current_booking = data.get("current_booking")
        next_available = data.get("next_available")

        if is_available:
            self.availability_label.setText(
                "<h4 style='color: green;'>Устройство доступно для бронирования</h4>")
        else:
            if current_booking:
                user = current_booking.get("user_id", "Неизвестно")
                end_time = current_booking.get("end_time", "Неизвестно")
                self.availability_label.setText(
                    f"<h4 style='color: orange;'>Устройство занято пользователем {user} до {end_time}</h4>"
                )
            else:
                self.availability_label.setText(
                    "<h4 style='color: red;'>Устройство недоступно</h4>")

        # Если устройство недоступно, устанавливаем время начала на следующее доступное время
        if not is_available and next_available:
            next_dt = QDateTime.fromString(next_available, Qt.ISODate)
            self.start_time_edit.setDateTime(
                next_dt.addSecs(300))  # +5 минут после освобождения
            # +30 минут после освобождения
            self.end_time_edit.setDateTime(next_dt.addSecs(1800))

    def _update_queue(self, device_id: str, queue: list):
        """Обновление таблицы очереди бронирований"""
        if device_id != self.device_id:
            return

        self.queue_table.setRowCount(len(queue))

        for i, booking in enumerate(queue):
            # Пользователь
            user_item = QTableWidgetItem(
                f"{booking.get('user_login', '')} ({booking.get('user_id', '')})"
            )
            self.queue_table.setItem(i, 0, user_item)

            # Время начала
            start_time = booking.get("start_time", "")
            start_item = QTableWidgetItem(start_time)
            self.queue_table.setItem(i, 1, start_item)

            # Время окончания
            end_time = booking.get("end_time", "")
            end_item = QTableWidgetItem(end_time)
            self.queue_table.setItem(i, 2, end_item)

            # Цель
            purpose = booking.get("purpose", "")
            purpose_item = QTableWidgetItem(purpose)
            self.queue_table.setItem(i, 3, purpose_item)

    def _book_device(self):
        """Бронирование устройства"""
        start_time = self.start_time_edit.dateTime().toPython()
        end_time = self.end_time_edit.dateTime().toPython()
        purpose = self.purpose_edit.toPlainText().strip()

        # Проверка корректности данных
        if not purpose:
            QMessageBox.warning(self, "Ошибка", "Укажите цель бронирования")
            return

        if start_time >= end_time:
            QMessageBox.warning(
                self, "Ошибка", "Время начала должно быть раньше времени окончания")
            return

        if start_time < datetime.now():
            QMessageBox.warning(
                self, "Ошибка", "Время начала не может быть в прошлом")
            return

        # Отправляем запрос на бронирование
        booking_manager.book_device(
            self.device_id, start_time, end_time, purpose)

    def _on_booking_created(self, result: dict):
        """Обработка успешного бронирования"""
        if result.get("success"):
            QMessageBox.information(
                self,
                "Успех",
                f"Устройство успешно забронировано.\nID бронирования: {result.get('booking_id')}"
            )
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Ошибка",
                f"Не удалось забронировать устройство: {result.get('message')}"
            )

    def _show_error(self, error: str):
        """Отображение ошибки"""
        QMessageBox.warning(self, "Ошибка", error)
