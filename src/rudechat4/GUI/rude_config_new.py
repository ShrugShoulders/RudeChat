#!/usr/bin/env python3
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

from rudechat4.Components.rude_color_option import RudeColorOption

class OptionsView(QScrollArea):
    def __init__(self, conf, map, parent):
        super().__init__(parent)
        self.conf = conf
        self.map = map

        self.setWidgetResizable(True)

        self.content = QWidget(self)
        self.content.layout = QVBoxLayout(self.content)
        self.setWidget(self.content)

        for section in self.conf.sections():
            row_count = 0
            section_frame = QGroupBox(section)

            section_frame.layout = QGridLayout(section_frame)
            section_frame.layout.setColumnStretch(0, 1)
            section_frame.layout.setColumnStretch(1, 1)

            for option in self.conf.options(section):
                label = QLabel(section_frame, text=map.get(option, option)[0])
                section_frame.layout.addWidget(label, row_count, 0, 1, 1)

                match self.map.get(option, option)[1]:
                    case 'bool':
                        entry = QCheckBox(section_frame)
                        entry.setChecked(self.conf.getboolean(section, option))

                        section_frame.layout.addWidget(entry, row_count, 1, 1, 2)

                    case 'string':
                        entry = QLineEdit(section_frame)
                        entry.setText(self.conf.get(section, option))

                        section_frame.layout.addWidget(entry, row_count, 1, 1, 2)

                    case 'int':
                        entry = QLineEdit(section_frame)
                        entry.setInputMask("99")
                        entry.setText(str(self.conf.getint(section, option)))

                        section_frame.layout.addWidget(entry, row_count, 1, 1, 2)

                    case 'color':
                        entry = RudeColorOption(section_frame)
                        entry.setText(self.conf.get(section, option))

                        section_frame.layout.addWidget(entry, row_count, 1, 1, 2)

                    case 'channels':
                        button = QPushButton(section_frame, text='Edit Channels...')
                        # button.clicked.connect(self.expand_channels_list)
                        entry = button

                        section_frame.layout.addWidget(entry, row_count, 1, 1, 2)

                    case 'select':
                        entry = QComboBox(section_frame)
                        for choice in self.map.get(option, option)[2]:
                            entry.addItem(choice)
                        
                        section_frame.layout.addWidget(entry, row_count, 1, 1, 2)

                row_count += 1
            
            self.content.layout.addWidget(section_frame)

