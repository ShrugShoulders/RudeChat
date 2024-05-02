import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import os

class ServerConfigWindow:
    def __init__(self, parent, config_file, close_callback):
        self.parent = parent
        self.config_file = config_file
        self.close_callback = close_callback

        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        self.label_map = {
            'server_name': 'Server Name',
            'nickname': 'Nickname',
            'server': 'Server Address',
            'auto_join_channels': 'Auto-Join Channels',
            'use_nickserv_auth': 'Use NickServ Authentication',
            'nickserv_password': 'NickServ Password',
            'port': 'Port',
            'ssl_enabled': 'SSL Enabled',
            'sasl_enabled': 'SASL Enabled',
            'sasl_username': 'SASL Username',
            'sasl_password': 'SASL Password',
            'use_time_stamp': 'Use Time Stamp',
            'show_hostmask': 'Show Hostmask',
            'show_join_part_quit_nick': 'Show Join/Part/Quit Messages',
            'use_beep_noise': 'Use Beep Noise',
            'auto_whois': 'Auto WHOIS',
            'custom_sounds': 'Custom Sounds',
        }

        self.create_widgets()

    def create_widgets(self):
        if hasattr(self, 'main_frame') and self.main_frame.winfo_exists():
            # Update existing widgets
            for (section, option), entry in self.entries.items():
                value = self.config.get(section, option)
                entry.delete(0, tk.END)
                entry.insert(0, value)
        else:
            # Create new widgets
            self.main_frame = ttk.Frame(self.parent)
            self.main_frame.pack(fill='both', expand=True)

            self.entries = {}

            for section in self.config.sections():
                section_frame = ttk.LabelFrame(self.main_frame, text=section)
                section_frame.pack(padx=10, pady=5, fill='both', expand=True)

                for option in self.config.options(section):
                    label_text = self.label_map.get(option, option)
                    label = ttk.Label(section_frame, text=label_text)
                    label.grid(row=len(self.entries), column=0, padx=5, pady=2, sticky='e')

                    entry = ttk.Entry(section_frame)
                    entry.insert(0, self.config.get(section, option))
                    entry.grid(row=len(self.entries), column=1, padx=5, pady=2, sticky='w')

                    self.entries[(section, option)] = entry

    def save_config(self):
        try:
            # Create a new configuration object
            new_config = configparser.ConfigParser()

            for (section, option), entry in self.entries.items():
                value = entry.get()
                # Add the entry to the new configuration
                if not new_config.has_section(section):
                    new_config.add_section(section)
                new_config.set(section, option, value)

            # Extract server name from the entries
            server_name = new_config.get('IRC', 'server_name')

            # Determine the script directory
            script_directory = os.path.dirname(os.path.abspath(__file__))

            # Generate new configuration file path in the script directory using server_name
            new_config_file = os.path.join(script_directory, f"conf.{server_name.lower()}.rude")

            with open(new_config_file, 'w') as configfile:
                new_config.write(configfile)

            self.close_callback()
        except configparser.NoOptionError as e:
            messagebox.showerror("Error", f"Error saving configuration: Option '{e.option}' not found in section '{e.section}'.")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving configuration: {e}")
