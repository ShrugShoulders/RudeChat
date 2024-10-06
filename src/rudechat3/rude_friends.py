import os


class RudeFriends:
    def __init__(self):
        self.friend_list = []
        self.script_directory = os.path.dirname(os.path.abspath(__file__))

        self.load_friend_list()

    def save_friend_list(self):
        """
        Save Friend list!
        """
        # Construct the full path for the friend_list.txt
        file_path = os.path.join(self.script_directory, 'friend_list.txt')

        with open(file_path, "w", encoding='utf-8') as f:
            for user in self.friend_list:
                f.write(f"{user}\n")

    def load_friend_list(self):
        """
        Load Friend list!
        """
        # Construct the full path for the friend_list.txt
        file_path = os.path.join(self.script_directory, 'friend_list.txt')

        if os.path.exists(file_path):
            with open(file_path, "r", encoding='utf-8') as f:
                self.friend_list = [line.strip() for line in f.readlines()]
        else:
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