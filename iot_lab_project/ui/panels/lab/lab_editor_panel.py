from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from typing import Dict, List, Any, Optional
from core.api import api_client
from core.api.api_worker import GetLabsWorker
from ui.dialogs.lab.lab_editor_dialog import LabEditorDialog
from core.logger import get_logger


class LabEditorPanel(QWidget):
    """Панель для создания и редактирования лабораторных работ"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()

        self._build_ui()
        self._load_labs()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        header = QHBoxLayout()

        title = QLabel("<h2>Управление лабораторными работами</h2>")
        header.addWidget(title)

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self._load_labs)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # Список лабораторных работ
        self.labs_list = QListWidget()
        self.labs_list.itemDoubleClicked.connect(self._edit_lab)
        layout.addWidget(self.labs_list)

        # Кнопки действий
        buttons = QHBoxLayout()

        create_btn = QPushButton("Создать новую")
        create_btn.clicked.connect(self._create_lab)
        buttons.addWidget(create_btn)

        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(
            lambda: self._edit_lab(self.labs_list.currentItem()))
        buttons.addWidget(edit_btn)

        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(self._delete_lab)
        buttons.addWidget(delete_btn)

        layout.addLayout(buttons)

    def _load_labs(self):
        """Загрузка списка лабораторных работ"""
        self.logger.info("Загрузка списка лабораторных работ")

        # Очищаем список
        self.labs_list.clear()

        # Показываем индикатор загрузки
        self.labs_list.addItem("Загрузка лабораторных работ...")

        # Загружаем лабораторные работы
        worker = GetLabsWorker(api_client)
        worker.result_ready.connect(self._on_labs_loaded)
        worker.error_occurred.connect(self._show_error)
        worker.start()

    def _on_labs_loaded(self, labs: Optional[List[Dict[str, Any]]]):
        """Обработка загруженных лабораторных работ"""
        # Очищаем список
        self.labs_list.clear()

        if not labs:
            self.labs_list.addItem("Нет доступных лабораторных работ")
            return

        # Заполняем список
        for lab in labs:
            lab_id = lab.get("id")
            title = lab.get("title", "Без названия")
            tasks_count = len(lab.get("tasks", []))

            item = QListWidgetItem(
                f"{title} (ID: {lab_id}, заданий: {tasks_count})")
            item.setData(Qt.UserRole, lab)
            self.labs_list.addItem(item)

        self.logger.info(f"Загружено {len(labs)} лабораторных работ")

    def _create_lab(self):
        """Создание новой лабораторной работы"""
        dialog = LabEditorDialog(parent=self)
        dialog.lab_saved.connect(lambda lab_id: self._load_labs())
        dialog.exec()

    def _edit_lab(self, item: QListWidgetItem):
        """Редактирование выбранной лабораторной работы"""
        if not item:
            QMessageBox.warning(
                self, "Ошибка", "Выберите лабораторную работу для редактирования")
            return

        lab_data = item.data(Qt.UserRole)
        lab_id = lab_data.get("id")

        dialog = LabEditorDialog(lab_id, parent=self)
        dialog.lab_saved.connect(lambda: self._load_labs())
        dialog.exec()

    def _delete_lab(self):
        """Удаление выбранной лабораторной работы"""
        item = self.labs_list.currentItem()
        if not item:
            QMessageBox.warning(
                self, "Ошибка", "Выберите лабораторную работу для удаления")
            return

        lab_data = item.data(Qt.UserRole)
        lab_id = lab_data.get("id")
        title = lab_data.get("title", "Без названия")

        confirm = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы уверены, что хотите удалить лабораторную работу '{title}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        from core.api.api_worker import DeleteLabWorker

        worker = DeleteLabWorker(api_client, lab_id)
        worker.result_ready.connect(
            lambda result: self._on_lab_deleted(result, lab_id))
        worker.error_occurred.connect(self._show_error)
        worker.start()

    def _on_lab_deleted(self, success: bool, lab_id: int):
        """Обработка результата удаления лабораторной работы"""
        if success:
            QMessageBox.information(
                self, "Успех", "Лабораторная работа успешно удалена")
            self._load_labs()
        else:
            QMessageBox.critical(
                self, "Ошибка", "Не удалось удалить лабораторную работу")

    def _show_error(self, error: str):
        """Отображение ошибки"""
        QMessageBox.critical(self, "Ошибка", error)
