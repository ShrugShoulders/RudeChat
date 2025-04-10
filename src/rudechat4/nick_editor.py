from rudechat4.global_variables import *
from rudechat4.shared_imports import *

class NickEditor(QWidget):
    def __init__(self, callback, nick = "", color = ""):
        super().__init__()

        self.callback = callback

        self.nick = nick
        self.color = color

        self.setFixedSize(336, 126)
        self.layout = QGridLayout(self)

        self.create_widgets()
    
    def create_widgets(self):
        self.nick_label = QLabel("Nickname")
        self.nick_input = QLineEdit()
        self.nick_input.setText(self.nick)

        self.layout.addWidget(self.nick_label, 0, 0)
        self.layout.addWidget(self.nick_input, 0, 1, 1, 2)

        self.color_label = QLabel("Color")
        self.color_input = QLineEdit()
        self.color_input.setText(self.color)
        self.color_pick = QPushButton("Pick Color")
        self.color_pick.clicked.connect(self.pick_colour)

        self.layout.addWidget(self.color_label, 1, 0)
        self.layout.addWidget(self.color_input, 1, 1)
        self.layout.addWidget(self.color_pick, 1, 2)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save)
        
        self.layout.addWidget(self.save_button, 3, 0, 1, 3)

    def pick_colour(self):
        color = QColorDialog.getColor(QColor(self.color_input.text()))

        self.color_input.setText(color.name())

    def save(self):
        self.callback(self.nick_input.text(), self.color_input.text())
        self.close()