from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QTabWidget,
    QWidget, QScrollArea, QSplitter
)
from PySide6.QtCore import Qt, Signal
from typing import Dict, List, Any, Optional
from core.api import api_client
from core.api.api_worker import GetLabWorker, StartLabWorker, GetLabResultWorker
from ui.widgets.lab.task_widget import TaskWidget
from core.logger import get_logger


class LabBrowserDialog(QDialog):
    """Диалог для просмотра и выполнения лабораторной работы"""

    def __init__(self, lab_id: int, parent=None):
        super().__init__(parent)
        self.lab_id = lab_id
        self.lab_data = None
        self.result_id = None
        self.result_data = None
        self.logger = get_logger()

        self.setWindowTitle("Лабораторная работа")
        self.setMinimumSize(800, 600)

        self._build_ui()
        self._load_lab()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        self.title_label = QLabel("<h2>Загрузка лабораторной работы...</h2>")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        # Описание
        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.description_label)

        # Сплиттер для разделения списка заданий и содержимого
        splitter = QSplitter(Qt.Horizontal)

        # Список заданий
        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)

        tasks_layout.addWidget(QLabel("<h3>Задания:</h3>"))

        self.tasks_list = QListWidget()
        self.tasks_list.currentRowChanged.connect(self._show_task)
        tasks_layout.addWidget(self.tasks_list)

        # Кнопки действий
        tasks_buttons = QHBoxLayout()

        self.start_btn = QPushButton("Начать выполнение")
        self.start_btn.clicked.connect(self._start_lab)
        tasks_buttons.addWidget(self.start_btn)

        self.submit_btn = QPushButton("Отправить на проверку")
        self.submit_btn.clicked.connect(self._submit_lab)
        self.submit_btn.setEnabled(False)
        tasks_buttons.addWidget(self.submit_btn)

        tasks_layout.addLayout(tasks_buttons)

        splitter.addWidget(tasks_widget)

        # Содержимое задания
        self.task_container = QScrollArea()
        self.task_container.setWidgetResizable(True)
        splitter.addWidget(self.task_container)

        # Устанавливаем соотношение размеров сплиттера
        splitter.setSizes([200, 600])

        layout.addWidget(splitter)

        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

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

        # Обновляем заголовок и описание
        self.title_label.setText(
            f"<h2>{lab_data.get('title', 'Лабораторная работа')}</h2>")

        description = lab_data.get("description", "")
        if description:
            self.description_label.setText(description)
        else:
            self.description_label.hide()

        # Заполняем список заданий
        self.tasks_list.clear()

        tasks = lab_data.get("tasks", [])
        for task in tasks:
            title = task.get("title", "Задание")
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, task)
            self.tasks_list.addItem(item)

        # Выбираем первое задание
        if tasks:
            self.tasks_list.setCurrentRow(0)

        # Проверяем, есть ли уже начатая работа
        self._check_existing_result()

    def _check_existing_result(self):
        """Проверка наличия уже начатой работы"""
        # Здесь должен быть запрос к API для проверки наличия результата
        # Пока просто отключаем кнопку начала, если нет заданий
        if not self.lab_data.get("tasks"):
            self.start_btn.setEnabled(False)

    def _start_lab(self):
        """Начало выполнения лабораторной работы"""
        worker = StartLabWorker(api_client, self.lab_id)
        worker.result_ready.connect(self._on_lab_started)
        worker.error_occurred.connect(self._show_error)
        worker.start()

    def _on_lab_started(self, result_data: Optional[Dict[str, Any]]):
        """Обработка результата начала выполнения лабораторной работы"""
        if not result_data:
            QMessageBox.critical(
                self, "Ошибка", "Не удалось начать выполнение лабораторной работы")
            return

        self.result_id = result_data.get("id")
        self.result_data = result_data

        # Обновляем UI
        self.start_btn.setEnabled(False)
        self.submit_btn.setEnabled(True)

        # Обновляем виджеты заданий
        self._show_task(self.tasks_list.currentRow())

        QMessageBox.information(
            self, "Успех", "Выполнение лабораторной работы начато")

    def _show_task(self, index: int):
        """Отображение выбранного задания"""
        if index < 0 or not self.lab_data:
            return

        # Получаем данные задания
        task_data = self.lab_data.get("tasks", [])[index]

        # Получаем результат задания, если есть
        task_result = None
        if self.result_data and self.result_data.get("task_results"):
            for result in self.result_data["task_results"]:
                if result.get("task_id") == task_data.get("id"):
                    task_result = result
                    break

        # Создаем виджет задания
        task_widget = TaskWidget(task_data, task_result)
        task_widget.answer_submitted.connect(self._on_answer_submitted)

        # Устанавливаем виджет в контейнер
        self.task_container.setWidget(task_widget)

    def _on_answer_submitted(self, task_id: int, answer: Dict[str, Any]):
        """Обработка отправки ответа на задание"""
        if not self.result_id:
            QMessageBox.warning(
                self, "Ошибка", "Сначала начните выполнение лабораторной работы")
            return

        # Здесь должен быть запрос к API для сохранения ответа
        # Пока просто обновляем локальные данные
        if not self.result_data.get("task_results"):
            self.result_data["task_results"] = []

        # Ищем результат задания
        task_result = None
        for result in self.result_data["task_results"]:
            if result.get("task_id") == task_id:
                task_result = result
                break

        if task_result:
            task_result["answer"] = answer
        else:
            self.result_data["task_results"].append({
                "task_id": task_id,
                "answer": answer
            })

        self.logger.info(f"Отправлен ответ на задание {task_id}")

        # Проверяем, все ли задания выполнены
        self._check_all_tasks_completed()

    def _check_all_tasks_completed(self):
        """Проверка выполнения всех заданий"""
        if not self.result_data or not self.result_data.get("task_results"):
            return False

        tasks = self.lab_data.get("tasks", [])
        task_results = self.result_data.get("task_results", [])

        # Проверяем, что для каждого задания есть результат с ответом
        all_completed = len(tasks) == len(task_results)

        for task in tasks:
            task_id = task.get("id")
            found = False

            for result in task_results:
                if result.get("task_id") == task_id and result.get("answer"):
                    found = True
                    break

            if not found:
                all_completed = False
                break

        # Если все задания выполнены, разрешаем отправку на проверку
        self.submit_btn.setEnabled(all_completed)

        return all_completed

    def _submit_lab(self):
        """Отправка лабораторной работы на проверку"""
        if not self.result_id:
            QMessageBox.warning(
                self, "Ошибка", "Сначала начните выполнение лабораторной работы")
            return

        # Проверяем, все ли задания выполнены
        if not self._check_all_tasks_completed():
            QMessageBox.warning(
                self, "Ошибка", "Сначала выполните все задания")
            return

        # Запрашиваем подтверждение
        confirm = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите отправить работу на проверку? После отправки вы не сможете изменить ответы.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        # Здесь должен быть запрос к API для отправки работы на проверку
        # Пока просто показываем сообщение об успехе
        QMessageBox.information(self, "Успех", "Работа отправлена на проверку")

        # Отключаем кнопку отправки
        self.submit_btn.setEnabled(False)

        # Обновляем виджеты заданий
        self._show_task(self.tasks_list.currentRow())

    def _show_error(self, error: str):
        """Отображение ошибки"""
        QMessageBox.critical(self, "Ошибка", error)
