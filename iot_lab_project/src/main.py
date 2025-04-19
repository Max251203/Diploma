from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, QTextStream
from ui.windows.Main.main_window import MainWindow

def load_stylesheet():
    file = QFile(":/style/style.qss")
    if file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(file)
        return stream.readAll()
    return ""

if __name__ == "__main__":
    app = QApplication([])
    app.setStyleSheet(load_stylesheet())
    window = MainWindow()
    window.show()
    app.exec()    