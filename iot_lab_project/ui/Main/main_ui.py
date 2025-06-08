# -*- coding: utf-8 -*-

################################################################################
# Form generated from reading UI file 'main_ui.ui'
##
# Created by: Qt User Interface Compiler version 6.8.3
##
# WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
                            QMetaObject, QObject, QPoint, QRect,
                            QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
                           QFont, QFontDatabase, QGradient, QIcon,
                           QImage, QKeySequence, QLinearGradient, QPainter,
                           QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QHBoxLayout,
                               QLabel, QMainWindow, QPushButton, QScrollArea,
                               QSizePolicy, QSpacerItem, QTabWidget, QTextEdit,
                               QToolButton, QVBoxLayout, QWidget)
import resources.resources_rc


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(900, 600)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.topPanel = QFrame(self.centralwidget)
        self.topPanel.setObjectName(u"topPanel")
        self.topPanel.setFrameShape(QFrame.StyledPanel)
        self.topPanel.setFrameShadow(QFrame.Raised)
        self.horizontalLayoutTopInfo = QHBoxLayout(self.topPanel)
        self.horizontalLayoutTopInfo.setSpacing(8)
        self.horizontalLayoutTopInfo.setObjectName(u"horizontalLayoutTopInfo")
        self.horizontalLayoutTopInfo.setContentsMargins(10, 5, 10, 5)
        self.connectionStatusLabel = QLabel(self.topPanel)
        self.connectionStatusLabel.setObjectName(u"connectionStatusLabel")
        self.connectionStatusLabel.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter)

        self.horizontalLayoutTopInfo.addWidget(self.connectionStatusLabel)

        self.connectionStatusText = QLabel(self.topPanel)
        self.connectionStatusText.setObjectName(u"connectionStatusText")
        self.connectionStatusText.setMinimumWidth(120)
        self.connectionStatusText.setMaximumWidth(120)
        self.connectionStatusText.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.horizontalLayoutTopInfo.addWidget(self.connectionStatusText)

        self.comboConnections = QComboBox(self.topPanel)
        self.comboConnections.setObjectName(u"comboConnections")
        self.comboConnections.setMinimumWidth(200)

        self.horizontalLayoutTopInfo.addWidget(self.comboConnections)

        self.btnConnectSettings = QToolButton(self.topPanel)
        self.btnConnectSettings.setObjectName(u"btnConnectSettings")
        self.btnConnectSettings.setMinimumSize(QSize(32, 32))
        icon = QIcon()
        icon.addFile(u":/icon/icons/settings.png", QSize(),
                     QIcon.Mode.Normal, QIcon.State.Off)
        self.btnConnectSettings.setIcon(icon)
        self.btnConnectSettings.setIconSize(QSize(24, 24))
        self.btnConnectSettings.setAutoRaise(True)

        self.horizontalLayoutTopInfo.addWidget(self.btnConnectSettings)

        self.btnConnect = QToolButton(self.topPanel)
        self.btnConnect.setObjectName(u"btnConnect")
        self.btnConnect.setMinimumSize(QSize(32, 32))
        icon1 = QIcon()
        icon1.addFile(u":/icon/icons/connect.png", QSize(),
                      QIcon.Mode.Normal, QIcon.State.Off)
        self.btnConnect.setIcon(icon1)
        self.btnConnect.setIconSize(QSize(24, 24))
        self.btnConnect.setAutoRaise(True)

        self.horizontalLayoutTopInfo.addWidget(self.btnConnect)

        self.btnGetDevices = QToolButton(self.topPanel)
        self.btnGetDevices.setObjectName(u"btnGetDevices")
        self.btnGetDevices.setMinimumSize(QSize(32, 32))
        icon2 = QIcon()
        icon2.addFile(u":/icon/icons/get_devices.png", QSize(),
                      QIcon.Mode.Normal, QIcon.State.Off)
        self.btnGetDevices.setIcon(icon2)
        self.btnGetDevices.setIconSize(QSize(24, 24))
        self.btnGetDevices.setAutoRaise(True)

        self.horizontalLayoutTopInfo.addWidget(self.btnGetDevices)

        self.horizontalSpacer = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayoutTopInfo.addItem(self.horizontalSpacer)

        self.btnProfileLabel = QPushButton(self.topPanel)
        self.btnProfileLabel.setObjectName(u"btnProfileLabel")
        self.btnProfileLabel.setFlat(True)

        self.horizontalLayoutTopInfo.addWidget(self.btnProfileLabel)

        self.btnLogout = QToolButton(self.topPanel)
        self.btnLogout.setObjectName(u"btnLogout")
        self.btnLogout.setMinimumSize(QSize(32, 32))
        icon3 = QIcon()
        icon3.addFile(u":/icon/icons/logout.png", QSize(),
                      QIcon.Mode.Normal, QIcon.State.Off)
        self.btnLogout.setIcon(icon3)
        self.btnLogout.setIconSize(QSize(24, 24))
        self.btnLogout.setAutoRaise(True)

        self.horizontalLayoutTopInfo.addWidget(self.btnLogout)

        self.verticalLayout.addWidget(self.topPanel)

        self.tabWidgetMain = QTabWidget(self.centralwidget)
        self.tabWidgetMain.setObjectName(u"tabWidgetMain")
        self.tabWidgetMain.setIconSize(QSize(28, 28))
        self.tabDevices = QWidget()
        self.tabDevices.setObjectName(u"tabDevices")
        self.verticalLayoutDevices = QVBoxLayout(self.tabDevices)
        self.verticalLayoutDevices.setObjectName(u"verticalLayoutDevices")
        self.scrollAreaDevices = QScrollArea(self.tabDevices)
        self.scrollAreaDevices.setObjectName(u"scrollAreaDevices")
        self.scrollAreaDevices.setWidgetResizable(True)
        self.scrollAreaDevices.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(
            u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 856, 439))
        self.layoutDeviceList = QVBoxLayout(self.scrollAreaWidgetContents)
        self.layoutDeviceList.setObjectName(u"layoutDeviceList")
        self.scrollAreaDevices.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayoutDevices.addWidget(self.scrollAreaDevices)

        icon4 = QIcon()
        icon4.addFile(u":/icon/icons/devices.png", QSize(),
                      QIcon.Mode.Normal, QIcon.State.Off)
        self.tabWidgetMain.addTab(self.tabDevices, icon4, "")
        self.tabLogs = QWidget()
        self.tabLogs.setObjectName(u"tabLogs")
        self.verticalLayoutLogs = QVBoxLayout(self.tabLogs)
        self.verticalLayoutLogs.setObjectName(u"verticalLayoutLogs")
        self.textEditLogs = QTextEdit(self.tabLogs)
        self.textEditLogs.setObjectName(u"textEditLogs")
        self.textEditLogs.setReadOnly(True)

        self.verticalLayoutLogs.addWidget(self.textEditLogs)

        icon5 = QIcon()
        icon5.addFile(u":/icon/icons/log.png", QSize(),
                      QIcon.Mode.Normal, QIcon.State.Off)
        self.tabWidgetMain.addTab(self.tabLogs, icon5, "")

        self.verticalLayout.addWidget(self.tabWidgetMain)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        self.tabWidgetMain.setCurrentIndex(0)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate(
            "MainWindow", u"IoT \u041b\u0430\u0431\u043e\u0440\u0430\u0442\u043e\u0440\u0438\u044f", None))
        self.connectionStatusLabel.setText(QCoreApplication.translate(
            "MainWindow", u"\u0421\u0442\u0430\u0442\u0443\u0441:", None))
        self.connectionStatusText.setText(QCoreApplication.translate(
            "MainWindow", u"\u041d\u0435 \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u043e", None))