class RudeNewConfig(QWidget):
    def __init__(self, close_callback):
        super().__init__()
        self.close_callback = close_callback

        # Base Layout Setup
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 15, 10, 10)
        self.layout.setSpacing(5)
        self.resize(600, 500)
        self.setWindowTitle("Configure RudeChat")

        # Let's tab it up! Each tab will hold all of its own variables and logic. 
        self.tabs  = QTabWidget(self)

        # Connections Tab
        self.tabConnLogic()

        # Appearance Tab
        self.tabLookLogic()

        # Behaviour Tab
        self.tabBehvLogic()

        # About Tab
        self.tabInfoLogic()

        # Add the tabs to the base layout
        self.layout.addWidget(self.tabs)

    def tabConnLogic(self):
        # Basic layout
        self.conn = QWidget()
        self.conn.layout = QGridLayout(self.conn)
        self.conn.layout.setContentsMargins(5, 5, 5, 5)
        self.conn.layout.setSpacing(5)
        
        # Add this tab.
        self.tabs.addTab(self.conn, "Connections")

        # List of rudeserver files. Each file will be represented by its name in the config.
        self.conn.connectionsList = QListWidget(self.conn)
        self.conn.connectionsList.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.conn.connectionsList.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        self.conn.layout.addWidget(self.conn.connectionsList, 0, 0, 1, 1)

        # New, Delete and Save buttons for profile management. Inspired by iTerm2.
        self.conn.btnNew = QPushButton("New", self.conn)
        self.conn.layout.addWidget(self.conn.btnNew, 1, 0, 1, 1)

        self.conn.btnDel = QPushButton("Delete", self.conn)
        self.conn.layout.addWidget(self.conn.btnDel, 2, 0, 1, 1)

        self.conn.btnSav = QPushButton("Save", self.conn)
        self.conn.layout.addWidget(self.conn.btnSav, 3, 0, 1, 1)

        # Let's populate the settings, using test_rudeserver.ini as a base.
        self.conn.entries = {}
        self.conn.parser = configparser.ConfigParser()
        config = """
            [General]
            conn_name = Libera
            conn_addr = irc.libera.chat
            conn_port = 6697
            conn_nick = Rude
            conn_auth = 0
            conn_ssl = True
            conn_cert = False
            conn_chans = #rudechat,##
            conn_enabled = True

            [NickServ]
            nickserv_password = password

            [SASL]
            sasl_username = username
            sasl_password = password

            [ZNC]
            znc_username = username
            znc_password = password
        """

        map = {
            'conn_name': ['Connection Name', 'string'],
            'conn_addr': ['Address', 'string'],
            'conn_port': ['Port Number', 'int'],
            'conn_nick': ['Nickname', 'string'],
            'conn_auth': ['Authorisation', 'select', [ 'NickServ', 'SASL', 'ZNC' ]],
            'conn_ssl': ['Use SSL', 'bool'],
            'conn_cert': ['Require Cert', 'bool'],
            'conn_chans': ['Auto-Join Channels', 'channels'],
            'conn_enabled': ['Use Connection', 'bool'],

            'nickserv_password': ['Password', 'string'],

            'sasl_username': ['Username', 'string'],
            'sasl_password': ['Password', 'string'],

            'znc_username': ['Username', 'string'],
            'znc_password': ['Password', 'string']
        }

        self.conn.parser.read_string(config)

        self.conn.settings = OptionsView(self.conn.parser, map, self.conn)
        self.conn.layout.addWidget(self.conn.settings, 0, 1, 4, 1)

    def tabLookLogic(self):
        # Basic Layout
        self.look = QWidget()
        self.look.layout = QVBoxLayout(self.look)
        self.look.layout.setContentsMargins(5, 5, 5, 5)
        self.look.layout.setSpacing(5)
        
        # Add this tab.
        self.tabs.addTab(self.look, "Appearance")

        # Let's populate the settings, using test_rudeserver.ini as a base.
        self.look.entries = {}
        self.look.parser = configparser.ConfigParser()
        
        config = """
            [Chat]
            window_bg = #1b1e20
            window_fg = #C0FFEE
            window_font_family = Courier
            window_font_size = 12
            chat_bg = #1b1e20
            chat_fg = #C0FFEE
            chat_font_family = Courier
            chat_font_size = 12

            [Entry]
            entry_bg = #2a2e32
            entry_fg = #C0FFEE
            entry_selected_bg = #C0FFEE
            entry_font_family = Courier
            entry_font_size = 12

            [Lists]
            list_bg = #1b1e20
            list_font_family = Courier
            list_font_size = 12
            list_channel_current_bg = #2986cc
            list_channel_needwho_fg = #a4a4a4
            list_channel_unread_bg = #008000
            list_channel_mention_bg = #ff0000
            list_server_fg = #C0FFEE
            list_channel_fg = #C0FFEE
            list_user_fg = #C0FFEE
            list_user_away_fg = #4c6c3b

            [Utility]
            main_nickname_color = #39ff14
            generate_nickname_colors = True
            scrollbar_bg = #2a2e32
            url_color = #3d85c6
            green_text = False
            use_irc_colors = True
            show_join_part_quit_nick = True
        """

        map = {
            'window_bg': ['Window BG Color', 'color'],
            'window_fg': ['Window FG Color', 'color'],
            'window_font_family': ['Window Font Family', 'string'],
            'window_font_size': ['Window Font Size', 'int'],
            'chat_bg': ['Chat BG Color', 'color'],
            'chat_fg': ['Chat FG Color', 'color'],
            'chat_font_family': ['Chat Font Family', 'string'],
            'chat_font_size': ['Chat Font Size', 'int'],

            'entry_bg': ['Entry BG Color', 'color'],
            'entry_fg': ['Entry FG Color', 'color'],
            'entry_selected_bg': ['Entry Selection Color', 'color'],
            'entry_font_family': ['Entry Font Family', 'string'],
            'entry_font_size': ['Entry Font Size', 'int'],

            'list_bg': ['List BG Color', 'color'],
            'list_font_family': ['List Font Family', 'string'],
            'list_font_size': ['List Font Size', 'int'],
            'list_channel_current_bg': ['Current Channel BG Color', 'color'],
            'list_channel_needwho_fg': ['Pending Channels FG Color', 'color'],
            'list_channel_unread_bg': ['Unread Channel BG Color', 'color'],
            'list_channel_mention_bg': ['Pinged Channel BG Color', 'color'],
            'list_server_fg': ['Server FG Color', 'color'],
            'list_channel_fg': ['Channel FG Color', 'color'],
            'list_user_fg': ['User FG Color', 'color'],
            'list_user_away_fg': ['Away User FG Color', 'color'],

            'main_nickname_color': ['My Nickname Color', 'color'],
            'generate_nickname_colors': ['Generate Nickname Colors', 'bool'],
            'scrollbar_bg': ['Scrollbar Color', 'color'],
            'url_color': ['Hyperlinks Color', 'color'],
            'green_text': ['Use Green Text', 'bool'],
            'use_irc_colors': ['Use IRC Colors', 'bool'],
            'show_join_part_quit_nick': ['Show Join/Part/Quit Messages', 'bool'],
        }

        self.look.parser.read_string(config)

        self.look.settings = OptionsView(self.look.parser, map, self.look)

        self.look.layout.addWidget(self.look.settings)

        self.look.btnSav = QPushButton("Save Changes", self.look.settings)

        self.look.layout.addWidget(self.look.btnSav)

    def tabBehvLogic(self):
        # Basic Layout
        self.behv = QWidget()
        self.behv.layout = QVBoxLayout(self.behv)
        self.behv.layout.setContentsMargins(5, 5, 5, 5)
        self.behv.layout.setSpacing(5)
        
        # Add this tab.
        self.tabs.addTab(self.behv, "Behaviour")

        # Let's populate the settings, using test_rudeserver.ini as a base.
        self.behv.entries = {}
        self.behv.parser = configparser.ConfigParser()
        
        config = """
            [Presence]
            auto_rejoin = True
            auto_away_minutes = 30
            auto_join_invite = True

            [Conversation]
            replace_pronouns = False
            use_emojis = True
            tab_complete_terminator = :

            [Visibility]
            show_hostmask = True
            use_time_stamp = True
            minimize_to_tray = True

            [Sounds]
            use_beep_noise = True
            custom_sounds = False

            [Misc/Unknown]
            display_user_modes = True
            send_ctcp_response = True
            auto_whois = False
            auto_connect_to_networks = True

            [Debugging]
            logging = False
        """

        map = {
            'auto_rejoin': ['Auto Rejoin', 'bool'],
            'auto_away_minutes': ['Time until Auto Away', 'int'],
            'auto_join_invite': ['Auto-Accept Channel Invites', 'bool'],

            'replace_pronouns': ['Make Pronouns Neutral', 'bool'],
            'use_emojis': ['Convert Text to Emoji', 'bool'],
            'tab_complete_terminator': ['Tab Autocomplete Terminator', 'string'],

            'show_hostmask': ['Show Hostmask', 'bool'],
            'use_time_stamp': ['Use Timestamps', 'bool'],
            'minimize_to_tray': ['Minimize to Tray', 'bool'],

            'use_beep_noise': ['Play Notification Sounds', 'bool'],
            'custom_sounds': ['Use Custom Sounds', 'bool'],

            'display_user_modes': ['Display Usermodes', 'bool'],
            'send_ctcp_response': ['Send CTCP Response', 'bool'],
            'auto_whois': ['Auto Whois', 'bool'],
            'auto_connect_to_networks': ['Auto-connect to Networks', 'bool'],

            'logging': ['Logging', 'bool']
        }

        self.behv.parser.read_string(config)

        self.behv.settings = OptionsView(self.behv.parser, map, self.behv)

        self.behv.layout.addWidget(self.behv.settings)

        self.behv.btnSav = QPushButton("Save Changes", self.behv.settings)

        self.behv.layout.addWidget(self.behv.btnSav)

    def tabInfoLogic(self):
        # Basic layout
        self.info = QWidget()
        self.info.layout = QGridLayout(self.info)
        self.info.layout.setContentsMargins(5, 5, 5, 5)
        self.info.layout.setSpacing(5)
        
        # Add this tab.
        self.tabs.addTab(self.info, "About")

        self.info.heehoo = QLabel("irish is a neeeeeeerd", self.info)

        self.info.layout.addWidget(self.info.heehoo)