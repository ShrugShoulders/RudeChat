# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'firstrun_config_gui.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_FirstRunConfig(object):
    def setupUi(self, FirstRunConfig):
        if not FirstRunConfig.objectName():
            FirstRunConfig.setObjectName(u"FirstRunConfig")
        FirstRunConfig.resize(450, 500)
        self.verticalLayout = QVBoxLayout(FirstRunConfig)
        self.verticalLayout.setSpacing(5)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(5, 5, 5, 5)
        self.label = QLabel(FirstRunConfig)
        self.label.setObjectName(u"label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)

        self.verticalLayout.addWidget(self.label)

        self.options_pane = QScrollArea(FirstRunConfig)
        self.options_pane.setObjectName(u"options_pane")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.options_pane.sizePolicy().hasHeightForWidth())
        self.options_pane.setSizePolicy(sizePolicy1)
        self.options_pane.setLineWidth(1)
        self.options_pane.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.options_pane.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.options_pane.setWidgetResizable(True)
        self.options_pane_contents = QWidget()
        self.options_pane_contents.setObjectName(u"options_pane_contents")
        self.options_pane_contents.setGeometry(QRect(0, 0, 438, 391))
        sizePolicy1.setHeightForWidth(self.options_pane_contents.sizePolicy().hasHeightForWidth())
        self.options_pane_contents.setSizePolicy(sizePolicy1)
        self.verticalLayout_2 = QVBoxLayout(self.options_pane_contents)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.example_widget_string = QWidget(self.options_pane_contents)
        self.example_widget_string.setObjectName(u"example_widget_string")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.example_widget_string.sizePolicy().hasHeightForWidth())
        self.example_widget_string.setSizePolicy(sizePolicy2)
        self.horizontalLayout = QHBoxLayout(self.example_widget_string)
        self.horizontalLayout.setSpacing(15)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(5, 5, 5, 5)
        self.option_label_string = QLabel(self.example_widget_string)
        self.option_label_string.setObjectName(u"option_label_string")
        self.option_label_string.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout.addWidget(self.option_label_string)

        self.option_input = QLineEdit(self.example_widget_string)
        self.option_input.setObjectName(u"option_input")

        self.horizontalLayout.addWidget(self.option_input)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 1)

        self.verticalLayout_2.addWidget(self.example_widget_string)

        self.example_widget_checkbox = QWidget(self.options_pane_contents)
        self.example_widget_checkbox.setObjectName(u"example_widget_checkbox")
        sizePolicy2.setHeightForWidth(self.example_widget_checkbox.sizePolicy().hasHeightForWidth())
        self.example_widget_checkbox.setSizePolicy(sizePolicy2)
        self.horizontalLayout_2 = QHBoxLayout(self.example_widget_checkbox)
        self.horizontalLayout_2.setSpacing(15)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(5, 5, 5, 5)
        self.option_label_checkbox = QLabel(self.example_widget_checkbox)
        self.option_label_checkbox.setObjectName(u"option_label_checkbox")
        self.option_label_checkbox.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_2.addWidget(self.option_label_checkbox)

        self.option_checkbox = QCheckBox(self.example_widget_checkbox)
        self.option_checkbox.setObjectName(u"option_checkbox")

        self.horizontalLayout_2.addWidget(self.option_checkbox)


        self.verticalLayout_2.addWidget(self.example_widget_checkbox)

        self.options_pane.setWidget(self.options_pane_contents)

        self.verticalLayout.addWidget(self.options_pane)

        self.apply_button = QPushButton(FirstRunConfig)
        self.apply_button.setObjectName(u"apply_button")

        self.verticalLayout.addWidget(self.apply_button)


        self.retranslateUi(FirstRunConfig)

        QMetaObject.connectSlotsByName(FirstRunConfig)
    # setupUi

    def retranslateUi(self, FirstRunConfig):
        FirstRunConfig.setWindowTitle(QCoreApplication.translate("FirstRunConfig", u"First Run Configuration", None))
        self.label.setText(QCoreApplication.translate("FirstRunConfig", u"Welcome to RudeChat's First Run Configuration. Please adjust your settings to your liking, then click Apply to start RudeChat. This will be the only time you see this menu.", None))
        self.option_label_string.setText(QCoreApplication.translate("FirstRunConfig", u"String", None))
        self.option_label_checkbox.setText(QCoreApplication.translate("FirstRunConfig", u"Checkbox", None))
        self.apply_button.setText(QCoreApplication.translate("FirstRunConfig", u"Apply", None))
    # retranslateUi

