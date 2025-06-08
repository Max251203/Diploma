from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel
from core.adapters.api_adapter import APIAdapter


class NetworkPanel(QWidget):
    def __init__(self, adapter: APIAdapter, parent=None):
        super().__init__(parent)
        self.adapter = adapter

        self.layout = QVBoxLayout(self)
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        self.btn_refresh = QPushButton("Обновить данные сети")
        self.btn_refresh.clicked.connect(self._load_info)

        self.layout.addWidget(QLabel("Состояние Zigbee-сети:"))
        self.layout.addWidget(self.output)
        self.layout.addWidget(self.btn_refresh)

        self._load_info()

    def _load_info(self):
        try:
            import requests
            res = requests.get(f"{self.adapter.url}/api/network/info",
                               headers={"x-api-key": self.adapter.api_key})
            if res.ok:
                data = res.json()
                self.output.setPlainText("Информация о сети:\n" + str(data))
            else:
                self.output.setPlainText(f"Ошибка запроса: {res.status_code}")
        except Exception as e:
            self.output.setPlainText("Ошибка запроса: " + str(e))
