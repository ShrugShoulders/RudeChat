#!/usr/bin/env python3
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

class ChannelListWindow(QDialog):
    def __init__(self, gui, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowIcon(QIcon(ICON_FILE))
        self.setWindowTitle("Channel List")
        self.resize(800, 400)

        self.gui = gui
        self.is_destroyed = False
        self.sort_order = "ascending"

        self.create_widgets()

        # Start periodic UI updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui_periodically)
        self.timer.start(100)

    def create_widgets(self):
        layout = QVBoxLayout(self)

        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search Channel/Topic:")
        self.search_entry = QLineEdit()
        self.search_entry.textChanged.connect(self.handle_search)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_entry)
        layout.addLayout(search_layout)

        # Tree widget (Channel list)
        self.tree = QTreeWidget()
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Channel", "Users", "Topic"])
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tree.header().sectionClicked.connect(self.sort_by_users)

        layout.addWidget(self.tree)

        # Scrollbar
        self.scrollbar = QScrollBar(Qt.Orientation.Vertical)
        self.tree.setVerticalScrollBar(self.scrollbar)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setStyleSheet(f"""
            QScrollBar:vertical {{
                border: none;
                background: {self.gui.scrollbar_bg };
                width: 12px;
                margin: 0px 0px 0px 0px;
            }}

            QScrollBar::handle:vertical {{
                background: white;
                min-height: 20px;
                border-radius: 5px;
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                background: none;
                border: none;
            }}

        """)

    def show_context_menu(self, position):
            item = self.tree.itemAt(position)
            if not item:
                return

            channel_name = item.text(0)
            menu = QMenu(self)
            join_action = menu.addAction(f"Join {channel_name}")
            action = menu.exec(self.tree.viewport().mapToGlobal(position))

            if action == join_action:
                self.gui.irc_client.loop.create_task(self.gui.irc_client.command_parser(f'/join {channel_name}'))

    def sort_by_users(self):
        # Toggle sorting order
        self.sort_order = "descending" if self.sort_order == "ascending" else "ascending"

        channels = []
        for index in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(index)
            channels.append((item.text(0), int(item.text(1)), item.text(2)))

        # Sort channels based on user count
        channels.sort(key=lambda x: x[1], reverse=(self.sort_order == "descending"))

        # Clear and repopulate
        self.tree.clear()
        for channel in channels:
            QTreeWidgetItem(self.tree, [channel[0], str(channel[1]), channel[2]])

    def update_ui_periodically(self):
        if self.is_destroyed:
            self.timer.stop()

    async def populate_channel_list(self):
        processed_channel_names = set()

        while not self.is_destroyed:
            for channel, info in self.gui.download_channel_list.items():
                if channel not in processed_channel_names:
                    QTreeWidgetItem(self.tree, [channel, str(info['user_count']), info['topic']])
                    processed_channel_names.add(channel)

            await asyncio.sleep(0.1)

    def handle_search(self):
        search_text = self.search_entry.text().lower()
        self.tree.clear()

        channels = [
            (channel, info['user_count'], info['topic'])
            for channel, info in self.gui.download_channel_list.items()
            if search_text in channel.lower() or search_text in info['topic'].lower()
        ]

        # Sort before populating
        channels.sort(key=lambda x: x[1], reverse=(self.sort_order == "descending"))
        for channel in channels:
            QTreeWidgetItem(self.tree, [channel[0], str(channel[1]), channel[2]])

    async def update_channel_info(self, channel_name, user_count, topic):
        QTreeWidgetItem(self.tree, [channel_name, str(user_count), topic])

    def closeEvent(self, event):
        self.is_destroyed = True
        event.accept()
