from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QListWidget, QListWidgetItem,
    QMessageBox, QTabWidget, QWidget, QFormLayout, QComboBox,
    QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal
from typing import Dict, List, Any, Optional
from core.api import api_client
from core.api.api_worker import (
    GetLabWorker, CreateLabWorker, UpdateLabWorker,
    CreateTaskWorker, UpdateTaskWorker, DeleteTaskWorker
)
from ui.dialogs.lab.task_editor_dialog import TaskEditorDialog
from core.logger import get_logger


class LabEditorDialog(QDialog):
    """Диалог для создания и редактирования лабораторной работы"""

    lab_saved = Signal(int)  # Сигнал с ID сохраненной лабораторной работы

    def __init__(self, lab_id: int = None, parent=None):
        super().__init__(parent)
        self.lab_id = lab_id
        self.lab_data = None
        self.logger = get_logger()

        self.setWindowTitle("Редактор лабораторной работы")
        self.setMinimumSize(800, 600)

        self._build_ui()

        if lab_id:
            # Режим редактирования
            self._load_lab()
        else:
            # Режим создания
            self.lab_data = {
                "title": "",
                "description": "",
                "content": {},
                "tasks": []
            }

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Вкладки
        self.tabs = QTabWidget()

        # Вкладка основной информации
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)

        form_layout = QFormLayout()

        self.title_edit = QLineEdit()
        form_layout.addRow("Название:", self.title_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        form_layout.addRow("Описание:", self.description_edit)

        info_layout.addLayout(form_layout)

        # Дополнительные настройки
        info_layout.addWidget(QLabel("<h3>Дополнительные настройки</h3>"))

        # Здесь можно добавить дополнительные настройки лабораторной работы

        self.tabs.addTab(info_tab, "Основная информация")

        # Вкладка заданий
        tasks_tab = QWidget()
        tasks_layout = QVBoxLayout(tasks_tab)

        tasks_layout.addWidget(QLabel("<h3>Задания</h3>"))

        self.tasks_list = QListWidget()
        tasks_layout.addWidget(self.tasks_list)

        tasks_buttons = QHBoxLayout()

        self.add_task_btn = QPushButton("Добавить задание")
        self.add_task_btn.clicked.connect(self._add_task)
        tasks_buttons.addWidget(self.add_task_btn)

        self.edit_task_btn = QPushButton("Редактировать")
        self.edit_task_btn.clicked.connect(self._edit_task)
        tasks_buttons.addWidget(self.edit_task_btn)

        self.delete_task_btn = QPushButton("Удалить")
        self.delete_task_btn.clicked.connect(self._delete_task)
        tasks_buttons.addWidget(self.delete_task_btn)

        tasks_layout.addLayout(tasks_buttons)

        self.tabs.addTab(tasks_tab, "Задания")

        layout.addWidget(self.tabs)

        # Кнопки действий
        buttons_layout = QHBoxLayout()

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self._save_lab)
        buttons_layout.addWidget(self.save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

    def _load_lab(self):
        """Загрузка данных лабораторной работы"""
        worker = GetLabWorker(api_client, self.lab_id)
        worker.result_ready.connect(self._on_lab_loaded)
        worker.error_occurred.connect(self._show_error)
        worker.start()

    def _on_lab_loaded(self, lab_data: Optional[Dict[str, Any]]):
        """Обработка загруженных данных лабораторной работы"""
        if not lab_data:
            QMessageBox.critical(
                self, "Ошибка", "Не удалось загрузить лабораторную работу")
            self.reject()
            return

        self.lab_data = lab_data

        # Заполняем поля формы
        self.title_edit.setText(lab_data.get("title", ""))
        self.description_edit.setText(lab_data.get("description", ""))

        # Заполняем список заданий
        self._update_tasks_list()

    def _update_tasks_list(self):
        """Обновление списка заданий"""
        self.tasks_list.clear()

        tasks = self.lab_data.get("tasks", [])
        for i, task in enumerate(tasks):
            title = task.get("title", "Задание")
            task_type = task.get("task_type", "")
            item = QListWidgetItem(f"{i+1}. {title} ({task_type})")
            item.setData(Qt.UserRole, task)
            self.tasks_list.addItem(item)

    def _add_task(self):
        """Добавление нового задания"""
        dialog = TaskEditorDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            task_data = dialog.get_task_data()

            # Добавляем задание в список
            if not self.lab_data.get("tasks"):
                self.lab_data["tasks"] = []

            # Устанавливаем порядковый номер
            task_data["order_index"] = len(self.lab_data["tasks"])

            self.lab_data["tasks"].append(task_data)
            self._update_tasks_list()

    def _edit_task(self):
        """Редактирование выбранного задания"""
        selected_item = self.tasks_list.currentItem()
        if not selected_item:
            QMessageBox.warning(
                self, "Ошибка", "Выберите задание для редактирования")
            return

        task_data = selected_item.data(Qt.UserRole)
        dialog = TaskEditorDialog(task_data=task_data, parent=self)

        if dialog.exec() == QDialog.Accepted:
            updated_task = dialog.get_task_data()

            # Обновляем задание в списке
            index = self.tasks_list.currentRow()
            self.lab_data["tasks"][index] = updated_task

            # Сохраняем порядковый номер
            updated_task["order_index"] = index

            self._update_tasks_list()

    def _delete_task(self):
        """Удаление выбранного задания"""
        selected_item = self.tasks_list.currentItem()
        if not selected_item:
            QMessageBox.warning(
                self, "Ошибка", "Выберите задание для удаления")
            return

        confirm = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить это задание?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        # Удаляем задание из списка
        index = self.tasks_list.currentRow()
        del self.lab_data["tasks"][index]

        # Обновляем порядковые номера
        for i, task in enumerate(self.lab_data["tasks"]):
            task["order_index"] = i

        self._update_tasks_list()

    def _save_lab(self):
        """Сохранение лабораторной работы"""
        # Проверка заполнения обязательных полей
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(
                self, "Ошибка", "Введите название лабораторной работы")
            return

        # Собираем данные
        lab_data = {
            "title": title,
            "description": self.description_edit.toPlainText().strip(),
            "content": self.lab_data.get("content", {})
        }

        if self.lab_id:
            # Режим редактирования - обновляем существующую лабораторную работу
            worker = UpdateLabWorker(api_client, self.lab_id, lab_data)
            worker.result_ready.connect(self._on_lab_updated)
            worker.error_occurred.connect(self._show_error)
            worker.start()
        else:
            # Режим создания - создаем новую лабораторную работу
            # Добавляем задания
            lab_data["tasks"] = self.lab_data.get("tasks", [])

            worker = CreateLabWorker(api_client, lab_data)
            worker.result_ready.connect(self._on_lab_created)
            worker.error_occurred.connect(self._show_error)
            worker.start()

    def _on_lab_created(self, lab_data: Optional[Dict[str, Any]]):
        """Обработка результата создания лабораторной работы"""
        if not lab_data:
            QMessageBox.critical(
                self, "Ошибка", "Не удалось создать лабораторную работу")
            return

        self.lab_id = lab_data.get("id")
        self.lab_data = lab_data

        QMessageBox.information(
            self, "Успех", "Лабораторная работа успешно создана")

        # Отправляем сигнал с ID созданной лабораторной работы
        self.lab_saved.emit(self.lab_id)

        self.accept()

    def _on_lab_updated(self, lab_data: Optional[Dict[str, Any]]):
        """Обработка результата обновления лабораторной работы"""
        if not lab_data:
            QMessageBox.critical(
                self, "Ошибка", "Не удалось обновить лабораторную работу")
            return

        # Теперь нужно обновить задания
        self._update_tasks()

    def _update_tasks(self):
        """Обновление заданий лабораторной работы"""
        # Здесь должна быть логика обновления заданий через API
        # Пока просто показываем сообщение об успехе
        QMessageBox.information(
            self, "Успех", "Лабораторная работа успешно обновлена")

        # Отправляем сигнал с ID обновленной лабораторной работы
        self.lab_saved.emit(self.lab_id)

        self.accept()

    def _show_error(self, error: str):
        """Отображение ошибки"""
        QMessageBox.critical(self, "Ошибка", error)
