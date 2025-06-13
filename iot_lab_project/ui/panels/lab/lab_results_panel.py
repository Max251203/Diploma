from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QTextEdit,
    QDialog, QFormLayout, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from typing import Dict, List, Any, Optional
from core.api import api_client
from core.api.api_worker import (
    GetLabsWorker, GetLabResultsWorker, GetLabResultWorker,
    UpdateLabResultWorker, UpdateTaskResultWorker
)
from core.logger import get_logger


class LabResultsPanel(QWidget):
    """Панель для просмотра и оценки результатов выполнения лабораторных работ"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.selected_lab_id = None

        self._build_ui()
        self._load_labs()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        header = QHBoxLayout()

        title = QLabel("<h2>Результаты выполнения лабораторных работ</h2>")
        header.addWidget(title)

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self._refresh_results)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # Выбор лабораторной работы
        lab_selection = QHBoxLayout()

        lab_selection.addWidget(QLabel("Лабораторная работа:"))

        self.lab_combo = QComboBox()
        self.lab_combo.setMinimumWidth(300)
        self.lab_combo.currentIndexChanged.connect(self._on_lab_selected)
        lab_selection.addWidget(self.lab_combo)

        lab_selection.addStretch()

        layout.addLayout(lab_selection)

        # Таблица результатов
        self.results_table = QTableWidget(0, 5)
        self.results_table.setHorizontalHeaderLabels(
            ["Студент", "Статус", "Дата сдачи", "Оценка", "Действия"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setAlternatingRowColors(True)
        layout.addWidget(self.results_table)

    def _load_labs(self):
        """Загрузка списка лабораторных работ"""
        self.logger.info("Загрузка списка лабораторных работ")

        # Очищаем комбобокс
        self.lab_combo.clear()
        self.lab_combo.addItem("Загрузка лабораторных работ...")

        # Загружаем лабораторные работы
        worker = GetLabsWorker(api_client)
        worker.result_ready.connect(self._on_labs_loaded)
        worker.error_occurred.connect(self._show_error)
        worker.start()

    def _on_labs_loaded(self, labs: Optional[List[Dict[str, Any]]]):
        """Обработка загруженных лабораторных работ"""
        # Очищаем комбобокс
        self.lab_combo.clear()

        if not labs:
            self.lab_combo.addItem("Нет доступных лабораторных работ")
            return

        # Заполняем комбобокс
        self.lab_combo.addItem("Выберите лабораторную работу", None)

        for lab in labs:
            lab_id = lab.get("id")
            title = lab.get("title", "Без названия")

            self.lab_combo.addItem(title, lab_id)

        self.logger.info(f"Загружено {len(labs)} лабораторных работ")

    def _on_lab_selected(self, index: int):
        """Обработка выбора лабораторной работы"""
        if index <= 0:
            self.selected_lab_id = None
            self.results_table.setRowCount(0)
            return

        self.selected_lab_id = self.lab_combo.currentData()
        self._load_results()

    def _load_results(self):
        """Загрузка результатов выполнения выбранной лабораторной работы"""
        if not self.selected_lab_id:
            return

        self.logger.info(
            f"Загрузка результатов для лабораторной работы {self.selected_lab_id}")

        # Очищаем таблицу
        self.results_table.setRowCount(0)

        # Загружаем результаты
        worker = GetLabResultsWorker(api_client, self.selected_lab_id)
        worker.result_ready.connect(self._on_results_loaded)
        worker.error_occurred.connect(self._show_error)
        worker.start()

    def _on_results_loaded(self, results: Optional[List[Dict[str, Any]]]):
        """Обработка загруженных результатов"""
        # Очищаем таблицу
        self.results_table.setRowCount(0)

        if not results:
            return

        # Заполняем таблицу
        self.results_table.setRowCount(len(results))

        for i, result in enumerate(results):
            # Студент
            user_id = result.get("user_id")

            # Получаем информацию о пользователе
            from core.api.api_worker import GetUserWorker

            worker = GetUserWorker(api_client, user_id)
            worker.result_ready.connect(
                lambda user, row=i: self._update_user_info(user, row))
            worker.start()

            # Студент
            user_id = result.get("user_id")

            # Получаем информацию о пользователе
            from core.api.api_worker import GetUserWorker

            worker = GetUserWorker(api_client, user_id)
            worker.result_ready.connect(
                lambda user, row=i: self._update_user_info(user, row))
            worker.start()

            # Временно устанавливаем ID пользователя
            self.results_table.setItem(
                i, 0, QTableWidgetItem(f"ID: {user_id}"))

            # Статус
            status = result.get("status", "")
            status_text = {
                "in_progress": "В процессе",
                "submitted": "На проверке",
                "reviewed": "Проверено"
            }.get(status, status)

            status_item = QTableWidgetItem(status_text)
            self.results_table.setItem(i, 1, status_item)

            # Дата сдачи
            submitted_at = result.get("submitted_at", "")
            self.results_table.setItem(i, 2, QTableWidgetItem(submitted_at))

            # Оценка
            score = result.get("score")
            score_item = QTableWidgetItem(
                str(score) if score is not None else "")
            self.results_table.setItem(i, 3, score_item)

            # Действия
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            view_btn = QPushButton("Просмотр")
            view_btn.clicked.connect(
                lambda checked, r=result: self._view_result(r))
            actions_layout.addWidget(view_btn)

            if status == "submitted":
                review_btn = QPushButton("Оценить")
                review_btn.clicked.connect(
                    lambda checked, r=result: self._review_result(r))
                actions_layout.addWidget(review_btn)

            self.results_table.setCellWidget(i, 4, actions_widget)

            # Сохраняем данные результата
            self.results_table.setItem(i, 0, QTableWidgetItem(""))
            self.results_table.item(i, 0).setData(Qt.UserRole, result)

        self.logger.info(f"Загружено {len(results)} результатов")

    def _update_user_info(self, user: Optional[Dict[str, Any]], row: int):
        """Обновление информации о пользователе в таблице"""
        if not user or row >= self.results_table.rowCount():
            return

        # Формируем ФИО
        last_name = user.get("last_name", "")
        first_name = user.get("first_name", "")
        middle_name = user.get("middle_name", "")

        fio = f"{last_name} {first_name} {middle_name}".strip()
        if not fio:
            fio = user.get("login", "")

        # Обновляем ячейку
        self.results_table.item(row, 0).setText(fio)

    def _view_result(self, result: Dict[str, Any]):
        """Просмотр результата выполнения лабораторной работы"""
        result_id = result.get("id")

        # Загружаем полную информацию о результате
        worker = GetLabResultWorker(api_client, result_id)
        worker.result_ready.connect(self._show_result_dialog)
        worker.error_occurred.connect(self._show_error)
        worker.start()

    def _show_result_dialog(self, result: Optional[Dict[str, Any]]):
        """Отображение диалога с результатом выполнения"""
        if not result:
            QMessageBox.critical(
                self, "Ошибка", "Не удалось загрузить результат")
            return

        # Создаем диалог для просмотра результата
        dialog = QDialog(self)
        dialog.setWindowTitle("Результат выполнения лабораторной работы")
        dialog.setMinimumSize(800, 600)

        layout = QVBoxLayout(dialog)

        # Информация о лабораторной работе
        lab_id = result.get("lab_id")

        # Загружаем информацию о лабораторной работе
        from core.api.api_worker import GetLabWorker

        worker = GetLabWorker(api_client, lab_id)
        worker.result_ready.connect(
            lambda lab: self._update_result_dialog(dialog, lab, result))
        worker.error_occurred.connect(self._show_error)
        worker.start()

        # Временный заголовок
        layout.addWidget(
            QLabel(f"<h2>Загрузка информации о лабораторной работе {lab_id}...</h2>"))

        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def _update_result_dialog(self, dialog: QDialog, lab: Optional[Dict[str, Any]], result: Dict[str, Any]):
        """Обновление диалога с результатом выполнения"""
        if not lab:
            return

        # Очищаем layout
        layout = dialog.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Заголовок
        layout.addWidget(
            QLabel(f"<h2>{lab.get('title', 'Лабораторная работа')}</h2>"))

        # Информация о студенте
        user_id = result.get("user_id")

        # Получаем информацию о пользователе
        from core.api.api_worker import GetUserWorker

        worker = GetUserWorker(api_client, user_id)
        worker.result_ready.connect(
            lambda user: self._update_student_info(dialog, user))
        worker.start()

        # Временная информация о студенте
        layout.addWidget(QLabel(f"<b>Студент:</b> ID {user_id}"))

        # Статус
        status = result.get("status", "")
        status_text = {
            "in_progress": "В процессе",
            "submitted": "На проверке",
            "reviewed": "Проверено"
        }.get(status, status)

        layout.addWidget(QLabel(f"<b>Статус:</b> {status_text}"))

        # Дата сдачи
        submitted_at = result.get("submitted_at", "")
        if submitted_at:
            layout.addWidget(QLabel(f"<b>Дата сдачи:</b> {submitted_at}"))

        # Оценка
        score = result.get("score")
        if score is not None:
            layout.addWidget(QLabel(f"<b>Оценка:</b> {score}"))

        # Комментарий преподавателя
        feedback = result.get("feedback", "")
        if feedback:
            layout.addWidget(
                QLabel(f"<b>Комментарий преподавателя:</b> {feedback}"))

        # Результаты заданий
        layout.addWidget(QLabel("<h3>Результаты заданий:</h3>"))

        task_results = result.get("task_results", [])
        tasks = lab.get("tasks", [])

        # Создаем словарь заданий для быстрого доступа
        tasks_dict = {task.get("id"): task for task in tasks}

        for task_result in task_results:
            task_id = task_result.get("task_id")
            task = tasks_dict.get(task_id)

            if not task:
                continue

            # Заголовок задания
            layout.addWidget(
                QLabel(f"<h4>{task.get('title', 'Задание')}</h4>"))

            # Тип задания
            task_type = task.get("task_type", "")
            layout.addWidget(QLabel(f"<b>Тип задания:</b> {task_type}"))

            # Ответ студента
            answer = task_result.get("answer", {})

            if task_type == "theory":
                text = answer.get("text", "")
                layout.addWidget(QLabel("<b>Ответ студента:</b>"))

                answer_text = QTextEdit()
                answer_text.setPlainText(text)
                answer_text.setReadOnly(True)
                answer_text.setMaximumHeight(150)
                layout.addWidget(answer_text)

            elif task_type == "test":
                answers = answer.get("answers", [])
                questions = task.get("content", {}).get("questions", [])

                layout.addWidget(QLabel("<b>Ответы на вопросы:</b>"))

                for i, question in enumerate(questions):
                    if i >= len(answers):
                        continue

                    q_text = question.get("text", f"Вопрос {i+1}")
                    q_type = question.get("type", "single")

                    layout.addWidget(QLabel(f"<b>{i+1}. {q_text}</b>"))

                    if q_type == "single":
                        options = question.get("options", [])
                        selected = answers[i]

                        if isinstance(selected, int) and 0 <= selected < len(options):
                            layout.addWidget(
                                QLabel(f"Ответ: {options[selected]}"))
                        else:
                            layout.addWidget(QLabel("Ответ: Не выбран"))

                    elif q_type == "multiple":
                        options = question.get("options", [])
                        selected = answers[i]

                        if isinstance(selected, list):
                            selected_options = [options[j]
                                                for j in selected if 0 <= j < len(options)]
                            layout.addWidget(
                                QLabel(f"Ответ: {', '.join(selected_options)}"))
                        else:
                            layout.addWidget(QLabel("Ответ: Не выбран"))

                    elif q_type == "text":
                        layout.addWidget(QLabel(f"Ответ: {answers[i]}"))

            elif task_type == "device_interaction":
                report = answer.get("report", "")
                layout.addWidget(QLabel("<b>Отчет о выполнении:</b>"))

                report_text = QTextEdit()
                report_text.setPlainText(report)
                report_text.setReadOnly(True)
                report_text.setMaximumHeight(150)
                layout.addWidget(report_text)

            elif task_type == "code":
                code = answer.get("code", "")
                layout.addWidget(QLabel("<b>Код:</b>"))

                code_text = QTextEdit()
                code_text.setPlainText(code)
                code_text.setReadOnly(True)
                code_text.setMaximumHeight(150)
                layout.addWidget(code_text)

            # Оценка за задание
            score = task_result.get("score")
            if score is not None:
                layout.addWidget(
                    QLabel(f"<b>Оценка за задание:</b> {score} из {task.get('max_score', 10)}"))

            # Комментарий к заданию
            feedback = task_result.get("feedback", "")
            if feedback:
                layout.addWidget(
                    QLabel(f"<b>Комментарий к заданию:</b> {feedback}"))

        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

    def _update_student_info(self, dialog: QDialog, user: Optional[Dict[str, Any]]):
        """Обновление информации о студенте в диалоге результата"""
        if not user:
            return

        # Находим метку с информацией о студенте
        layout = dialog.layout()
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, QLabel) and widget.text().startswith("<b>Студент:</b>"):
                # Формируем ФИО
                last_name = user.get("last_name", "")
                first_name = user.get("first_name", "")
                middle_name = user.get("middle_name", "")

                fio = f"{last_name} {first_name} {middle_name}".strip()
                if not fio:
                    fio = user.get("login", "")

                # Обновляем текст метки
                widget.setText(f"<b>Студент:</b> {fio}")
                break

    def _review_result(self, result: Dict[str, Any]):
        """Оценка результата выполнения лабораторной работы"""
        result_id = result.get("id")

        # Загружаем полную информацию о результате
        worker = GetLabResultWorker(api_client, result_id)
        worker.result_ready.connect(self._show_review_dialog)
        worker.error_occurred.connect(self._show_error)
        worker.start()

    def _show_review_dialog(self, result: Optional[Dict[str, Any]]):
        """Отображение диалога для оценки результата"""
        if not result:
            QMessageBox.critical(
                self, "Ошибка", "Не удалось загрузить результат")
            return

        # Создаем диалог для оценки результата
        dialog = QDialog(self)
        dialog.setWindowTitle(
            "Оценка результата выполнения лабораторной работы")
        dialog.setMinimumSize(800, 600)

        layout = QVBoxLayout(dialog)

        # Информация о лабораторной работе
        lab_id = result.get("lab_id")

        # Загружаем информацию о лабораторной работе
        from core.api.api_worker import GetLabWorker

        worker = GetLabWorker(api_client, lab_id)
        worker.result_ready.connect(
            lambda lab: self._update_review_dialog(dialog, lab, result))
        worker.error_occurred.connect(self._show_error)
        worker.start()

        # Временный заголовок
        layout.addWidget(
            QLabel(f"<h2>Загрузка информации о лабораторной работе {lab_id}...</h2>"))

        # Кнопки действий
        buttons = QHBoxLayout()

        save_btn = QPushButton("Сохранить оценку")
        save_btn.clicked.connect(lambda: self._save_review(dialog, result))
        buttons.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addWidget(cancel_btn)

        layout.addLayout(buttons)

        dialog.exec()

    def _update_review_dialog(self, dialog: QDialog, lab: Optional[Dict[str, Any]], result: Dict[str, Any]):
        """Обновление диалога для оценки результата"""
        if not lab:
            return

        # Очищаем layout
        layout = dialog.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Заголовок
        layout.addWidget(
            QLabel(f"<h2>{lab.get('title', 'Лабораторная работа')}</h2>"))

        # Информация о студенте
        user_id = result.get("user_id")

        # Получаем информацию о пользователе
        from core.api.api_worker import GetUserWorker

        worker = GetUserWorker(api_client, user_id)
        worker.result_ready.connect(
            lambda user: self._update_student_info(dialog, user))
        worker.start()

        # Временная информация о студенте
        layout.addWidget(QLabel(f"<b>Студент:</b> ID {user_id}"))

        # Общая оценка
        form = QFormLayout()

        score_spin = QDoubleSpinBox()
        score_spin.setMinimum(0)
        score_spin.setMaximum(100)
        score_spin.setValue(result.get("score", 0) or 0)
        score_spin.setObjectName("score_spin")
        form.addRow("Общая оценка:", score_spin)

        feedback_edit = QTextEdit()
        feedback_edit.setPlainText(result.get("feedback", ""))
        feedback_edit.setObjectName("feedback_edit")
        form.addRow("Комментарий:", feedback_edit)

        layout.addLayout(form)

        # Результаты заданий
        layout.addWidget(QLabel("<h3>Оценка заданий:</h3>"))

        task_results = result.get("task_results", [])
        tasks = lab.get("tasks", [])

        # Создаем словарь заданий для быстрого доступа
        tasks_dict = {task.get("id"): task for task in tasks}

        # Создаем виджет для заданий
        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)

        for task_result in task_results:
            task_id = task_result.get("task_id")
            task = tasks_dict.get(task_id)

            if not task:
                continue

            # Заголовок задания
            tasks_layout.addWidget(
                QLabel(f"<h4>{task.get('title', 'Задание')}</h4>"))

            # Тип задания
            task_type = task.get("task_type", "")
            tasks_layout.addWidget(QLabel(f"<b>Тип задания:</b> {task_type}"))

            # Ответ студента
            answer = task_result.get("answer", {})

            if task_type == "theory":
                text = answer.get("text", "")
                tasks_layout.addWidget(QLabel("<b>Ответ студента:</b>"))

                answer_text = QTextEdit()
                answer_text.setPlainText(text)
                answer_text.setReadOnly(True)
                answer_text.setMaximumHeight(150)
                tasks_layout.addWidget(answer_text)

            elif task_type == "test":
                answers = answer.get("answers", [])
                questions = task.get("content", {}).get("questions", [])

                tasks_layout.addWidget(QLabel("<b>Ответы на вопросы:</b>"))

                for i, question in enumerate(questions):
                    if i >= len(answers):
                        continue

                    q_text = question.get("text", f"Вопрос {i+1}")
                    q_type = question.get("type", "single")

                    tasks_layout.addWidget(QLabel(f"<b>{i+1}. {q_text}</b>"))

                    if q_type == "single":
                        options = question.get("options", [])
                        selected = answers[i]

                        if isinstance(selected, int) and 0 <= selected < len(options):
                            tasks_layout.addWidget(
                                QLabel(f"Ответ: {options[selected]}"))
                        else:
                            tasks_layout.addWidget(QLabel("Ответ: Не выбран"))

                    elif q_type == "multiple":
                        options = question.get("options", [])
                        selected = answers[i]

                        if isinstance(selected, list):
                            selected_options = [options[j]
                                                for j in selected if 0 <= j < len(options)]
                            tasks_layout.addWidget(
                                QLabel(f"Ответ: {', '.join(selected_options)}"))
                        else:
                            tasks_layout.addWidget(QLabel("Ответ: Не выбран"))

                    elif q_type == "text":
                        tasks_layout.addWidget(QLabel(f"Ответ: {answers[i]}"))

            elif task_type == "device_interaction":
                report = answer.get("report", "")
                tasks_layout.addWidget(QLabel("<b>Отчет о выполнении:</b>"))

                report_text = QTextEdit()
                report_text.setPlainText(report)
                report_text.setReadOnly(True)
                report_text.setMaximumHeight(150)
                tasks_layout.addWidget(report_text)

            elif task_type == "code":
                code = answer.get("code", "")
                tasks_layout.addWidget(QLabel("<b>Код:</b>"))

                code_text = QTextEdit()
                code_text.setPlainText(code)
                code_text.setReadOnly(True)
                code_text.setMaximumHeight(150)
                tasks_layout.addWidget(code_text)

            # Оценка за задание
            task_form = QFormLayout()

            task_score_spin = QDoubleSpinBox()
            task_score_spin.setMinimum(0)
            task_score_spin.setMaximum(task.get("max_score", 10))
            task_score_spin.setValue(task_result.get("score", 0) or 0)
            task_score_spin.setObjectName(f"task_score_{task_id}")
            task_form.addRow("Оценка за задание:", task_score_spin)

            task_feedback_edit = QTextEdit()
            task_feedback_edit.setPlainText(task_result.get("feedback", ""))
            task_feedback_edit.setObjectName(f"task_feedback_{task_id}")
            task_feedback_edit.setMaximumHeight(80)
            task_form.addRow("Комментарий к заданию:", task_feedback_edit)

            tasks_layout.addLayout(task_form)

            # Разделитель
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            tasks_layout.addWidget(separator)

        # Добавляем виджет с заданиями в скроллируемую область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tasks_widget)
        layout.addWidget(scroll)

        # Кнопки действий
        buttons = QHBoxLayout()

        save_btn = QPushButton("Сохранить оценку")
        save_btn.clicked.connect(lambda: self._save_review(dialog, result))
        buttons.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addWidget(cancel_btn)

        layout.addLayout(buttons)

    def _save_review(self, dialog: QDialog, result: Dict[str, Any]):
        """Сохранение оценки результата"""
        # Получаем общую оценку и комментарий
        score_spin = dialog.findChild(QDoubleSpinBox, "score_spin")
        feedback_edit = dialog.findChild(QTextEdit, "feedback_edit")

        if not score_spin or not feedback_edit:
            QMessageBox.critical(
                dialog, "Ошибка", "Не удалось найти элементы формы")
            return

        score = score_spin.value()
        feedback = feedback_edit.toPlainText().strip()

        # Обновляем результат
        result_id = result.get("id")

        update_data = {
            "status": "reviewed",
            "score": score,
            "feedback": feedback
        }

        worker = UpdateLabResultWorker(api_client, result_id, update_data)
        worker.result_ready.connect(
            lambda updated_result: self._on_result_updated(dialog, updated_result))
        worker.error_occurred.connect(
            lambda error: self._show_error_in_dialog(dialog, error))
        worker.start()

        # Обновляем оценки заданий
        task_results = result.get("task_results", [])

        for task_result in task_results:
            task_id = task_result.get("task_id")
            task_result_id = task_result.get("id")

            # Находим элементы формы для задания
            task_score_spin = dialog.findChild(
                QDoubleSpinBox, f"task_score_{task_id}")
            task_feedback_edit = dialog.findChild(
                QTextEdit, f"task_feedback_{task_id}")

            if not task_score_spin or not task_feedback_edit:
                continue

            task_score = task_score_spin.value()
            task_feedback = task_feedback_edit.toPlainText().strip()

            # Обновляем результат задания
            task_update_data = {
                "score": task_score,
                "feedback": task_feedback
            }

            worker = UpdateTaskResultWorker(
                api_client, result_id, task_result_id, task_update_data)
            worker.start()

    def _on_result_updated(self, dialog: QDialog, result: Optional[Dict[str, Any]]):
        """Обработка обновления результата"""
        if not result:
            QMessageBox.critical(
                dialog, "Ошибка", "Не удалось обновить результат")
            return

        QMessageBox.information(dialog, "Успех", "Оценка успешно сохранена")
        dialog.accept()

        # Обновляем таблицу результатов
        self._refresh_results()

    def _show_error_in_dialog(self, dialog: QDialog, error: str):
        """Отображение ошибки в диалоге"""
        QMessageBox.critical(dialog, "Ошибка", error)

    def _refresh_results(self):
        """Обновление результатов"""
        if self.selected_lab_id:
            self._load_results()
        else:
            self._load_labs()

    def _show_error(self, error: str):
        """Отображение ошибки"""
        QMessageBox.critical(self, "Ошибка", error)
