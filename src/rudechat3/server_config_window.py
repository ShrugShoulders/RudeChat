from rudechat3.shared_imports import *
from rudechat3.global_variables import *
from rudechat3.channel_expand import ChannelExp
from rudechat3.rude_logger import configure_logging

class ServerConfigWindow:
    def __init__(self, parent, config_file, close_callback):
        self.parent = parent
        self.config_file = config_file
        self.close_callback = close_callback
        self.frame = QScrollArea()
        self.frame.setViewportMargins(-10, -10, -10, -10)
        self.frame.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.frame.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.frame.setWidgetResizable(True)
        self.frame.setFrameShape(QFrame.Shape.NoFrame)
        self.widget = QWidget()
        self.widget.layout = QVBoxLayout(self.widget)
        self.frame.setWidget(self.widget)

        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        self.label_map = {
            'server_name': ['Server Name', 'string'],
            'nickname': ['Nickname', 'string'],
            'server': ['Server Address', 'string'],
            'auto_join_channels': ['Auto-Join Channels', 'string'],
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

    def create_widgets(self):
        self.entries = {}
        self.create_config_widgets()

    def create_config_widgets(self):
        row_count = 0  # Track row number for grid positioning

        for section in self.config.sections():
            section_frame = QGroupBox()
            
            section_frame.layout = QGridLayout(section_frame)
            section_frame.layout.setColumnStretch(0, 1)
            section_frame.layout.setColumnStretch(1, 1)

            for option in self.config.options(section):
                label = QLabel(section_frame, text=self.label_map.get(option, option)[0])
                label.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred))
                
                label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

                section_frame.layout.addWidget(label, row_count, 0, 1, 1)

                match self.label_map.get(option, option)[1]:
                    case 'bool':
                        entry = QCheckBox(section_frame)
                        entry.setChecked(self.config.getboolean(section, option))
                        
                    case 'string':
                        entry = QLineEdit(section_frame)
                        entry.setText(self.config.get(section, option))
                        
                    case 'button':
                        button = QPushButton(section_frame, text="Edit Channels")
                        button.clicked.connect(self.expand_channels_list)
                        entry = button
                    
                section_frame.layout.addWidget(entry, row_count, 1, 1, 1)

                self.entries[(section, option)] = entry
                row_count += 1
            try:
                self.widget.layout.itemAt(0).widget().setParent(None)
            except:
                print("No widget to remove")

            self.widget.layout.addWidget(section_frame)
            

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
                        value = str(entry.isChecked())
                    case 'string':
                        value = entry.text()
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