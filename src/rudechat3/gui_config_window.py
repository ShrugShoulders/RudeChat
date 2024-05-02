import tkinter as tk
from tkinter import ttk
import configparser

class GuiConfigWindow:
    def __init__(self, config_file):
        self.config_file = config_file
        self.root = tk.Tk()
        self.root.title("Rude GUI Configuration")
        
        # Create a notebook to organize settings into tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        # Create tabs for main GUI settings and widget settings
        self.create_settings_tab("Main GUI Settings", "GUI", [
            ("Your Nickname Color:", "main_nickname_color"),
            ("Generate Nickname Colors:", "generate_nickname_colors"),
            ("Master:", "master_color"),
            ("Font Family:", "family"),
            ("Font Size:", "size"),
            ("Main Text Foreground:", "main_fg_color"),
            ("Main Text Background:", "main_bg_color"),
            ("Console Foreground:", "server_fg"),
            ("Console Background:", "server_bg")
        ])

        self.create_settings_tab("Widget Settings", "WIDGETS", [
            ("User List Foreground:", "users_fg"),
            ("User List Background:", "users_bg"),
            ("User Label Foreground:", "user_label_fg"),
            ("User Label Background:", "user_label_bg"),
            ("Channel List Foreground:", "channels_fg"),
            ("Channel List Background:", "channels_bg"),
            ("Channel Label Foreground:", "channel_label_fg"),
            ("Channel Label Background:", "channel_label_bg"),
            ("Input Foreground:", "entry_fg"),
            ("Input Insert Background:", "entry_insertbackground"),
            ("Input Background:", "entry_bg"),
            ("Input Label Foreground:", "entry_label_fg"),
            ("Input Label Background:", "entry_label_bg"),
            ("Server List Foreground:", "server_listbox_fg"),
            ("Server List Background:", "server_listbox_bg"),
            ("Server Label Foreground:", "servers_label_fg"),
            ("Server Label Background:", "servers_label_bg"),
            ("Topic Label Foreground:", "topic_label_fg"),
            ("Topic Label Background:", "topic_label_bg"),
            ("Show Console Window:", "show_server_window"),
            ("Tab Completion:", "tab_complete_terminator")
        ])

        # Button to save changes
        ttk.Button(self.root, text="Save", command=self.save_changes).pack()
        tk.Label(self.root, text="Once you click the Save button the GUI will automatically apply the settings.", wraplength=400).pack()

    def create_settings_tab(self, tab_name, section, settings):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=tab_name)

        config = configparser.ConfigParser()
        config.read(self.config_file)

        for setting_name, config_key in settings:
            frame = tk.Frame(tab)
            frame.pack(fill="x")

            label = tk.Label(frame, text=setting_name, anchor="w", width=25)
            label.pack(side="left")

            entry = tk.Entry(frame)
            entry.insert(0, config.get(section, config_key))
            entry.pack(side="right", fill="x", expand=True)

            setattr(self, config_key, entry)

    def save_changes(self):
        new_config = configparser.ConfigParser()

        # Update the new config with the values from the entry widgets
        for child in self.notebook.winfo_children():
            for widget in child.winfo_children():
                if isinstance(widget, tk.Entry):
                    setting_name = widget.master.winfo_children()[0].cget("text")
                    config_key = setting_name.split(":")[0].strip()
                    section = "GUI" if child.winfo_name() == ".!notebook.!frame" else "WIDGETS"
                    new_config[section] = {config_key: widget.get()}

        # Write the updated config to a new file
        with open(self.config_file, 'w') as configfile:
            new_config.write(configfile)

        # Close the window after saving changes
        self.root.destroy()
