# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gui_config_gui.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_GUIConfig(object):
    def setupUi(self, GUIConfig):
        if not GUIConfig.objectName():
            GUIConfig.setObjectName(u"GUIConfig")
        GUIConfig.resize(700, 500)
        self.verticalLayout = QVBoxLayout(GUIConfig)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.options_pane = QHBoxLayout()
        self.options_pane.setObjectName(u"options_pane")
        self.gui_section = QGroupBox(GUIConfig)
        self.gui_section.setObjectName(u"gui_section")
        self.gui_section.setFlat(False)
        self.gridLayout = QGridLayout(self.gui_section)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setHorizontalSpacing(0)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gui_options = QScrollArea(self.gui_section)
        self.gui_options.setObjectName(u"gui_options")
        self.gui_options.setFrameShape(QFrame.Shape.NoFrame)
        self.gui_options.setWidgetResizable(True)
        self.gui_options_contents = QWidget()
        self.gui_options_contents.setObjectName(u"gui_options_contents")
        self.gui_options_contents.setGeometry(QRect(0, 0, 323, 417))
        self.verticalLayout_2 = QVBoxLayout(self.gui_options_contents)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.example_widget_string = QWidget(self.gui_options_contents)
        self.example_widget_string.setObjectName(u"example_widget_string")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.example_widget_string.sizePolicy().hasHeightForWidth())
        self.example_widget_string.setSizePolicy(sizePolicy)
        self.horizontalLayout_2 = QHBoxLayout(self.example_widget_string)
        self.horizontalLayout_2.setSpacing(15)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(5, 5, 5, 5)
        self.option_label_string = QLabel(self.example_widget_string)
        self.option_label_string.setObjectName(u"option_label_string")
        self.option_label_string.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_2.addWidget(self.option_label_string)

        self.option_input = QLineEdit(self.example_widget_string)
        self.option_input.setObjectName(u"option_input")

        self.horizontalLayout_2.addWidget(self.option_input)

        self.horizontalLayout_2.setStretch(0, 1)
        self.horizontalLayout_2.setStretch(1, 1)

        self.verticalLayout_2.addWidget(self.example_widget_string)

        self.example_widget_checkbox = QWidget(self.gui_options_contents)
        self.example_widget_checkbox.setObjectName(u"example_widget_checkbox")
        sizePolicy.setHeightForWidth(self.example_widget_checkbox.sizePolicy().hasHeightForWidth())
        self.example_widget_checkbox.setSizePolicy(sizePolicy)
        self.horizontalLayout_3 = QHBoxLayout(self.example_widget_checkbox)
        self.horizontalLayout_3.setSpacing(15)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(5, 5, 5, 5)
        self.option_label_checkbox = QLabel(self.example_widget_checkbox)
        self.option_label_checkbox.setObjectName(u"option_label_checkbox")
        self.option_label_checkbox.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_3.addWidget(self.option_label_checkbox)

        self.option_checkbox = QCheckBox(self.example_widget_checkbox)
        self.option_checkbox.setObjectName(u"option_checkbox")

        self.horizontalLayout_3.addWidget(self.option_checkbox)


        self.verticalLayout_2.addWidget(self.example_widget_checkbox)

        self.gui_options.setWidget(self.gui_options_contents)

        self.gridLayout.addWidget(self.gui_options, 0, 0, 1, 1)


        self.options_pane.addWidget(self.gui_section)

        self.widgets_section = QGroupBox(GUIConfig)
        self.widgets_section.setObjectName(u"widgets_section")
        self.widgets_section.setFlat(False)
        self.gridLayout_3 = QGridLayout(self.widgets_section)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setHorizontalSpacing(0)
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.widgets_options = QScrollArea(self.widgets_section)
        self.widgets_options.setObjectName(u"widgets_options")
        self.widgets_options.setFrameShape(QFrame.Shape.NoFrame)
        self.widgets_options.setWidgetResizable(True)
        self.widgets_options_contents = QWidget()
        self.widgets_options_contents.setObjectName(u"widgets_options_contents")
        self.widgets_options_contents.setGeometry(QRect(0, 0, 323, 417))
        self.verticalLayout_4 = QVBoxLayout(self.widgets_options_contents)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.example_widget_string_2 = QWidget(self.widgets_options_contents)
        self.example_widget_string_2.setObjectName(u"example_widget_string_2")
        sizePolicy.setHeightForWidth(self.example_widget_string_2.sizePolicy().hasHeightForWidth())
        self.example_widget_string_2.setSizePolicy(sizePolicy)
        self.horizontalLayout_6 = QHBoxLayout(self.example_widget_string_2)
        self.horizontalLayout_6.setSpacing(15)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(5, 5, 5, 5)
        self.option_label_string_2 = QLabel(self.example_widget_string_2)
        self.option_label_string_2.setObjectName(u"option_label_string_2")
        self.option_label_string_2.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_6.addWidget(self.option_label_string_2)

        self.option_input_2 = QLineEdit(self.example_widget_string_2)
        self.option_input_2.setObjectName(u"option_input_2")

        self.horizontalLayout_6.addWidget(self.option_input_2)

        self.horizontalLayout_6.setStretch(0, 1)
        self.horizontalLayout_6.setStretch(1, 1)

        self.verticalLayout_4.addWidget(self.example_widget_string_2)

        self.example_widget_checkbox_2 = QWidget(self.widgets_options_contents)
        self.example_widget_checkbox_2.setObjectName(u"example_widget_checkbox_2")
        sizePolicy.setHeightForWidth(self.example_widget_checkbox_2.sizePolicy().hasHeightForWidth())
        self.example_widget_checkbox_2.setSizePolicy(sizePolicy)
        self.horizontalLayout_7 = QHBoxLayout(self.example_widget_checkbox_2)
        self.horizontalLayout_7.setSpacing(15)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(5, 5, 5, 5)
        self.option_label_checkbox_2 = QLabel(self.example_widget_checkbox_2)
        self.option_label_checkbox_2.setObjectName(u"option_label_checkbox_2")
        self.option_label_checkbox_2.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_7.addWidget(self.option_label_checkbox_2)

        self.option_checkbox_2 = QCheckBox(self.example_widget_checkbox_2)
        self.option_checkbox_2.setObjectName(u"option_checkbox_2")

        self.horizontalLayout_7.addWidget(self.option_checkbox_2)


        self.verticalLayout_4.addWidget(self.example_widget_checkbox_2)

        self.widgets_options.setWidget(self.widgets_options_contents)

        self.gridLayout_3.addWidget(self.widgets_options, 0, 0, 1, 1)


        self.options_pane.addWidget(self.widgets_section)


        self.verticalLayout.addLayout(self.options_pane)

        self.save_button = QPushButton(GUIConfig)
        self.save_button.setObjectName(u"save_button")

        self.verticalLayout.addWidget(self.save_button)


        self.retranslateUi(GUIConfig)

        QMetaObject.connectSlotsByName(GUIConfig)
    # setupUi

    def retranslateUi(self, GUIConfig):
        GUIConfig.setWindowTitle(QCoreApplication.translate("GUIConfig", u"GUI Configuration", None))
        self.gui_section.setTitle(QCoreApplication.translate("GUIConfig", u"GUI", None))
        self.option_label_string.setText(QCoreApplication.translate("GUIConfig", u"String", None))
        self.option_label_checkbox.setText(QCoreApplication.translate("GUIConfig", u"Checkbox", None))
        self.widgets_section.setTitle(QCoreApplication.translate("GUIConfig", u"Widgets", None))
        self.option_label_string_2.setText(QCoreApplication.translate("GUIConfig", u"String", None))
        self.option_label_checkbox_2.setText(QCoreApplication.translate("GUIConfig", u"Checkbox", None))
        self.save_button.setText(QCoreApplication.translate("GUIConfig", u"Save", None))
    # retranslateUi

