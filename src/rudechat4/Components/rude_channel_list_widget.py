#!/usr/bin/env python3
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

class RudeChannelListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.gui = parent

    def show_context_menu(self, pos: QPoint):
        """Displays channel list context menu"""
        menu = QMenu(self)
        selected_item = self.currentItem()
        
        if not selected_item:
            return

        if any(selected_item.text().startswith(prefix) for prefix in self.gui.irc_client.chantypes):
            remove_action = QAction("Leave Channel", self)
            remove_action.triggered.connect(lambda _, item=selected_item.text(): self.exit_channel(item))
        elif selected_item.text().startswith("!"):
            remove_action = QAction("Close Info", self)
            remove_action.triggered.connect(lambda _, item=selected_item.text(): self.exit_dm(item))
        else:
            remove_action = QAction("Close DM", self)
            remove_action.triggered.connect(lambda _, item=selected_item.text(): self.exit_dm(item))


        # Pop Out Window
        pop_out_action = QAction("Pop Out", self)
        pop_out_action.triggered.connect(lambda _, item=selected_item.text(): self.gui.open_pop_out_window(item))

        # Add actions to menu
        menu.addAction(remove_action)
        menu.addAction(pop_out_action)

        # Show menu at cursor position
        menu.exec(self.mapToGlobal(pos))

    def exit_channel(self, item):
        """Leaves a channel"""
        if not item:
            return
        channel_name = item
        reason = f"Bye!"
        self.gui.irc_client.loop.create_task(self.gui.irc_client.leave_channel(channel_name, reason))    

    def exit_dm(self, item):
        """Closes a DM from a user"""
        if not item:
            return
        self.gui.irc_client.close_dm(item)
