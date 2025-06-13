#!/usr/bin/env python3
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

class RudeServerListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.gui = parent

    def show_context_menu(self, pos: QPoint):
        menu = QMenu(self)

        connect_to_server = QAction("Connect", self)
        disconnect_from_server = QAction("Disconnect", self)

        connect_to_server.triggered.connect(self.server_connect)
        disconnect_from_server.triggered.connect(self.server_disconnect)

        menu.addAction(connect_to_server)
        menu.addAction(disconnect_from_server)

        menu.exec(self.mapToGlobal(pos))

    def server_connect(self):
        selected_item = self.currentItem()
        if selected_item:
            server_name = selected_item.text()
            self.gui.irc_client.loop.create_task(self.gui.client_connect(server_name))

    def server_disconnect(self):
        selected_item = self.currentItem()
        if selected_item:
            server_name = selected_item.text()
            self.gui.irc_client.loop.create_task(self.gui.irc_client.disconnect(server_name))