# if QT_CONFIG(tooltip)
        self.btnConnectSettings.setToolTip(QCoreApplication.translate(
            "MainWindow", u"\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438 \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0439", None))
# endif // QT_CONFIG(tooltip)
# if QT_CONFIG(tooltip)
        self.btnConnect.setToolTip(QCoreApplication.translate(
            "MainWindow", u"\u041f\u043e\u0434\u043a\u043b\u044e\u0447\u0438\u0442\u044c\u0441\u044f", None))
# endif // QT_CONFIG(tooltip)
# if QT_CONFIG(tooltip)
        self.btnGetDevices.setToolTip(QCoreApplication.translate(
            "MainWindow", u"\u041f\u043e\u043b\u0443\u0447\u0438\u0442\u044c \u0443\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u0430", None))
# endif // QT_CONFIG(tooltip)
# if QT_CONFIG(tooltip)
        self.btnProfileLabel.setToolTip(QCoreApplication.translate(
            "MainWindow", u"\u041f\u0440\u043e\u0444\u0438\u043b\u044c", None))
# endif // QT_CONFIG(tooltip)
        self.btnProfileLabel.setText(QCoreApplication.translate(
            "MainWindow", u"\u0424\u0430\u043c\u0438\u043b\u0438\u044f \u0418.\u041e.", None))
# if QT_CONFIG(tooltip)
        self.btnLogout.setToolTip(QCoreApplication.translate(
            "MainWindow", u"\u0412\u044b\u0439\u0442\u0438", None))
# endif // QT_CONFIG(tooltip)
        self.tabWidgetMain.setTabText(self.tabWidgetMain.indexOf(self.tabDevices), QCoreApplication.translate(
            "MainWindow", u"\u0423\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u0430", None))
        self.textEditLogs.setPlaceholderText(QCoreApplication.translate(
            "MainWindow", u"\u0417\u0434\u0435\u0441\u044c \u043e\u0442\u043e\u0431\u0440\u0430\u0436\u0430\u044e\u0442\u0441\u044f \u043b\u043e\u0433\u0438 \u0440\u0430\u0431\u043e\u0442\u044b \u043f\u0440\u043e\u0433\u0440\u0430\u043c\u043c\u044b...", None))
        self.tabWidgetMain.setTabText(self.tabWidgetMain.indexOf(self.tabLogs), QCoreApplication.translate(
            "MainWindow", u"\u0416\u0443\u0440\u043d\u0430\u043b", None))
    # retranslateUi
