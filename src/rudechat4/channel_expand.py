from rudechat4.shared_imports import *

class ChannelExp(QWidget):
    def __init__(self, channels, set):
        super().__init__()
        self.channels = channels
        self.set = set

        self.layout = QGridLayout(self)

        self.create_widgets()

    def create_widgets(self):
        self.channel_list = QListWidget()
        self.layout.addWidget(self.channel_list, 0, 0)

        self.load_channels()

        self.delete_channel_button = QPushButton("-")
        self.delete_channel_button.setEnabled(False)
        self.delete_channel_button.clicked.connect(self.remove_channel)
        self.layout.addWidget(self.delete_channel_button, 0, 1)

        self.channel_input = QLineEdit()
        self.channel_input.setPlaceholderText("Type channel here...")

        self.layout.addWidget(self.channel_input, 1, 0)

        self.add_channel_button = QPushButton("+")
        self.add_channel_button.setEnabled(False)
        self.add_channel_button.clicked.connect(self.add_channel)
        self.layout.addWidget(self.add_channel_button, 1, 1)

        self.channel_input.textChanged.connect(lambda: self.add_channel_button.setEnabled(self.channel_input.text() != ""))
        self.channel_list.itemSelectionChanged.connect(lambda: self.delete_channel_button.setEnabled(True))

        self.done_button = QPushButton("Done")
        self.done_button.clicked.connect(self.save_channels)
        self.layout.addWidget(self.done_button, 2, 0, 1, 2)

    def load_channels(self):
        for channel in self.channels.split(","):
            self.channel_list.addItem(channel)

    def add_channel(self):
        self.channel_list.addItem(self.channel_input.text())
        self.channel_input.clear()

    def remove_channel(self):
        self.channel_list.takeItem(self.channel_list.currentRow())

    def save_channels(self):
        result = []

        for i in range (0, self.channel_list.count()):
            result.append(self.channel_list.item(i).text())
        
        self.set(','.join(result))
        self.close()