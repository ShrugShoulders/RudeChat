#!/usr/bin/env python3
"""Friend (watch) list that is saved per server to ``<server>_friend_list.txt`` in the config folder.

    The ``/watch`` command and the user list use this to flag friends who
    are online. Each server's client has its own RudeFriends and its own file.
"""
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

class RudeFriends:
    """Holds one server's friend list and the subset of friends currently online.

        Attributes:
            friend_list: Nicknames to watch for on this server.
            online_friends: Friends seen online during this session on this server.
            server_name: The server this list belongs to. Set by ``use_server``.
    """
    def __init__(self):
        """Create empty lists. Call ``use_server`` to pick the file and load it."""
        self.friend_list = []
        self.online_friends = []
        self.server_name = None

    def _file_path(self):
        return os.path.join(G_CONFIG_DIR, f'{self.server_name}_friend_list.txt')

    def use_server(self, server_name):
        """Point this list at a server's file and load it."""
        self.server_name = server_name
        self.load_friend_list()

    def save_friend_list(self):
        """
        Save Friend list!
        """
        if not self.server_name:
            return

        # Write to a temp file and swap it in, so a crash never leaves a half-written list.
        file_path = self._file_path()
        tmp_path = file_path + ".tmp"
        with open(tmp_path, "w", encoding='utf-8') as f:
            for user in self.friend_list:
                f.write(f"{user}\n")
        os.replace(tmp_path, file_path)

    def load_friend_list(self):
        """
        Load Friend list!

        A server with no file yet starts from the old shared ``friend_list.txt``
        if there is one, so lists made before per-server files aren't lost.
        """
        file_path = self._file_path()
        legacy_path = os.path.join(G_CONFIG_DIR, 'friend_list.txt')

        source = file_path if os.path.exists(file_path) else legacy_path
        if os.path.exists(source):
            with open(source, "r", encoding='utf-8') as f:
                self.friend_list = [line.strip() for line in f if line.strip()]
        else:
            self.friend_list = []

        if not os.path.exists(file_path):
            self.save_friend_list()

    def add_friend(self, friend):
        """
        Add a friend!
        """
        if friend not in self.friend_list:
            self.friend_list.append(friend)
            self.save_friend_list()
            return f"Added {friend} to watch list."
        else:
            return "Already in watch list."

    def remove_friend(self, enemy):
        """
        Remove Friend :(
        """
        if enemy in self.friend_list:
            self.friend_list.remove(enemy)
            self.save_friend_list()
            return f"Removed {enemy} from watch list."
        else:
            return "Not found in watch list."

    def show_friend_list(self):
        """
        Show Friends!
        """
        if not self.friend_list:
            return "No users in the watch list."

        return "Friends: " + ", ".join(self.friend_list)

    def friend_online(self, channel, username):
        """
        Friend is online!
        """
        if username in self.friend_list:
            return f"{channel}: {username} is Online!"
        else:
            return