import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, QTextStream
from ui.windows.main_window import MainWindow

def load_stylesheet():
    """Загружает стили из файла"""
    file = QFile(":/style/style.qss")
    if file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(file)
        return stream.readAll()
    return ""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Применяем стили
    app.setStyleSheet(load_stylesheet())
    
    # Создаем и показываем главное окно
    window = MainWindow()
    window.show()
    
    # Запускаем основной цикл приложения
    sys.exit(app.exec())