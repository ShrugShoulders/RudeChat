import tkinter as tk
from tkinter import ttk
import configparser

class GuiConfigWindow:
    def __init__(self, config_file):
        self.config_file = config_file
        self.root = tk.Tk()
        self.root.title("Rude GUI Configuration")
        
        # Create labels and entry fields for each configuration variable
        self.create_widgets()

    def create_widgets(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)

        # Create labels and entry fields for main GUI settings
        tk.Label(self.root, text="Main GUI Settings").pack()
        self.create_setting_entry("Your Nickname Color:", config.get('GUI', 'main_nickname_color'))
        self.create_setting_entry("Generage Nickname Colors:", config.get('GUI', 'generate_nickname_colors'))
        self.create_setting_entry("Master:", config.get('GUI', 'master_color'))
        self.create_setting_entry("Font Family:", config.get('GUI', 'family'))
        self.create_setting_entry("Font Size:", config.get('GUI', 'size'))
        self.create_setting_entry("Main Text Foreground:", config.get('GUI', 'main_fg_color'))
        self.create_setting_entry("Main Text Background:", config.get('GUI', 'main_bg_color'))
        self.create_setting_entry("Console Foreground:", config.get('GUI', 'server_fg'))
        self.create_setting_entry("Console Background:", config.get('GUI', 'server_bg'))

        # Create labels and entry fields for widget settings
        tk.Label(self.root, text="Widget Settings").pack()
        self.create_setting_entry("User List Foreground:", config.get('WIDGETS', 'users_fg'))
        self.create_setting_entry("User List Background:", config.get('WIDGETS', 'users_bg'))
        self.create_setting_entry("User Label Foreground:", config.get('WIDGETS', 'user_label_fg'))
        self.create_setting_entry("User Label Background:", config.get('WIDGETS', 'user_label_bg'))
        self.create_setting_entry("Channel List Foreground:", config.get('WIDGETS', 'channels_fg'))
        self.create_setting_entry("Channel List Background:", config.get('WIDGETS', 'channels_bg'))
        self.create_setting_entry("Channel Label Foreground:", config.get('WIDGETS', 'channel_label_fg'))
        self.create_setting_entry("Channel Label Background:", config.get('WIDGETS', 'channel_label_bg'))
        self.create_setting_entry("Input Foreground:", config.get('WIDGETS', 'entry_fg'))
        self.create_setting_entry("Input Insert Background:", config.get('WIDGETS', 'entry_insertbackground'))
        self.create_setting_entry("Input Background:", config.get('WIDGETS', 'entry_bg'))
        self.create_setting_entry("Input Label Foreground:", config.get('WIDGETS', 'entry_label_fg'))
        self.create_setting_entry("Input Label Background:", config.get('WIDGETS', 'entry_label_bg'))
        self.create_setting_entry("Server List Foreground:", config.get('WIDGETS', 'server_listbox_fg'))
        self.create_setting_entry("Server List Background:", config.get('WIDGETS', 'server_listbox_bg'))
        self.create_setting_entry("Server Label Foreground:", config.get('WIDGETS', 'servers_label_fg'))
        self.create_setting_entry("Server Label Background:", config.get('WIDGETS', 'servers_label_bg'))
        self.create_setting_entry("Topic Label Foreground:", config.get('WIDGETS', 'topic_label_fg'))
        self.create_setting_entry("Topic Label Background:", config.get('WIDGETS', 'topic_label_bg'))
        self.create_setting_entry("Tab Completion:", config.get('WIDGETS', 'tab_complete_terminator'))

        # Button to save changes
        ttk.Button(self.root, text="Save", command=self.save_changes).pack()
        tk.Label(self.root, text="Once you click the Save button the GUI will automatically apply the settings.", wraplength=400).pack()

    def create_setting_entry(self, setting_name, default_value):
        frame = tk.Frame(self.root)
        frame.pack(fill="x")

        label = tk.Label(frame, text=setting_name, anchor="w")
        label.pack(side="left")

        # Calculate the appropriate width for the label based on the length of setting_name
        label_width = max(10, len(setting_name))  # Minimum width of 10 pixels
        label.config(width=label_width)

        entry = tk.Entry(frame)
        entry.insert(0, default_value)
        entry.pack(side="right", fill="x", expand=True)

        setattr(self, setting_name, entry)

    def save_changes(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)

        # Update config with new values
        config.set('GUI', 'main_nickname_color', getattr(self, "Your Nickname Color:").get())
        config.set('GUI', 'generate_nickname_colors', getattr(self, "Generage Nickname Colors:").get())
        config.set('GUI', 'master_color', getattr(self, "Master:").get())
        config.set('GUI', 'family', getattr(self, "Font Family:").get())
        config.set('GUI', 'size', getattr(self, "Font Size:").get())
        config.set('GUI', 'main_fg_color', getattr(self, "Main Text Foreground:").get())
        config.set('GUI', 'main_bg_color', getattr(self, "Main Text Background:").get())
        config.set('GUI', 'server_fg', getattr(self, "Console Foreground:").get())
        config.set('GUI', 'server_bg', getattr(self, "Console Background:").get())

        config.set('WIDGETS', 'users_fg', getattr(self, "User List Foreground:").get())
        config.set('WIDGETS', 'users_bg', getattr(self, "User List Background:").get())
        config.set('WIDGETS', 'user_label_bg', getattr(self, "User Label Background:").get())
        config.set('WIDGETS', 'user_label_fg', getattr(self, "User Label Foreground:").get())
        config.set('WIDGETS', 'channels_fg', getattr(self, "Channel List Foreground:").get())
        config.set('WIDGETS', 'channels_bg', getattr(self, "Channel List Background:").get())
        config.set('WIDGETS', 'channel_label_fg', getattr(self, "Channel Label Foreground:").get())
        config.set('WIDGETS', 'channel_label_bg', getattr(self, "Channel Label Background:").get())
        config.set('WIDGETS', 'entry_fg', getattr(self, "Input Foreground:").get())
        config.set('WIDGETS', 'entry_insertbackground', getattr(self, "Input Insert Background:").get())
        config.set('WIDGETS', 'entry_bg', getattr(self, "Input Background:").get())
        config.set('WIDGETS', 'entry_label_bg', getattr(self, "Input Label Background:").get())
        config.set('WIDGETS', 'entry_label_fg', getattr(self, "Input Label Foreground:").get())
        config.set('WIDGETS', 'server_listbox_bg', getattr(self, "Server List Background:").get())
        config.set('WIDGETS', 'server_listbox_fg', getattr(self, "Server List Foreground:").get())
        config.set('WIDGETS', 'servers_label_bg', getattr(self, "Server Label Background:").get())
        config.set('WIDGETS', 'servers_label_fg', getattr(self, "Server Label Foreground:").get())
        config.set('WIDGETS', 'topic_label_bg', getattr(self, "Topic Label Background:").get())
        config.set('WIDGETS', 'topic_label_fg', getattr(self, "Topic Label Foreground:").get())
        config.set('WIDGETS', 'tab_complete_terminator', getattr(self, "Tab Completion:").get())

        # Write the updated config back to the file
        with open(self.config_file, 'w') as configfile:
            config.write(configfile)

        # Close the window after saving changes
        self.root.destroy()
