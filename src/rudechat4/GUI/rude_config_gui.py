#!/usr/bin/env python3

from rudechat4.shared_imports import *
from rudechat4.global_variables import *
from rudechat4.Util.rude_logger import configure_logging
from rudechat4.GUI.channel_expand import ChannelExp
from rudechat4.Components.rude_color_option import RudeColorOption

class RudeConfigGui(QScrollArea):
    def __init__(self, parent, config_file, close_callback):
        super().__init__(parent)
        self.config_file = config_file
        self.close_callback = close_callback
        self.setViewportMargins(-10, 0, -10, -10)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.widget = QWidget()
        self.widget.layout = QVBoxLayout(self.widget)
        self.setWidget(self.widget)

        self.parent().setFixedSize(450, 500)

        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        self.start()

    def start(self):
        self.label_map = {
            'window_bg' : ['Window BG Color', 'color'],
            'window_fg' : ['Window FG Color', 'color'],
            'window_font_family' : ['Window Font Family', 'string'],
            'window_font_size' : ['Window Font Size', 'int'],
            'chat_bg' : ['Chat BG Color', 'color'],
            'chat_fg' : ['Chat FG Color', 'color'],
            'chat_font_family' : ['Chat Font Family', 'string'],
            'chat_font_size' : ['Chat Font Size', 'int'],

            'entry_bg' : ['Entry BG Color', 'color'],
            'entry_fg' : ['Entry FG Color', 'color'],
            'entry_selected_bg' : ['Entry Selection Colour', 'color'],
            'entry_font_family' : ['Entry Font Family', 'string'],
            'entry_font_size' : ['Entry Font Size', 'int'],

            'list_bg' : ['List BG Color', 'color'],
            'list_font_family' : ['List Font Family', 'string'],
            'list_font_size' : ['List Font Size', 'int'],
            'list_channel_current_bg' : ['Current Channel BG Color', 'color'],
            'list_channel_needwho_fg' : ['Pending Channels FG Color', 'color'],
            'list_server_fg' : ['Server FG Color', 'color'],
            'list_channel_fg' : ['Channel FG Color', 'color'],
            'list_user_fg': ['User FG Color', 'color'],
            'list_user_away_fg' : ['Away User FG Color', 'color'],

            'main_nickname_color' : ['Nickname Color', 'color'],
            'generate_nickname_colors' : ['Generate Nickname Colors', 'bool'],
            'minimize_to_tray' : ['Minimize to Tray', 'bool'],
            'highlight_all_nicknames' : ['Highlight All Nicks', 'bool'],
            'show_server_window' : ['Show Server Window', 'bool'],
            'tab_complete_terminator' : ['Tab Autocomplete Terminator', 'string'],
            'turn_logging_on' : ['Turn On Logging', 'bool'],
            'scrollbar_bg' : ['Scrollbar Background', 'color']
        }

        configure_logging()
        self.entries = {}
        self.create_widgets()

    def create_widgets(self):
        for section in self.config.sections():
            row_count = 0  # Track row number for grid positioning
            section_frame = QGroupBox(section.title())
            
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

                        section_frame.layout.addWidget(entry, row_count, 1, 1, 2)
                        
                    case 'string':
                        entry = QLineEdit(section_frame)
                        entry.setText(self.config.get(section, option))

                        section_frame.layout.addWidget(entry, row_count, 1, 1, 2)

                    case 'int':
                        entry = QLineEdit(section_frame)
                        entry.setInputMask("99")
                        entry.setText(str(self.config.getint(section, option)))

                        section_frame.layout.addWidget(entry, row_count, 1, 1, 2)

                    case 'color':
                        entry = RudeColorOption(section_frame)
                        entry.setText(self.config.get(section, option))

                        section_frame.layout.addWidget(entry, row_count, 1, 1, 2)

                    case 'channels':
                        button = QPushButton(section_frame, text='Edit Channels...')
                        button.clicked.connect(self.expand_channels_list)
                        entry = button

                        section_frame.layout.addWidget(entry, row_count, 1, 1, 2)

                self.entries[(section, option)] = entry
                row_count += 1

            self.widget.layout.addWidget(section_frame)

    def expand_channels_list(self):
        channels = self.channels
        if channels:
            self.expander = ChannelExp(channels, self.set_channels)

            self.expander.show()

    def set_channels(self, new_channels):
        self.channels = new_channels

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
                    case 'int':
                        value = entry.text()
                    case 'color':
                        value = entry.text()
                    case 'channels':
                        value = self.channels
                # Add the entry to the new configuration
                if not new_config.has_section(section):
                    new_config.add_section(section)
                new_config.set(section, option, value)

            # Generate new configuration file path in the script directory using server_name
            new_config_file = self.config_file

            with open(new_config_file, 'w') as configfile:
                new_config.write(configfile)

            self.close_callback()
        except configparser.NoOptionError as e:
            logging.error(f"Error saving configuration: Option '{e.option}' not found in section '{e.section}'.")
        except Exception as e:
            logging.error(f"Error saving configuration: {e}")