from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, QTextStream
from ui.windows.User.login_dialog import LoginDialog
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

    login_dialog = LoginDialog()
    if login_dialog.exec() == LoginDialog.Accepted:
        user = login_dialog.user_data
        window = MainWindow(user_data=user)
        window.show()
        app.exec()