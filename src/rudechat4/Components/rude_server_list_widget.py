#!/usr/bin/env python3
"""Server list widget with a right-click menu to connect or disconnect a server."""
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

class RudeServerListWidget(QListWidget):
"""List of configured servers.

    The parent must be the ``RudeGui`` window, which is stored as ``gui``.
"""
    def __init__(self, parent=None):
    """Enable the custom context menu and keep a reference to the GUI."""
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.gui = parent

    def show_context_menu(self, pos: QPoint):
    """Show the Connect and Disconnect menu at the cursor."""
        menu = QMenu(self)

        connect_to_server = QAction("Connect", self)
        disconnect_from_server = QAction("Disconnect", self)

        connect_to_server.triggered.connect(self.server_connect)
        disconnect_from_server.triggered.connect(self.server_disconnect)

        menu.addAction(connect_to_server)
        menu.addAction(disconnect_from_server)

        menu.exec(self.mapToGlobal(pos))

    def server_connect(self):
    """Connect to the selected server by scheduling ``client_connect`` on the GUI."""
        selected_item = self.currentItem()
        if selected_item:
            server_name = selected_item.text()
            self.gui.irc_client.loop.create_task(self.gui.client_connect(server_name))

    def server_disconnect(self):
    """Disconnect the selected server by scheduling ``disconnect`` on the IRC client."""
        selected_item = self.currentItem()
        if selected_item:
            server_name = selected_item.text()
            self.gui.irc_client.loop.create_task(self.gui.irc_client.disconnect(server_name))
