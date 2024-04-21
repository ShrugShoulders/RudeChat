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
        self.create_setting_entry("Master", config.get('GUI', 'master_color'))
        self.create_setting_entry("Font Family", config.get('GUI', 'family'))
        self.create_setting_entry("Font Size", config.get('GUI', 'size'))
        self.create_setting_entry("Main Text Foreground", config.get('GUI', 'main_fg_color'))
        self.create_setting_entry("Main Text Background", config.get('GUI', 'main_bg_color'))
        self.create_setting_entry("Console Foreground", config.get('GUI', 'server_fg'))
        self.create_setting_entry("Console Background", config.get('GUI', 'server_bg'))

        # Create labels and entry fields for widget settings
        tk.Label(self.root, text="Widget Settings").pack()
        self.create_setting_entry("User List Foreground", config.get('WIDGETS', 'users_fg'))
        self.create_setting_entry("User List Background", config.get('WIDGETS', 'users_bg'))
        self.create_setting_entry("Channel List Foreground", config.get('WIDGETS', 'channels_fg'))
        self.create_setting_entry("Channel List Background", config.get('WIDGETS', 'channels_bg'))
        self.create_setting_entry("Input Foreground", config.get('WIDGETS', 'entry_fg'))
        self.create_setting_entry("Input Insert Background", config.get('WIDGETS', 'entry_insertbackground'))
        self.create_setting_entry("Input Background", config.get('WIDGETS', 'entry_bg'))
        self.create_setting_entry("Input Label Foreground", config.get('WIDGETS', 'entry_label_bg'))
        self.create_setting_entry("Input Label Background", config.get('WIDGETS', 'entry_label_fg'))
        self.create_setting_entry("Server List Background", config.get('WIDGETS', 'server_listbox_bg'))
        self.create_setting_entry("Server List Foreground", config.get('WIDGETS', 'server_listbox_fg'))

        # Button to save changes
        tk.Button(self.root, text="Save", command=self.save_changes).pack()

    def create_setting_entry(self, setting_name, default_value):
        frame = tk.Frame(self.root)
        frame.pack(fill="x")
        
        label = tk.Label(frame, text=setting_name, width=20, anchor="w")
        label.pack(side="left")
        
        entry = tk.Entry(frame)
        entry.insert(0, default_value)
        entry.pack(side="right", fill="x", expand=True)
        
        setattr(self, setting_name, entry)

    def save_changes(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)

        # Update config with new values
        config['GUI']['master_color'] = self.Master.get()
        config['GUI']['family'] = self["Font Family"].get()
        config['GUI']['size'] = self["Font Size"].get()
        config['GUI']['main_fg_color'] = self["Main Text Foreground"].get()
        config['GUI']['main_bg_color'] = self["Main Text Background"].get()
        config['GUI']['server_fg'] = self["Console Foreground"].get()
        config['GUI']['server_bg'] = self["Console Background"].get()

        config['WIDGETS']['users_fg'] = self["User List Foreground"].get()
        config['WIDGETS']['users_bg'] = self["User List Background"].get()
        config['WIDGETS']['channels_fg'] = self["Channel List Foreground"].get()
        config['WIDGETS']['channels_bg'] = self["Channel List Background"].get()
        config['WIDGETS']['entry_fg'] = self["Input Foreground"].get()
        config['WIDGETS']['entry_insertbackground'] = self["Input Insert Background"].get()
        config['WIDGETS']['entry_bg'] = self["Input Background"].get()
        config['WIDGETS']['entry_label_bg'] = self["Input Label Foreground"].get()
        config['WIDGETS']['entry_label_fg'] = self["Input Label Background"].get()
        config['WIDGETS']['server_listbox_bg'] = self["Server List Background"].get()
        config['WIDGETS']['server_listbox_fg'] = self["Server List Foreground"].get()

        # Write the updated config back to the file
        with open(self.config_file, 'w') as configfile:
            config.write(configfile)

        # Close the window after saving changes
        self.root.destroy()