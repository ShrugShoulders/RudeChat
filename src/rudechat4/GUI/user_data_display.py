#!/usr/bin/env python3
from rudechat4.shared_imports import * 
from rudechat4.global_variables import *

class RudeUserData(object):
    def __init__(self, parent):
        super().__init__()
        self.parentGui = parent

    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setWindowIcon(QIcon(ICON_FILE))
        Form.resize(412, 390)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QLabel(parent=Form)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)

        self.scrollArea = QScrollArea(parent=Form)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")

        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 386, 273))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")

        self.gridLayout = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setObjectName("gridLayout")

        labels = [
            (0, "Nickname", "racko"),
            (1, "Username", "~racko"),
            (2, "Host", "user/racko"),
            (3, "Server", "urmum.libera.chat"),
            (4, "Channel", "#rudechat"),
            (5, "Status", "Active"),
            (6, "Mode", "#rudechat()"),
            (7, "Account", "racko"),
            (8, "Who Message", "Racko! :3"),
            (9, "Shared Channels", "#rudechat"),
        ]

        for row, key, value in labels:
            label_key = QLabel(parent=self.scrollAreaWidgetContents)
            sizePolicy.setHeightForWidth(label_key.sizePolicy().hasHeightForWidth())
            label_key.setSizePolicy(sizePolicy)
            label_key.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTrailing | Qt.AlignmentFlag.AlignVCenter)
            label_key.setText(f"<b>{key}</b>")
            self.gridLayout.addWidget(label_key, row, 0, 1, 1)

            label_value = QLabel(parent=self.scrollAreaWidgetContents)
            sizePolicy.setHeightForWidth(label_value.sizePolicy().hasHeightForWidth())
            label_value.setSizePolicy(sizePolicy)
            label_value.setText(value)
            self.gridLayout.addWidget(label_value, row, 1, 1, 1)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)

        self.label_22 = QLabel(parent=Form)
        self.label_22.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_22.setObjectName("label_22")
        self.label_22.setText("<b>Ignore Mask Suggestion</b>")
        self.verticalLayout.addWidget(self.label_22)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.lineEdit = QLineEdit(parent=Form)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHeightForWidth(self.lineEdit.sizePolicy().hasHeightForWidth())
        self.lineEdit.setSizePolicy(sizePolicy)
        self.lineEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineEdit.setReadOnly(True)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout.addWidget(self.lineEdit)

        self.pushButton = QPushButton(parent=Form)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Form)
        QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "User Info"))
        self.label.setText(_translate("Form", "Data for <b>racko</b>"))
        self.pushButton.setText(_translate("Form", "Copy ID"))
        self.pushButton.clicked.connect(self.copy_lineedit_text)

    def copy_lineedit_text(self):
        """Copy the text in lineEdit widget"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.lineEdit.text())

    def set_user_data(self, data: dict):
        """Update the labels with values from a user info dictionary."""
        key_mapping = {
            "Nickname": data.get("nickname", ""),
            "Username": data.get("username", ""),
            "Host": data.get("host", ""),
            "Server": data.get("server", ""),
            "Channel": data.get("channel", ""),
            "Status": data.get("status", ""),
            "Mode": data.get("mode", ""),
            "Account": data.get("account", ""),
            "Who Message": data.get("who_message", ""),
            "Shared Channels": data.get("shared-channels", ""),
        }

        ignore_suggestion = f"*!{data['username']}@{data['host']}"
        self.lineEdit.setText(ignore_suggestion)

        # Update grid layout labels
        for i in range(self.gridLayout.rowCount()):
            key_widget = self.gridLayout.itemAtPosition(i, 0).widget()
            val_widget = self.gridLayout.itemAtPosition(i, 1).widget()
            if key_widget and val_widget:
                key = key_widget.text().replace("<b>", "").replace("</b>", "")
                if key in key_mapping:
                    val_widget.setText(key_mapping[key])

        # Update the main top label
        if "nickname" in data:
            self.label.setText(f"Data for <b>{data['nickname']}</b>")