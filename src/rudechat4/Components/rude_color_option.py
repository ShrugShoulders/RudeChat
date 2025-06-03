#!/usr/bin/env python3
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

class RudeColorOption(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.setLayout(QHBoxLayout())

        self.layout().setContentsMargins(0, 0, 0, 0)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.inputField = QLineEdit(self)
        self.inputField.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.editButton = QToolButton(self)
        self.editButton.setText('Pick...')
        self.editButton.clicked.connect(self.pickColor)

        self.layout().addWidget(self.inputField)
        self.layout().addWidget(self.editButton)

    def setText(self, text):
        self.inputField.setText(text)

    def text(self):
        return self.inputField.text()
    
    def pickColor(self):
        newColor = QColorDialog.getColor(QColor(self.text()))

        if newColor.isValid():
            self.setText(newColor.name())