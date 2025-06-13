from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QComboBox, QCheckBox, QRadioButton,
    QButtonGroup, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from typing import Dict, Any, List, Optional


class TaskWidget(QWidget):
    """Виджет для отображения и выполнения задания"""

    answer_submitted = Signal(int, dict)  # Сигнал с ID задания и ответом

    def __init__(self, task_data: Dict[str, Any], result_data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.task_data = task_data
        self.result_data = result_data
        self.task_id = task_data.get("id", 0)
        self.task_type = task_data.get("task_type", "")
        self.content = task_data.get("content", {})

        self.answer = {}
        self.is_completed = False

        if result_data:
            self.answer = result_data.get("answer", {}) or {}
            self.is_completed = bool(self.answer)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок задания
        title_label = QLabel(
            f"<h3>{self.task_data.get('title', 'Задание')}</h3>")
        layout.addWidget(title_label)

        # Описание задания
        description = self.task_data.get("description", "")
        if description:
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        # Содержимое задания в зависимости от типа
        content_widget = self._create_content_widget()
        layout.addWidget(content_widget)

        # Кнопки действий
        buttons_layout = QHBoxLayout()

        self.submit_btn = QPushButton("Отправить ответ")
        self.submit_btn.clicked.connect(self._submit_answer)
        buttons_layout.addWidget(self.submit_btn)

        # Если задание уже выполнено, отключаем кнопку отправки
        if self.is_completed:
            self.submit_btn.setEnabled(False)
            self.submit_btn.setText("Ответ отправлен")

        layout.addLayout(buttons_layout)

        # Если есть результат с оценкой, показываем его
        if self.result_data and self.result_data.get("score") is not None:
            score_label = QLabel(
                f"<h4>Оценка: {self.result_data.get('score')} из {self.task_data.get('max_score', 10)}</h4>")
            layout.addWidget(score_label)

            if self.result_data.get("feedback"):
                feedback_label = QLabel(
                    f"<b>Комментарий преподавателя:</b> {self.result_data.get('feedback')}")
                feedback_label.setWordWrap(True)
                layout.addWidget(feedback_label)

    def _create_content_widget(self) -> QWidget:
        """Создание виджета с содержимым задания в зависимости от типа"""
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        if self.task_type == "theory":
            # Теоретический материал
            text = self.content.get("text", "")
            text_label = QLabel(text)
            text_label.setWordWrap(True)
            text_label.setTextFormat(Qt.RichText)
            content_layout.addWidget(text_label)

            # Поле для ответа (например, конспект)
            content_layout.addWidget(QLabel("<b>Ваш конспект:</b>"))
            self.answer_edit = QTextEdit()
            if self.answer.get("text"):
                self.answer_edit.setText(self.answer.get("text"))
            if self.is_completed:
                self.answer_edit.setReadOnly(True)
            content_layout.addWidget(self.answer_edit)

        elif self.task_type == "test":
            # Тестовое задание
            questions = self.content.get("questions", [])
            self.question_widgets = []

            for i, question in enumerate(questions):
                q_widget = self._create_question_widget(i, question)
                content_layout.addWidget(q_widget)
                self.question_widgets.append(q_widget)

        elif self.task_type == "device_interaction":
            # Задание с взаимодействием с устройствами
            instructions = self.content.get("instructions", "")
            instr_label = QLabel(instructions)
            instr_label.setWordWrap(True)
            content_layout.addWidget(instr_label)

            # Список устройств
            devices = self.task_data.get("devices", [])
            if devices:
                devices_group = QGroupBox("Устройства для выполнения задания:")
                devices_layout = QVBoxLayout(devices_group)

                for device in devices:
                    device_id = device.get("device_id", "")
                    required_state = device.get("required_state", {})

                    device_label = QLabel(f"Устройство: {device_id}")
                    if required_state:
                        state_text = ", ".join(
                            f"{k}: {v}" for k, v in required_state.items())
                        device_label.setText(
                            f"Устройство: {device_id} (требуемое состояние: {state_text})")

                    devices_layout.addWidget(device_label)

                content_layout.addWidget(devices_group)

            # Поле для отчета о выполнении
            content_layout.addWidget(QLabel("<b>Отчет о выполнении:</b>"))
            self.report_edit = QTextEdit()
            if self.answer.get("report"):
                self.report_edit.setText(self.answer.get("report"))
            if self.is_completed:
                self.report_edit.setReadOnly(True)
            content_layout.addWidget(self.report_edit)

        elif self.task_type == "code":
            # Задание с программированием
            task_text = self.content.get("task", "")
            task_label = QLabel(task_text)
            task_label.setWordWrap(True)
            content_layout.addWidget(task_label)

            # Поле для кода
            content_layout.addWidget(QLabel("<b>Ваш код:</b>"))
            self.code_edit = QTextEdit()
            self.code_edit.setFontFamily("Courier New")
            if self.answer.get("code"):
                self.code_edit.setText(self.answer.get("code"))
            if self.is_completed:
                self.code_edit.setReadOnly(True)
            content_layout.addWidget(self.code_edit)

        else:
            # Неизвестный тип задания
            content_layout.addWidget(
                QLabel(f"Неизвестный тип задания: {self.task_type}"))

        return content_widget

    def _create_question_widget(self, index: int, question: Dict[str, Any]) -> QWidget:
        """Создание виджета для вопроса теста"""
        q_widget = QWidget()
        q_layout = QVBoxLayout(q_widget)

        # Текст вопроса
        q_text = question.get("text", f"Вопрос {index + 1}")
        q_label = QLabel(f"<b>{index + 1}. {q_text}</b>")
        q_label.setWordWrap(True)
        q_layout.addWidget(q_label)

        # Варианты ответов
        q_type = question.get("type", "single")
        options = question.get("options", [])

        if q_type == "single":
            # Вопрос с одним вариантом ответа
            radio_group = QButtonGroup(q_widget)
            self.radio_buttons = []

            for i, option in enumerate(options):
                radio = QRadioButton(option)
                radio.setProperty("question_index", index)
                radio.setProperty("option_index", i)

                # Если есть сохраненный ответ, выбираем соответствующий вариант
                if self.answer.get("answers") and len(self.answer["answers"]) > index:
                    if self.answer["answers"][index] == i:
                        radio.setChecked(True)

                if self.is_completed:
                    radio.setEnabled(False)

                radio_group.addButton(radio)
                self.radio_buttons.append(radio)
                q_layout.addWidget(radio)

        elif q_type == "multiple":
            # Вопрос с несколькими вариантами ответа
            self.checkboxes = []

            for i, option in enumerate(options):
                checkbox = QCheckBox(option)
                checkbox.setProperty("question_index", index)
                checkbox.setProperty("option_index", i)

                # Если есть сохраненный ответ, выбираем соответствующие варианты
                if self.answer.get("answers") and len(self.answer["answers"]) > index:
                    if i in self.answer["answers"][index]:
                        checkbox.setChecked(True)

                if self.is_completed:
                    checkbox.setEnabled(False)

                self.checkboxes.append(checkbox)
                q_layout.addWidget(checkbox)

        elif q_type == "text":
            # Вопрос с текстовым ответом
            self.text_answer = QTextEdit()

            # Если есть сохраненный ответ, заполняем поле
            if self.answer.get("answers") and len(self.answer["answers"]) > index:
                self.text_answer.setText(self.answer["answers"][index])

            if self.is_completed:
                self.text_answer.setReadOnly(True)

            q_layout.addWidget(self.text_answer)

        return q_widget

    def _submit_answer(self):
        """Отправка ответа на задание"""
        answer = {}

        if self.task_type == "theory":
            # Для теоретического задания - текст конспекта
            answer["text"] = self.answer_edit.toPlainText().strip()

            if not answer["text"]:
                QMessageBox.warning(self, "Ошибка", "Введите ваш конспект")
                return

        elif self.task_type == "test":
            # Для тестового задания - ответы на вопросы
            questions = self.content.get("questions", [])
            answers = []

            for i, question in enumerate(questions):
                q_type = question.get("type", "single")

                if q_type == "single":
                    # Для вопроса с одним вариантом ответа
                    selected = -1
                    for j, radio in enumerate(self.radio_buttons):
                        if radio.property("question_index") == i and radio.isChecked():
                            selected = radio.property("option_index")

                    answers.append(selected)

                elif q_type == "multiple":
                    # Для вопроса с несколькими вариантами ответа
                    selected = []
                    for checkbox in self.checkboxes:
                        if checkbox.property("question_index") == i and checkbox.isChecked():
                            selected.append(checkbox.property("option_index"))

                    answers.append(selected)

                elif q_type == "text":
                    # Для вопроса с текстовым ответом
                    answers.append(self.text_answer.toPlainText().strip())

            answer["answers"] = answers

            # Проверяем, что на все вопросы даны ответы
            for i, a in enumerate(answers):
                if a == -1 or a == [] or (isinstance(a, str) and not a):
                    QMessageBox.warning(
                        self, "Ошибка", f"Ответьте на вопрос {i + 1}")
                    return

        elif self.task_type == "device_interaction":
            # Для задания с устройствами - отчет о выполнении
            answer["report"] = self.report_edit.toPlainText().strip()

            if not answer["report"]:
                QMessageBox.warning(
                    self, "Ошибка", "Введите отчет о выполнении")
                return

        elif self.task_type == "code":
            # Для задания с программированием - код
            answer["code"] = self.code_edit.toPlainText().strip()

            if not answer["code"]:
                QMessageBox.warning(self, "Ошибка", "Введите ваш код")
                return

        # Отправляем ответ
        self.answer_submitted.emit(self.task_id, answer)

        # Отключаем кнопку отправки
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("Ответ отправлен")

        # Обновляем состояние
        self.is_completed = True
        self.answer = answer

        # Делаем поля только для чтения
        if self.task_type == "theory":
            self.answer_edit.setReadOnly(True)
        elif self.task_type == "device_interaction":
            self.report_edit.setReadOnly(True)
        elif self.task_type == "code":
            self.code_edit.setReadOnly(True)
