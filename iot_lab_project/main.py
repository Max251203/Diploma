from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, QTextStream
from ui.dialogs.login_dialog import LoginDialog
from ui.Main.main_window import MainWindow

def load_stylesheet():
    file = QFile(":/style/style.qss")
    if file.open(QFile.ReadOnly | QFile.Text):
        return QTextStream(file).readAll()
    return ""

if __name__ == "__main__":
    app = QApplication([])
    app.setStyleSheet(load_stylesheet())

    login = LoginDialog()
    if login.exec() == LoginDialog.Accepted:
        user = login.user_data
        window = MainWindow(user_data=user)
        window.show()
        app.exec()