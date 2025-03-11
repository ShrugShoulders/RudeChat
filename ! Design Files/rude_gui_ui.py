# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'rude_gui.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QHBoxLayout, QLabel,
    QLineEdit, QListView, QListWidget, QListWidgetItem,
    QMainWindow, QSizePolicy, QTextBrowser, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QSize(0, 0))
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setMinimumSize(QSize(0, 0))
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setSpacing(5)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(5, 5, 10, 5)
        self.content = QVBoxLayout()
        self.content.setSpacing(5)
        self.content.setObjectName(u"content")
        self.chat_area = QVBoxLayout()
        self.chat_area.setSpacing(5)
        self.chat_area.setObjectName(u"chat_area")
        self.topic_label = QLabel(self.centralwidget)
        self.topic_label.setObjectName(u"topic_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.topic_label.sizePolicy().hasHeightForWidth())
        self.topic_label.setSizePolicy(sizePolicy1)

        self.chat_area.addWidget(self.topic_label)

        self.display_text = QTextBrowser(self.centralwidget)
        self.display_text.setObjectName(u"display_text")

        self.chat_area.addWidget(self.display_text)


        self.content.addLayout(self.chat_area)

        self.text_input = QHBoxLayout()
        self.text_input.setSpacing(5)
        self.text_input.setObjectName(u"text_input")
        self.user_chan_display = QLabel(self.centralwidget)
        self.user_chan_display.setObjectName(u"user_chan_display")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.user_chan_display.sizePolicy().hasHeightForWidth())
        self.user_chan_display.setSizePolicy(sizePolicy2)

        self.text_input.addWidget(self.user_chan_display)

        self.input_field = QLineEdit(self.centralwidget)
        self.input_field.setObjectName(u"input_field")
        sizePolicy1.setHeightForWidth(self.input_field.sizePolicy().hasHeightForWidth())
        self.input_field.setSizePolicy(sizePolicy1)

        self.text_input.addWidget(self.input_field)


        self.content.addLayout(self.text_input)


        self.horizontalLayout.addLayout(self.content)

        self.sidebar = QVBoxLayout()
        self.sidebar.setSpacing(5)
        self.sidebar.setObjectName(u"sidebar")
        self.users_selector = QVBoxLayout()
        self.users_selector.setSpacing(5)
        self.users_selector.setObjectName(u"users_selector")
        self.user_label = QLabel(self.centralwidget)
        self.user_label.setObjectName(u"user_label")
        sizePolicy1.setHeightForWidth(self.user_label.sizePolicy().hasHeightForWidth())
        self.user_label.setSizePolicy(sizePolicy1)

        self.users_selector.addWidget(self.user_label)

        self.user_list = QListWidget(self.centralwidget)
        self.user_list.setObjectName(u"user_list")
        self.user_list.setMouseTracking(True)
        self.user_list.setAutoFillBackground(True)
        self.user_list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.user_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.user_list.setItemAlignment(Qt.AlignmentFlag.AlignLeading)

        self.users_selector.addWidget(self.user_list)


        self.sidebar.addLayout(self.users_selector)

        self.servers_selector = QVBoxLayout()
        self.servers_selector.setSpacing(5)
        self.servers_selector.setObjectName(u"servers_selector")
        self.server_label = QLabel(self.centralwidget)
        self.server_label.setObjectName(u"server_label")
        sizePolicy1.setHeightForWidth(self.server_label.sizePolicy().hasHeightForWidth())
        self.server_label.setSizePolicy(sizePolicy1)

        self.servers_selector.addWidget(self.server_label)

        self.server_list = QListWidget(self.centralwidget)
        self.server_list.setObjectName(u"server_list")
        self.server_list.setItemAlignment(Qt.AlignmentFlag.AlignLeading)

        self.servers_selector.addWidget(self.server_list)


        self.sidebar.addLayout(self.servers_selector)

        self.channels_selector = QVBoxLayout()
        self.channels_selector.setSpacing(5)
        self.channels_selector.setObjectName(u"channels_selector")
        self.channel_label = QLabel(self.centralwidget)
        self.channel_label.setObjectName(u"channel_label")
        sizePolicy1.setHeightForWidth(self.channel_label.sizePolicy().hasHeightForWidth())
        self.channel_label.setSizePolicy(sizePolicy1)

        self.channels_selector.addWidget(self.channel_label)

        self.channel_list = QListWidget(self.centralwidget)
        self.channel_list.setObjectName(u"channel_list")
        self.channel_list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.channel_list.setBatchSize(250)
        self.channel_list.setItemAlignment(Qt.AlignmentFlag.AlignLeading)

        self.channels_selector.addWidget(self.channel_list)


        self.sidebar.addLayout(self.channels_selector)

        self.sidebar.setStretch(0, 2)
        self.sidebar.setStretch(1, 1)
        self.sidebar.setStretch(2, 2)

        self.horizontalLayout.addLayout(self.sidebar)

        self.horizontalLayout.setStretch(0, 5)
        self.horizontalLayout.setStretch(1, 1)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"RudeChat", None))
        self.topic_label.setText(QCoreApplication.translate("MainWindow", u"Topic: yro'ue mother", None))
        self.user_chan_display.setText(QCoreApplication.translate("MainWindow", u"user @ #channel", None))
        self.user_label.setText(QCoreApplication.translate("MainWindow", u"Users (0)", None))
        self.server_label.setText(QCoreApplication.translate("MainWindow", u"Servers (0)", None))
        self.channel_label.setText(QCoreApplication.translate("MainWindow", u"Channels (0)", None))
    # retranslateUi

