import tkinter as tk
from tkinter import ttk
import configparser
import os
import logging
from rudechat3.global_variables import *
from rudechat3.channel_expand import ChannelExp
from rudechat3.rude_logger import configure_logging


class ServerConfigWindow:
    def __init__(self, parent, config_file, close_callback):
        self.parent = parent
        self.config_file = config_file
        self.close_callback = close_callback 

        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self.parent.protocol("WM_DELETE_WINDOW", self.save_config)

        self.label_map = {
            'server_name': ['Server Name', 'string'],
            'nickname': ['Nickname', 'string'],
            'server': ['Server Address', 'string'],
            'auto_join_channels': ['Auto-Join Channels', 'button'],
            'use_nickserv_auth': ['Use NickServ Authentication', 'bool'],
            'nickserv_password': ['NickServ Password', 'string'],
            'port': ['Port', 'string'],
            'ssl_enabled': ['SSL Enabled', 'bool'],
            'sasl_enabled': ['SASL Enabled', 'bool'],
            'sasl_username': ['SASL Username', 'string'],
            'sasl_password': ['SASL Password', 'string'],
            'use_time_stamp': ['Use Time Stamps?', 'bool'],
            'show_hostmask': ['Show Hostmasks?', 'bool'],
            'show_join_part_quit_nick': ['Show Join/Part/Quit Messages?', 'bool'],
            'use_beep_noise': ['Use Beep Noises?', 'bool'],
            'auto_whois': ['Auto WHOIS Users?', 'bool'],
            'custom_sounds': ['Custom Sounds', 'bool'],
            'mention_note_color': ['Mention Channel Highlight', 'string'],
            'activity_note_color': ['Activity Channel Highlight', 'string'],
            'use_logging': ['Turn Logging On/Off', 'bool'],
            'znc_connection': ['Use ZNC Connection', 'bool'],
            'znc_password': ['ZNC Password', 'string'],
            'ignore_cert': ['Ignore SSL Certs?', 'bool'],
            'znc_user': ['ZNC Username', 'string'],
            'replace_pronouns': ['Replace Pronouns?', 'bool'],
            'display_user_modes': ['Display User Modes?', 'bool'],
            'use_auto_join': ['Use Auto Join?', 'bool'],
            'auto_rejoin': ['Auto Rejoin on Kick?', 'bool'],
            'use_irc_colors': ['Enable/Disable IRC Colors', 'bool'],
            'send_ctcp_response': ['Respond to CTCP Requests?', 'bool'],
            'green_text': ['Green Text Styling', 'bool'],
            'auto_away_minutes': ['Time Until Auto Away', 'string'],
            'use_auto_away': ['Use Auto Away?', 'bool'],
            'auto_join_invite': ['Auto Join On Invite?', 'bool'],
            'log_on': ['Turn Client Debug Logging On', 'bool'],
            'use_emojis': ['Turn Emoji filters on/off', 'bool'],
        }
        configure_logging()
        self.entries = {}
        self.read_config()
        self.create_widgets()

    def read_config(self):
        config_file = os.path.join(G_CONFIG_DIR, 'gui_config.ini')

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
        # Configure parent window grid
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.parent, bg=self.bg_color)
        self.scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=self.canvas.yview)
        
        # Create a frame inside the canvas
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.frame_bg_color)
        self.scrollable_frame.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Create a window inside the canvas
        self.window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configure grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        # Attach scrollbar to canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Entries dictionary
        self.entries = {}
        self.create_config_widgets()

    def create_config_widgets(self):
        row_count = 0  # Track row number for grid positioning
        button = None

        for section in self.config.sections():
            section_frame = tk.LabelFrame(self.scrollable_frame, text=section, bg=self.frame_bg_color, fg=self.fg_color)
            section_frame.grid(row=row_count, column=0, padx=10, pady=5, sticky="ew")
            section_frame.columnconfigure(1, weight=1)  # Allow second column to expand
            section_frame.columnconfigure(2, weight=0)

            for option in self.config.options(section):
                label_text = self.label_map.get(option, option)[0]
                label = tk.Label(section_frame, text=label_text, bg=self.frame_bg_color, fg=self.fg_color)
                label.grid(row=row_count, column=0, padx=5, pady=2, sticky='e')

                match self.label_map.get(option, option)[1]:
                    case 'bool':
                        entry = ttk.Checkbutton(section_frame, onvalue=True, offvalue=False)
                        entry.state(['selected']) if self.config.getboolean(section, option) else entry.state(['!alternate'])
                        button = None
                    case 'string':
                        entry = tk.Entry(section_frame, bg=self.entry_bg_color, fg=self.entry_fg_color, insertbackground="white")
                        entry.insert(0, self.config.get(section, option))
                        button = None
                    case 'button':
                        button = tk.Button(section_frame, text="Edit Channels", command=self.expand_channels_list, bg=self.entry_bg_color, fg=self.entry_fg_color,)
                        entry = tk.Entry(section_frame, bg=self.entry_bg_color, fg=self.entry_fg_color, insertbackground="white")
                        entry.insert(0, self.config.get(section, option))

                entry.grid(row=row_count, column=1, padx=5, pady=2, sticky='w')
                if button is not None:
                    button.grid(row=row_count, column=2, padx=5, pady=2, sticky='w')

                self.entries[(section, option)] = entry
                row_count += 1

    def expand_channels_list(self):
        channels = self.config.get('IRC', 'auto_join_channels')
        if channels:
            expander = ChannelExp(self.parent, channels, self.entry_bg_color, self.entry_fg_color)
            new_list = str(expander.get_channels())
            for (section, option), entry in self.entries.items():
                if option == 'auto_join_channels':
                    entry.delete(0, tk.END)
                    entry.insert(0, new_list)

    def save_config(self):
        try:
            # Create a new configuration object
            new_config = configparser.ConfigParser()

            for (section, option), entry in self.entries.items():
                match self.label_map.get(option, option)[1]:
                    case 'bool':
                        value = 'True' if entry.instate(['selected']) else 'False'
                    case 'string':
                        value = entry.get()
                    case 'button':
                        value = entry.get()
                # Add the entry to the new configuration
                if not new_config.has_section(section):
                    new_config.add_section(section)
                new_config.set(section, option, value)

            # Extract server name from the entries
            server_name = new_config.get('IRC', 'server_name')

            # Determine the script directory
            config_directory = G_CONFIG_DIR

            # Generate new configuration file path in the script directory using server_name
            new_config_file = os.path.join(config_directory, f"{server_name.lower()}.rudeserver")

            with open(new_config_file, 'w') as configfile:
                new_config.write(configfile)

            self.close_callback()
        except configparser.NoOptionError as e:
            logging.error(f"Error saving configuration: Option '{e.option}' not found in section '{e.section}'.")
        except Exception as e:
            logging.error(f"Error saving configuration: {e}")