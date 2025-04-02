# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'connection_settings.ui'
##
## Created by: Qt User Interface Compiler version 6.8.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_ConnectionSettingsWindow(object):
    def setupUi(self, ConnectionSettingsWindow):
        if not ConnectionSettingsWindow.objectName():
            ConnectionSettingsWindow.setObjectName(u"ConnectionSettingsWindow")
        ConnectionSettingsWindow.resize(600, 400)
        self.verticalLayout = QVBoxLayout(ConnectionSettingsWindow)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.connectionsList = QListWidget(ConnectionSettingsWindow)
        self.connectionsList.setObjectName(u"connectionsList")

        self.verticalLayout.addWidget(self.connectionsList)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.labelName = QLabel(ConnectionSettingsWindow)
        self.labelName.setObjectName(u"labelName")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.labelName)

        self.nameEdit = QLineEdit(ConnectionSettingsWindow)
        self.nameEdit.setObjectName(u"nameEdit")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.nameEdit)

        self.labelUrl = QLabel(ConnectionSettingsWindow)
        self.labelUrl.setObjectName(u"labelUrl")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.labelUrl)

        self.urlEdit = QLineEdit(ConnectionSettingsWindow)
        self.urlEdit.setObjectName(u"urlEdit")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.urlEdit)

        self.labelToken = QLabel(ConnectionSettingsWindow)
        self.labelToken.setObjectName(u"labelToken")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.labelToken)

        self.tokenEdit = QLineEdit(ConnectionSettingsWindow)
        self.tokenEdit.setObjectName(u"tokenEdit")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.tokenEdit)


        self.verticalLayout.addLayout(self.formLayout)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setObjectName(u"buttonLayout")
        self.saveButton = QPushButton(ConnectionSettingsWindow)
        self.saveButton.setObjectName(u"saveButton")

        self.buttonLayout.addWidget(self.saveButton)

        self.removeButton = QPushButton(ConnectionSettingsWindow)
        self.removeButton.setObjectName(u"removeButton")

        self.buttonLayout.addWidget(self.removeButton)

        self.clearButton = QPushButton(ConnectionSettingsWindow)
        self.clearButton.setObjectName(u"clearButton")

        self.buttonLayout.addWidget(self.clearButton)


        self.verticalLayout.addLayout(self.buttonLayout)


        self.retranslateUi(ConnectionSettingsWindow)

        QMetaObject.connectSlotsByName(ConnectionSettingsWindow)
    # setupUi

    def retranslateUi(self, ConnectionSettingsWindow):
        ConnectionSettingsWindow.setWindowTitle(QCoreApplication.translate("ConnectionSettingsWindow", u"\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438 \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0439", None))
        self.labelName.setText(QCoreApplication.translate("ConnectionSettingsWindow", u"\u0418\u043c\u044f:", None))
        self.labelUrl.setText(QCoreApplication.translate("ConnectionSettingsWindow", u"URL:", None))
        self.labelToken.setText(QCoreApplication.translate("ConnectionSettingsWindow", u"Token:", None))
        self.saveButton.setText(QCoreApplication.translate("ConnectionSettingsWindow", u"\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c", None))
        self.removeButton.setText(QCoreApplication.translate("ConnectionSettingsWindow", u"\u0423\u0434\u0430\u043b\u0438\u0442\u044c", None))
        self.clearButton.setText(QCoreApplication.translate("ConnectionSettingsWindow", u"\u041e\u0447\u0438\u0441\u0442\u0438\u0442\u044c", None))
    # retranslateUi

