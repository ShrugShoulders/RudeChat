#!/usr/bin/env python3
"""Colour input row: a text field plus a Pick button that opens the colour dialog."""
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

class RudeColorOption(QWidget):
    """Widget for editing one colour value.

        The value is a colour name or hex string. Use ``text`` and ``setText`` to
        read and write it.
    """
    def __init__(self, parent):
        """Build the text field and the Pick button."""
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
        """Set the colour text."""
        self.inputField.setText(text)

    def text(self):
        """Return the colour text as typed."""
        return self.inputField.text()

    def pickColor(self):
        """Open the colour dialog and store the chosen colour as a hex string.

            Does nothing if the dialog is cancelled.
        """
        newColor = QColorDialog.getColor(QColor(self.text()))

        if newColor.isValid():
            self.setText(newColor.name())