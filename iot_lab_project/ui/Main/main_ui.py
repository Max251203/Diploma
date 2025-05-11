# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_ui.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QHBoxLayout,
    QMainWindow, QPushButton, QScrollArea, QSizePolicy,
    QTabWidget, QTextEdit, QToolButton, QVBoxLayout,
    QWidget)
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
        self.horizontalLayoutTopInfo = QHBoxLayout()
        self.horizontalLayoutTopInfo.setObjectName(u"horizontalLayoutTopInfo")
        self.connectionStatus = QToolButton(self.centralwidget)
        self.connectionStatus.setObjectName(u"connectionStatus")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.connectionStatus.sizePolicy().hasHeightForWidth())
        self.connectionStatus.setSizePolicy(sizePolicy)
        self.connectionStatus.setMinimumSize(QSize(24, 24))
        self.connectionStatus.setMaximumSize(QSize(24, 24))
        self.connectionStatus.setIconSize(QSize(24, 24))
        self.connectionStatus.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.connectionStatus.setAutoRaise(True)

        self.horizontalLayoutTopInfo.addWidget(self.connectionStatus)

        self.comboConnections = QComboBox(self.centralwidget)
        self.comboConnections.setObjectName(u"comboConnections")

        self.horizontalLayoutTopInfo.addWidget(self.comboConnections)

        self.btnConnectSettings = QPushButton(self.centralwidget)
        self.btnConnectSettings.setObjectName(u"btnConnectSettings")

        self.horizontalLayoutTopInfo.addWidget(self.btnConnectSettings)


        self.verticalLayout.addLayout(self.horizontalLayoutTopInfo)

        self.topButtonPanel = QFrame(self.centralwidget)
        self.topButtonPanel.setObjectName(u"topButtonPanel")
        self.topButtonPanel.setFrameShape(QFrame.StyledPanel)
        self.horizontalLayoutButtons = QHBoxLayout(self.topButtonPanel)
        self.horizontalLayoutButtons.setObjectName(u"horizontalLayoutButtons")
        self.btnConnect = QPushButton(self.topButtonPanel)
        self.btnConnect.setObjectName(u"btnConnect")

        self.horizontalLayoutButtons.addWidget(self.btnConnect)

        self.btnGetDevices = QPushButton(self.topButtonPanel)
        self.btnGetDevices.setObjectName(u"btnGetDevices")
        icon = QIcon()
        icon.addFile(u":/icon/icons/get_devices.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnGetDevices.setIcon(icon)

        self.horizontalLayoutButtons.addWidget(self.btnGetDevices)


        self.verticalLayout.addWidget(self.topButtonPanel)

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
        self.scrollAreaDevices.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 856, 439))
        self.layoutDeviceList = QVBoxLayout(self.scrollAreaWidgetContents)
        self.layoutDeviceList.setObjectName(u"layoutDeviceList")
        self.scrollAreaDevices.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayoutDevices.addWidget(self.scrollAreaDevices)

        icon1 = QIcon()
        icon1.addFile(u":/icon/icons/devices.png", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        self.tabWidgetMain.addTab(self.tabDevices, icon1, "")
        self.tabLogs = QWidget()
        self.tabLogs.setObjectName(u"tabLogs")
        self.verticalLayoutLogs = QVBoxLayout(self.tabLogs)
        self.verticalLayoutLogs.setObjectName(u"verticalLayoutLogs")
        self.textEditLogs = QTextEdit(self.tabLogs)
        self.textEditLogs.setObjectName(u"textEditLogs")
        self.textEditLogs.setReadOnly(True)

        self.verticalLayoutLogs.addWidget(self.textEditLogs)

        icon2 = QIcon()
        icon2.addFile(u":/icon/icons/log.png", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        self.tabWidgetMain.addTab(self.tabLogs, icon2, "")

        self.verticalLayout.addWidget(self.tabWidgetMain)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        self.tabWidgetMain.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"IoT \u041b\u0430\u0431\u043e\u0440\u0430\u0442\u043e\u0440\u0438\u044f", None))
        self.connectionStatus.setText("")
#if QT_CONFIG(tooltip)
        self.btnConnectSettings.setToolTip(QCoreApplication.translate("MainWindow", u"\u041e\u0442\u043a\u0440\u044b\u0442\u044c \u0441\u043f\u0438\u0441\u043e\u043a \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0439", None))
#endif // QT_CONFIG(tooltip)
        self.btnConnectSettings.setText(QCoreApplication.translate("MainWindow", u"\u0412\u0430\u0440\u0438\u0430\u043d\u0442\u044b \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u044f", None))
        self.btnConnect.setText(QCoreApplication.translate("MainWindow", u"\u041f\u043e\u0434\u043a\u043b\u044e\u0447\u0438\u0442\u044c\u0441\u044f", None))
        self.btnGetDevices.setText(QCoreApplication.translate("MainWindow", u"\u041f\u043e\u043b\u0443\u0447\u0438\u0442\u044c \u0443\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u0430", None))
        self.tabWidgetMain.setTabText(self.tabWidgetMain.indexOf(self.tabDevices), QCoreApplication.translate("MainWindow", u"\u0423\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u0430", None))
        self.textEditLogs.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\u0417\u0434\u0435\u0441\u044c \u043e\u0442\u043e\u0431\u0440\u0430\u0436\u0430\u044e\u0442\u0441\u044f \u043b\u043e\u0433\u0438 \u0440\u0430\u0431\u043e\u0442\u044b \u043f\u0440\u043e\u0433\u0440\u0430\u043c\u043c\u044b...", None))
        self.tabWidgetMain.setTabText(self.tabWidgetMain.indexOf(self.tabLogs), QCoreApplication.translate("MainWindow", u"\u0416\u0443\u0440\u043d\u0430\u043b \u0441\u043e\u0431\u044b\u0442\u0438\u0439", None))
    # retranslateUi

