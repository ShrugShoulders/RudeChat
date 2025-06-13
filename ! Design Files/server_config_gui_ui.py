# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'server_config_gui.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_server_config_window(object):
    def setupUi(self, server_config_window):
        if not server_config_window.objectName():
            server_config_window.setObjectName(u"server_config_window")
        server_config_window.resize(450, 500)
        self.base_layout = QVBoxLayout(server_config_window)
        self.base_layout.setSpacing(5)
        self.base_layout.setObjectName(u"base_layout")
        self.base_layout.setContentsMargins(5, 5, 5, 5)
        self.file_selector = QComboBox(server_config_window)
        self.file_selector.setObjectName(u"file_selector")

        self.base_layout.addWidget(self.file_selector)

        self.options_pane = QScrollArea(server_config_window)
        self.options_pane.setObjectName(u"options_pane")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.options_pane.sizePolicy().hasHeightForWidth())
        self.options_pane.setSizePolicy(sizePolicy)
        self.options_pane.setFrameShape(QFrame.Shape.NoFrame)
        self.options_pane.setFrameShadow(QFrame.Shadow.Plain)
        self.options_pane.setLineWidth(1)
        self.options_pane.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.options_pane.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.options_pane.setWidgetResizable(True)
        self.options_pane_contents = QWidget()
        self.options_pane_contents.setObjectName(u"options_pane_contents")
        self.options_pane_contents.setGeometry(QRect(0, 0, 440, 422))
        sizePolicy.setHeightForWidth(self.options_pane_contents.sizePolicy().hasHeightForWidth())
        self.options_pane_contents.setSizePolicy(sizePolicy)
        self.gridLayout = QGridLayout(self.options_pane_contents)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.lineEdit = QLineEdit(self.options_pane_contents)
        self.lineEdit.setObjectName(u"lineEdit")

        self.gridLayout.addWidget(self.lineEdit, 0, 1, 1, 1)

        self.label = QLabel(self.options_pane_contents)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.label_2 = QLabel(self.options_pane_contents)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.checkBox = QCheckBox(self.options_pane_contents)
        self.checkBox.setObjectName(u"checkBox")

        self.gridLayout.addWidget(self.checkBox, 1, 1, 1, 1)

        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 1)
        self.options_pane.setWidget(self.options_pane_contents)

        self.base_layout.addWidget(self.options_pane)

        self.file_operations = QWidget(server_config_window)
        self.file_operations.setObjectName(u"file_operations")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.file_operations.sizePolicy().hasHeightForWidth())
        self.file_operations.setSizePolicy(sizePolicy1)
        self.file_operations_layout = QHBoxLayout(self.file_operations)
        self.file_operations_layout.setSpacing(5)
        self.file_operations_layout.setObjectName(u"file_operations_layout")
        self.file_operations_layout.setContentsMargins(0, 0, 0, 0)
        self.save_button = QPushButton(self.file_operations)
        self.save_button.setObjectName(u"save_button")

        self.file_operations_layout.addWidget(self.save_button)

        self.save_as_new_button = QPushButton(self.file_operations)
        self.save_as_new_button.setObjectName(u"save_as_new_button")

        self.file_operations_layout.addWidget(self.save_as_new_button)

        self.delete_button = QPushButton(self.file_operations)
        self.delete_button.setObjectName(u"delete_button")

        self.file_operations_layout.addWidget(self.delete_button)


        self.base_layout.addWidget(self.file_operations)


        self.retranslateUi(server_config_window)

        QMetaObject.connectSlotsByName(server_config_window)
    # setupUi

    def retranslateUi(self, server_config_window):
        server_config_window.setWindowTitle(QCoreApplication.translate("server_config_window", u"Server Configuration", None))
        self.label.setText(QCoreApplication.translate("server_config_window", u"TextLabel", None))
        self.label_2.setText(QCoreApplication.translate("server_config_window", u"TextLabel", None))
        self.checkBox.setText("")
        self.save_button.setText(QCoreApplication.translate("server_config_window", u"Save", None))
        self.save_as_new_button.setText(QCoreApplication.translate("server_config_window", u"Save as New", None))
        self.delete_button.setText(QCoreApplication.translate("server_config_window", u"Delete", None))
    # retranslateUi

