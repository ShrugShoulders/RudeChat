import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import os

class ServerConfigWindow:
    def __init__(self, parent, config_file, close_callback):
        self.parent = parent
        self.config_file = config_file
        self.close_callback = close_callback
        self.script_directory = os.path.dirname(os.path.abspath(__file__))

        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        self.label_map = {
            'server_name': 'Server Name',
            'nickname': 'Nickname',
            'server': 'Server Address',
            'auto_join_channels': 'Auto-Join Channels?',
            'use_nickserv_auth': 'Use NickServ Authentication',
            'nickserv_password': 'NickServ Password',
            'port': 'Port',
            'ssl_enabled': 'SSL Enabled',
            'sasl_enabled': 'SASL Enabled',
            'sasl_username': 'SASL Username',
            'sasl_password': 'SASL Password',
            'use_time_stamp': 'Use Time Stamps?',
            'show_hostmask': 'Show Hostmasks?',
            'show_join_part_quit_nick': 'Show Join/Part/Quit Messages?',
            'use_beep_noise': 'Use Beep Noises?',
            'auto_whois': 'Auto WHOIS Users?',
            'custom_sounds': 'Custom Sounds',
            'mention_note_color': 'Mention Channel Highlight',
            'activity_note_color': 'Activity Channel Highlight',
            'use_logging': 'Turn Logging On/Off',
            'znc_connection': 'Use ZNC Connection',
            'znc_password': 'ZNC Password',
            'ignore_cert': 'Ignore SSL Certs?',
            'znc_user': 'ZNC Username',
            'replace_pronouns': 'Replace Pronouns?',
            'display_user_modes': 'Display User Modes?',
            'use_auto_join': 'Use Auto Join?',
            'auto_rejoin': 'Auto Rejoin on Kick?',
            'use_irc_colors': 'Enable/Disable IRC Colors',
            'send_ctcp_response': 'Respond to CTCP Requests?',
            'green_text': 'Green Text Styling',
            'auto_away_minutes': 'Time Until Auto Away',
            'use_auto_away': 'Use Auto Away?',
            'auto_join_invite': 'Auto Join On Invite?',
            'log_on': 'Turn Client Debug Logging On',
        }

        self.read_config()
        self.create_widgets()

    def read_config(self):
        config_file = os.path.join(self.script_directory, 'gui_config.ini')

        if os.path.exists(config_file):
            color_config = configparser.ConfigParser()
            color_config.read(config_file)

            self.bg_color = color_config.get('GUI', 'master_color', fallback='black')
            self.fg_color = color_config.get('GUI', 'main_fg_color', fallback='#C0FFEE')
            self.entry_bg_color = color_config.get('GUI', 'master_color', fallback='black')
            self.entry_fg_color = color_config.get('GUI', 'main_fg_color', fallback='#C0FFEE')
            self.frame_bg_color = color_config.get('GUI', 'master_color', fallback='black')
            self.parent.configure(bg=self.bg_color)

    def create_widgets(self):
        # Clear existing widgets if they exist
        if hasattr(self, 'scrollable_frame') and self.scrollable_frame.winfo_exists():
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
        else:
            # Create the canvas and scrollbar
            self.canvas = tk.Canvas(self.parent, bg=self.bg_color)
            self.scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=self.canvas.yview)
            self.scrollable_frame = tk.Frame(self.canvas, bg=self.frame_bg_color)

            # Configure the canvas and scrollbar
            self.scrollable_frame.bind(
                "<Configure>",
                lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            )

            # Create a window on the canvas for the scrollable frame
            self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
            self.canvas.configure(yscrollcommand=self.scrollbar.set)

            # Pack the canvas and scrollbar
            self.canvas.pack(side="left", fill="both", expand=True)
            self.scrollbar.pack(side="right", fill="y")

        # Add widgets to the scrollable frame
        self.entries = {}
        self.create_config_widgets()

        # Set the window size
        self.parent.geometry("600x400")  # Set the window size to 600x400

    def create_config_widgets(self):
        for section in self.config.sections():
            section_frame = tk.LabelFrame(self.scrollable_frame, text=section, bg=self.frame_bg_color, fg=self.fg_color)
            section_frame.pack(padx=10, pady=5, fill='both', expand=True)

            for option in self.config.options(section):
                label_text = self.label_map.get(option, option)
                label = tk.Label(section_frame, text=label_text, bg=self.frame_bg_color, fg=self.fg_color)
                label.grid(row=len(self.entries), column=0, padx=5, pady=2, sticky='e')

                entry = tk.Entry(section_frame, bg=self.entry_bg_color, fg=self.entry_fg_color)
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
