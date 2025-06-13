from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal
from typing import Dict, Any


class LabCard(QFrame):
    """Карточка лабораторной работы"""

    clicked = Signal(int)  # Сигнал с ID лабораторной работы
    start_clicked = Signal(int)  # Сигнал для начала выполнения
    edit_clicked = Signal(int)  # Сигнал для редактирования
    delete_clicked = Signal(int)  # Сигнал для удаления

    def __init__(self, lab_data: Dict[str, Any], is_teacher: bool = False, parent=None):
        super().__init__(parent)
        self.lab_data = lab_data
        self.lab_id = lab_data.get("id", 0)
        self.is_teacher = is_teacher

        self.setObjectName("labCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(120)
        self.setMaximumHeight(180)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        title_label = QLabel(
            f"<h3>{self.lab_data.get('title', 'Без названия')}</h3>")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Описание
        description = self.lab_data.get("description", "")
        if description:
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(desc_label)

        # Информация о заданиях
        tasks = self.lab_data.get("tasks", [])
        tasks_count = len(tasks)
        tasks_label = QLabel(f"Количество заданий: {tasks_count}")
        tasks_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(tasks_label)

        # Кнопки действий
        buttons_layout = QHBoxLayout()

        if self.is_teacher:
            # Кнопки для преподавателя
            edit_btn = QPushButton("Редактировать")
            edit_btn.clicked.connect(
                lambda: self.edit_clicked.emit(self.lab_id))
            buttons_layout.addWidget(edit_btn)

            delete_btn = QPushButton("Удалить")
            delete_btn.clicked.connect(
                lambda: self.delete_clicked.emit(self.lab_id))
            buttons_layout.addWidget(delete_btn)
        else:
            # Кнопка для студента
            start_btn = QPushButton("Начать выполнение")
            start_btn.clicked.connect(
                lambda: self.start_clicked.emit(self.lab_id))
            buttons_layout.addWidget(start_btn)

        layout.addLayout(buttons_layout)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit(self.lab_id)
