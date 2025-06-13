from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QFormLayout, QSpinBox,
    QDoubleSpinBox, QTabWidget, QWidget, QMessageBox,
    QListWidget, QListWidgetItem, QCheckBox
)
from PySide6.QtCore import Qt
from typing import Dict, List, Any, Optional


class TaskEditorDialog(QDialog):
    """Диалог для создания и редактирования задания"""

    def __init__(self, task_data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.task_data = task_data or {}

        self.setWindowTitle("Редактор задания")
        self.setMinimumSize(600, 500)

        self._build_ui()

        if task_data:
            # Режим редактирования
            self._fill_form()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Основная информация
        form_layout = QFormLayout()

        self.title_edit = QLineEdit()
        form_layout.addRow("Название:", self.title_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        form_layout.addRow("Описание:", self.description_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItems(
            ["theory", "test", "device_interaction", "code"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        form_layout.addRow("Тип задания:", self.type_combo)

        self.max_score_spin = QDoubleSpinBox()
        self.max_score_spin.setMinimum(0)
        self.max_score_spin.setMaximum(100)
        self.max_score_spin.setValue(10)
        self.max_score_spin.setSingleStep(0.5)
        form_layout.addRow("Максимальный балл:", self.max_score_spin)

        layout.addLayout(form_layout)

        # Вкладки для разных типов заданий
        self.tabs = QTabWidget()

        # Вкладка для теоретического задания
        self.theory_tab = QWidget()
        theory_layout = QVBoxLayout(self.theory_tab)

        theory_layout.addWidget(QLabel("Текст теоретического материала:"))
        self.theory_text = QTextEdit()
        theory_layout.addWidget(self.theory_text)

        self.tabs.addTab(self.theory_tab, "Теория")

        # Вкладка для тестового задания
        self.test_tab = QWidget()
        test_layout = QVBoxLayout(self.test_tab)

        test_layout.addWidget(QLabel("Вопросы теста:"))

        self.questions_list = QListWidget()
        test_layout.addWidget(self.questions_list)

        questions_buttons = QHBoxLayout()

        self.add_question_btn = QPushButton("Добавить вопрос")
        self.add_question_btn.clicked.connect(self._add_question)
        questions_buttons.addWidget(self.add_question_btn)

        self.edit_question_btn = QPushButton("Редактировать")
        self.edit_question_btn.clicked.connect(self._edit_question)
        questions_buttons.addWidget(self.edit_question_btn)

        self.delete_question_btn = QPushButton("Удалить")
        self.delete_question_btn.clicked.connect(self._delete_question)
        questions_buttons.addWidget(self.delete_question_btn)

        test_layout.addLayout(questions_buttons)

        self.tabs.addTab(self.test_tab, "Тест")

        # Вкладка для задания с устройствами
        self.device_tab = QWidget()
        device_layout = QVBoxLayout(self.device_tab)

        device_layout.addWidget(QLabel("Инструкции по работе с устройствами:"))
        self.device_instructions = QTextEdit()
        device_layout.addWidget(self.device_instructions)

        device_layout.addWidget(QLabel("Устройства для задания:"))

        self.devices_list = QListWidget()
        device_layout.addWidget(self.devices_list)

        devices_buttons = QHBoxLayout()

        self.add_device_btn = QPushButton("Добавить устройство")
        self.add_device_btn.clicked.connect(self._add_device)
        devices_buttons.addWidget(self.add_device_btn)

        self.edit_device_btn = QPushButton("Редактировать")
        self.edit_device_btn.clicked.connect(self._edit_device)
        devices_buttons.addWidget(self.edit_device_btn)

        self.delete_device_btn = QPushButton("Удалить")
        self.delete_device_btn.clicked.connect(self._delete_device)
        devices_buttons.addWidget(self.delete_device_btn)

        device_layout.addLayout(devices_buttons)

        self.tabs.addTab(self.device_tab, "Устройства")

        # Вкладка для задания с программированием
        self.code_tab = QWidget()
        code_layout = QVBoxLayout(self.code_tab)

        code_layout.addWidget(QLabel("Задание по программированию:"))
        self.code_task = QTextEdit()
        code_layout.addWidget(self.code_task)

        self.tabs.addTab(self.code_tab, "Программирование")

        layout.addWidget(self.tabs)

        # Кнопки действий
        buttons_layout = QHBoxLayout()

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

        # Устанавливаем активную вкладку в зависимости от типа задания
        self._on_type_changed(self.type_combo.currentText())

    def _on_type_changed(self, task_type: str):
        """Обработка изменения типа задания"""
        if task_type == "theory":
            self.tabs.setCurrentWidget(self.theory_tab)
        elif task_type == "test":
            self.tabs.setCurrentWidget(self.test_tab)
        elif task_type == "device_interaction":
            self.tabs.setCurrentWidget(self.device_tab)
        elif task_type == "code":
            self.tabs.setCurrentWidget(self.code_tab)

    def _fill_form(self):
        """Заполнение формы данными задания"""
        self.title_edit.setText(self.task_data.get("title", ""))
        self.description_edit.setText(self.task_data.get("description", ""))

        task_type = self.task_data.get("task_type", "theory")
        self.type_combo.setCurrentText(task_type)

        self.max_score_spin.setValue(self.task_data.get("max_score", 10))

        content = self.task_data.get("content", {})

        if task_type == "theory":
            self.theory_text.setText(content.get("text", ""))
        elif task_type == "test":
            self._fill_questions(content.get("questions", []))
        elif task_type == "device_interaction":
            self.device_instructions.setText(content.get("instructions", ""))
            self._fill_devices(self.task_data.get("devices", []))
        elif task_type == "code":
            self.code_task.setText(content.get("task", ""))

    def _fill_questions(self, questions: List[Dict[str, Any]]):
        """Заполнение списка вопросов"""
        self.questions_list.clear()

        for i, question in enumerate(questions):
            q_text = question.get("text", f"Вопрос {i+1}")
            q_type = question.get("type", "single")
            item = QListWidgetItem(f"{i+1}. {q_text} ({q_type})")
            item.setData(Qt.UserRole, question)
            self.questions_list.addItem(item)

    def _fill_devices(self, devices: List[Dict[str, Any]]):
        """Заполнение списка устройств"""
        self.devices_list.clear()

        for i, device in enumerate(devices):
            device_id = device.get("device_id", "")
            required_state = device.get("required_state", {})

            if required_state:
                state_text = ", ".join(
                    f"{k}: {v}" for k, v in required_state.items())
                item_text = f"{device_id} (требуемое состояние: {state_text})"
            else:
                item_text = device_id

            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, device)
            self.devices_list.addItem(item)

    def _add_question(self):
        """Добавление нового вопроса"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QListWidget, QListWidgetItem, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle("Добавление вопроса")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        form = QFormLayout()

        text_edit = QLineEdit()
        form.addRow("Текст вопроса:", text_edit)

        type_combo = QComboBox()
        type_combo.addItems(["single", "multiple", "text"])
        form.addRow("Тип вопроса:", type_combo)

        layout.addLayout(form)

        layout.addWidget(QLabel("Варианты ответов:"))

        options_list = QListWidget()
        layout.addWidget(options_list)

        options_buttons = QHBoxLayout()

        add_option_btn = QPushButton("Добавить вариант")
        add_option_btn.clicked.connect(lambda: self._add_option(options_list))
        options_buttons.addWidget(add_option_btn)

        edit_option_btn = QPushButton("Редактировать")
        edit_option_btn.clicked.connect(
            lambda: self._edit_option(options_list))
        options_buttons.addWidget(edit_option_btn)

        delete_option_btn = QPushButton("Удалить")
        delete_option_btn.clicked.connect(
            lambda: self._delete_option(options_list))
        options_buttons.addWidget(delete_option_btn)

        layout.addLayout(options_buttons)

        buttons = QHBoxLayout()

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(dialog.accept)
        buttons.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addWidget(cancel_btn)

        layout.addLayout(buttons)

        if dialog.exec() == QDialog.Accepted:
            question_text = text_edit.text().strip()
            question_type = type_combo.currentText()

            if not question_text:
                QMessageBox.warning(self, "Ошибка", "Введите текст вопроса")
                return

            options = []
            for i in range(options_list.count()):
                options.append(options_list.item(i).text())

            # Для текстового вопроса варианты не нужны
            if question_type == "text":
                options = []
            elif not options and question_type != "text":
                QMessageBox.warning(
                    self, "Ошибка", "Добавьте варианты ответов")
                return

            question = {
                "text": question_text,
                "type": question_type,
                "options": options
            }

            item = QListWidgetItem(
                f"{self.questions_list.count() + 1}. {question_text} ({question_type})")
            item.setData(Qt.UserRole, question)
            self.questions_list.addItem(item)

    def _edit_question(self):
        """Редактирование выбранного вопроса"""
        selected_item = self.questions_list.currentItem()
        if not selected_item:
            QMessageBox.warning(
                self, "Ошибка", "Выберите вопрос для редактирования")
            return

        question = selected_item.data(Qt.UserRole)

        from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QListWidget, QListWidgetItem, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактирование вопроса")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        form = QFormLayout()

        text_edit = QLineEdit()
        text_edit.setText(question.get("text", ""))
        form.addRow("Текст вопроса:", text_edit)

        type_combo = QComboBox()
        type_combo.addItems(["single", "multiple", "text"])
        type_combo.setCurrentText(question.get("type", "single"))
        form.addRow("Тип вопроса:", type_combo)

        layout.addLayout(form)

        layout.addWidget(QLabel("Варианты ответов:"))

        options_list = QListWidget()
        for option in question.get("options", []):
            options_list.addItem(option)
        layout.addWidget(options_list)

        options_buttons = QHBoxLayout()

        add_option_btn = QPushButton("Добавить вариант")
        add_option_btn.clicked.connect(lambda: self._add_option(options_list))
        options_buttons.addWidget(add_option_btn)

        edit_option_btn = QPushButton("Редактировать")
        edit_option_btn.clicked.connect(
            lambda: self._edit_option(options_list))
        options_buttons.addWidget(edit_option_btn)

        delete_option_btn = QPushButton("Удалить")
        delete_option_btn.clicked.connect(
            lambda: self._delete_option(options_list))
        options_buttons.addWidget(delete_option_btn)

        layout.addLayout(options_buttons)

        buttons = QHBoxLayout()

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(dialog.accept)
        buttons.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addWidget(cancel_btn)

        layout.addLayout(buttons)

        if dialog.exec() == QDialog.Accepted:
            question_text = text_edit.text().strip()
            question_type = type_combo.currentText()

            if not question_text:
                QMessageBox.warning(self, "Ошибка", "Введите текст вопроса")
                return

            options = []
            for i in range(options_list.count()):
                options.append(options_list.item(i).text())

            # Для текстового вопроса варианты не нужны
            if question_type == "text":
                options = []
            elif not options and question_type != "text":
                QMessageBox.warning(
                    self, "Ошибка", "Добавьте варианты ответов")
                return

            updated_question = {
                "text": question_text,
                "type": question_type,
                "options": options
            }

            index = self.questions_list.currentRow()
            item = QListWidgetItem(
                f"{index + 1}. {question_text} ({question_type})")
            item.setData(Qt.UserRole, updated_question)
            self.questions_list.takeItem(index)
            self.questions_list.insertItem(index, item)
            self.questions_list.setCurrentRow(index)

    def _delete_question(self):
        """Удаление выбранного вопроса"""
        selected_item = self.questions_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Ошибка", "Выберите вопрос для удаления")
            return

        confirm = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить этот вопрос?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        self.questions_list.takeItem(self.questions_list.currentRow())

        # Обновляем нумерацию
        for i in range(self.questions_list.count()):
            item = self.questions_list.item(i)
            question = item.data(Qt.UserRole)
            item.setText(
                f"{i + 1}. {question.get('text', '')} ({question.get('type', '')})")

    def _add_option(self, options_list):
        """Добавление варианта ответа"""
        from PySide6.QtWidgets import QInputDialog

        option, ok = QInputDialog.getText(
            self, "Добавление варианта", "Введите текст варианта ответа:")
        if ok and option.strip():
            options_list.addItem(option.strip())

    def _edit_option(self, options_list):
        """Редактирование варианта ответа"""
        selected_item = options_list.currentItem()
        if not selected_item:
            QMessageBox.warning(
                self, "Ошибка", "Выберите вариант для редактирования")
            return

        from PySide6.QtWidgets import QInputDialog

        option, ok = QInputDialog.getText(
            self,
            "Редактирование варианта",
            "Введите текст варианта ответа:",
            text=selected_item.text()
        )

        if ok and option.strip():
            selected_item.setText(option.strip())

    def _delete_option(self, options_list):
        """Удаление варианта ответа"""
        selected_item = options_list.currentItem()
        if not selected_item:
            QMessageBox.warning(
                self, "Ошибка", "Выберите вариант для удаления")
            return

        options_list.takeItem(options_list.currentRow())

    def _add_device(self):
        """Добавление устройства к заданию"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle("Добавление устройства")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        form = QFormLayout()

        device_id_edit = QLineEdit()
        form.addRow("ID устройства:", device_id_edit)

        state_edit = QTextEdit()
        state_edit.setMaximumHeight(100)
        state_edit.setPlaceholderText('{"state": "ON", "brightness": 100}')
        form.addRow("Требуемое состояние (JSON):", state_edit)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(dialog.accept)
        buttons.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addWidget(cancel_btn)

        layout.addLayout(buttons)

        if dialog.exec() == QDialog.Accepted:
            device_id = device_id_edit.text().strip()
            state_text = state_edit.toPlainText().strip()

            if not device_id:
                QMessageBox.warning(self, "Ошибка", "Введите ID устройства")
                return

            required_state = None
            if state_text:
                try:
                    import json
                    required_state = json.loads(state_text)
                except json.JSONDecodeError:
                    QMessageBox.warning(
                        self, "Ошибка", "Некорректный формат JSON")
                    return

            device = {
                "device_id": device_id,
                "required_state": required_state
            }

            if required_state:
                state_text = ", ".join(
                    f"{k}: {v}" for k, v in required_state.items())
                item_text = f"{device_id} (требуемое состояние: {state_text})"
            else:
                item_text = device_id

            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, device)
            self.devices_list.addItem(item)

    def _edit_device(self):
        """Редактирование устройства"""
        selected_item = self.devices_list.currentItem()
        if not selected_item:
            QMessageBox.warning(
                self, "Ошибка", "Выберите устройство для редактирования")
            return

        device = selected_item.data(Qt.UserRole)

        from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактирование устройства")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        form = QFormLayout()

        device_id_edit = QLineEdit()
        device_id_edit.setText(device.get("device_id", ""))
        form.addRow("ID устройства:", device_id_edit)

        state_edit = QTextEdit()
        state_edit.setMaximumHeight(100)

        if device.get("required_state"):
            import json
            state_edit.setText(json.dumps(device["required_state"]))

        form.addRow("Требуемое состояние (JSON):", state_edit)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(dialog.accept)
        buttons.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addWidget(cancel_btn)

        layout.addLayout(buttons)

        if dialog.exec() == QDialog.Accepted:
            device_id = device_id_edit.text().strip()
            state_text = state_edit.toPlainText().strip()

            if not device_id:
                QMessageBox.warning(self, "Ошибка", "Введите ID устройства")
                return

            required_state = None
            if state_text:
                try:
                    import json
                    required_state = json.loads(state_text)
                except json.JSONDecodeError:
                    QMessageBox.warning(
                        self, "Ошибка", "Некорректный формат JSON")
                    return

            updated_device = {
                "device_id": device_id,
                "required_state": required_state
            }

            if required_state:
                state_text = ", ".join(
                    f"{k}: {v}" for k, v in required_state.items())
                item_text = f"{device_id} (требуемое состояние: {state_text})"
            else:
                item_text = device_id

            index = self.devices_list.currentRow()
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, updated_device)
            self.devices_list.takeItem(index)
            self.devices_list.insertItem(index, item)
            self.devices_list.setCurrentRow(index)

    def _delete_device(self):
        """Удаление устройства"""
        selected_item = self.devices_list.currentItem()
        if not selected_item:
            QMessageBox.warning(
                self, "Ошибка", "Выберите устройство для удаления")
            return

        confirm = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить это устройство?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        self.devices_list.takeItem(self.devices_list.currentRow())

    def get_task_data(self) -> Dict[str, Any]:
        """Получение данных задания"""
        title = self.title_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        task_type = self.type_combo.currentText()
        max_score = self.max_score_spin.value()

        content = {}

        if task_type == "theory":
            content["text"] = self.theory_text.toPlainText().strip()
        elif task_type == "test":
            questions = []
            for i in range(self.questions_list.count()):
                questions.append(self.questions_list.item(i).data(Qt.UserRole))
            content["questions"] = questions
        elif task_type == "device_interaction":
            content["instructions"] = self.device_instructions.toPlainText().strip()
        elif task_type == "code":
            content["task"] = self.code_task.toPlainText().strip()

        task_data = {
            "title": title,
            "description": description,
            "task_type": task_type,
            "content": content,
            "max_score": max_score
        }

        # Добавляем устройства для задания с устройствами
        if task_type == "device_interaction":
            devices = []
            for i in range(self.devices_list.count()):
                devices.append(self.devices_list.item(i).data(Qt.UserRole))
            task_data["devices"] = devices

        return task_data
