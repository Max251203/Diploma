from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from typing import Dict, List, Any, Optional
from core.api import api_client
from core.api.api_worker import GetLabsWorker
from ui.widgets.lab.lab_card import LabCard
from ui.dialogs.lab.lab_browser_dialog import LabBrowserDialog
from core.logger import get_logger


class LabBrowserPanel(QWidget):
    """Панель для просмотра доступных лабораторных работ"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()

        self._build_ui()
        self._load_labs()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        header = QHBoxLayout()

        title = QLabel("<h2>Доступные лабораторные работы</h2>")
        header.addWidget(title)

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self._load_labs)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # Контейнер для карточек лабораторных работ
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)

        scroll.setWidget(self.container)
        layout.addWidget(scroll)

    def _load_labs(self):
        """Загрузка списка лабораторных работ"""
        self.logger.info("Загрузка списка лабораторных работ")

        # Очищаем контейнер
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Показываем индикатор загрузки
        loading_label = QLabel("Загрузка лабораторных работ...")
        loading_label.setAlignment(Qt.AlignCenter)
        self.container_layout.addWidget(loading_label)

        # Загружаем лабораторные работы
        worker = GetLabsWorker(api_client)
        worker.result_ready.connect(self._on_labs_loaded)
        worker.error_occurred.connect(self._show_error)
        worker.start()

    def _on_labs_loaded(self, labs: Optional[List[Dict[str, Any]]]):
        """Обработка загруженных лабораторных работ"""
        # Очищаем контейнер
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not labs:
            no_labs_label = QLabel("Нет доступных лабораторных работ")
            no_labs_label.setAlignment(Qt.AlignCenter)
            self.container_layout.addWidget(no_labs_label)
            return

        # Определяем, является ли пользователь преподавателем
        is_teacher = False
        main_window = self.window()
        if hasattr(main_window, "user_data"):
            is_teacher = main_window.user_data.get(
                "role") in ["admin", "teacher"]

        # Создаем карточки для лабораторных работ
        for lab in labs:
            card = LabCard(lab, is_teacher)
            card.clicked.connect(self._open_lab)
            card.start_clicked.connect(self._start_lab)
            card.edit_clicked.connect(self._edit_lab)
            card.delete_clicked.connect(self._delete_lab)
            self.container_layout.addWidget(card)

        # Добавляем растягивающийся элемент в конец
        self.container_layout.addStretch()

        self.logger.info(f"Загружено {len(labs)} лабораторных работ")

    def _open_lab(self, lab_id: int):
        """Открытие лабораторной работы для просмотра"""
        dialog = LabBrowserDialog(lab_id, parent=self)
        dialog.exec()

    def _start_lab(self, lab_id: int):
        """Начало выполнения лабораторной работы"""
        dialog = LabBrowserDialog(lab_id, parent=self)
        dialog.exec()

    def _edit_lab(self, lab_id: int):
        """Редактирование лабораторной работы"""
        from ui.dialogs.lab.lab_editor_dialog import LabEditorDialog

        dialog = LabEditorDialog(lab_id, parent=self)
        dialog.lab_saved.connect(lambda: self._load_labs())
        dialog.exec()

    def _delete_lab(self, lab_id: int):
        """Удаление лабораторной работы"""
        confirm = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить эту лабораторную работу?",
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
