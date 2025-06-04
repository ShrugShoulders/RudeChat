#!/usr/bin/env python3
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

class RudeUserListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.gui = parent

    def show_context_menu(self, pos: QPoint):
        """Displays user list context menu"""
        menu = QMenu(self)

        # Init the actions
        open_user_dm = QAction("Open DM", self)
        whois_user = QAction("whois", self)
        ignore_action = QAction("Ignore User", self)
        unignore_action = QAction("Unignore User", self)
        kick_action = QAction("Kick User", self)
        open_user_data_action = QAction("User Data", self)

        # Connect actions to methods
        open_user_dm.triggered.connect(self.open_dm_with_user)
        whois_user.triggered.connect(self.whois_the_user)
        ignore_action.triggered.connect(self.ignore_user)
        unignore_action.triggered.connect(self.unignore_user)
        kick_action.triggered.connect(self.kick_user_from_channel)
        open_user_data_action.triggered.connect(self.open_user_data_window)

        # Add meu actions
        menu.addAction(open_user_dm)
        menu.addAction(whois_user)
        menu.addAction(ignore_action)
        menu.addAction(unignore_action)
        menu.addAction(kick_action)
        menu.addAction(open_user_data_action)

        # Show menu at cursor position
        menu.exec(self.mapToGlobal(pos))

    def open_user_data_window(self):
        try:
            # Get the user
            selected_item = self.currentItem()
            username = selected_item.text()
            modes_to_strip = ''.join(self.gui.irc_client.mode_values)
            cleaned_nickname = username.lstrip(modes_to_strip)
            
            # Retrieve WHO data if it exists
            if cleaned_nickname in self.gui.irc_client.who_user_data:
                self.gui.open_user_info(cleaned_nickname)

        except Exception as e:
            logging.error(f"Error Showing User Data: {e}")

    def open_dm_with_user(self):
        """Removes the selected channel from the list."""
        selected_item = self.currentItem()
        if selected_item:
            self.gui.irc_client.loop.create_task(self.gui.irc_client.command_parser(f"/query {selected_item.text()}"))

    def whois_the_user(self):
        """Runs a whois command on the selected user."""
        selected_item = self.currentItem()
        if selected_item:
            modes_to_strip = ''.join(self.gui.irc_client.mode_values)
            user = selected_item.text().lstrip(modes_to_strip)
            self.gui.irc_client.whois_user_request = True
            self.gui.irc_client.loop.create_task(self.gui.irc_client.cmd_whois(user))

    def ignore_user(self):
        selected_item = self.currentItem()
        if selected_item:
            modes_to_strip = ''.join(self.gui.irc_client.mode_values)
            cleaned_nickname = selected_item.text().lstrip(modes_to_strip)
            self.gui.irc_client.loop.create_task(self.gui.irc_client.ignore_user_from_gui(cleaned_nickname))

    def unignore_user(self):
        selected_item = self.currentItem()
        if selected_item:
            modes_to_strip = ''.join(self.gui.irc_client.mode_values)
            cleaned_nickname = selected_item.text().lstrip(modes_to_strip)
            self.gui.irc_client.loop.create_task(self.gui.irc_client.unignore_user_from_gui(cleaned_nickname))

    def kick_user_from_channel(self):
        selected_item = self.currentItem()
        if selected_item:
            modes_to_strip = ''.join(self.gui.irc_client.mode_values)
            channel = self.gui.irc_client.current_channel
            selected_user = selected_item.text().lstrip(modes_to_strip)
            self.gui.irc_client.loop.create_task(self.gui.irc_client.handle_kick_command(["/kick", selected_user, channel, "Bye <3"]))
