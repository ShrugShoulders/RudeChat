#!/usr/bin/env python3
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

from rudechat4.Components.rude_color_option import RudeColorOption

class OptionsView(QScrollArea):
    def __init__(self, conf, map, parent):
        """
        Modular reusable widget for allowing the user to change settings. Automatically creates groups based on sections, and uses a map to replace configuration keys with human readable labels and typing.
        
        :param conf: Dictionary object of configuration sections, settings and their values.
        :type conf: dict[str, any]
        :param map: Dictionary object of human-readable labels and types for each setting.
        :type map: dict[str, any]
        :param parent: Parent widget.
        :type parent: QWidget
        """
        super().__init__(parent)
        self.conf = conf
        self.map = map


        self.content = QWidget(self)
        self.content.layout = QVBoxLayout(self.content)
        self.setWidgetResizable(True)
        self.setWidget(self.content)

        # Create a QGroupBox for every section in the JSON file.
        for section in self.conf:
            row_count = 0
            section_frame = QGroupBox(section)

            section_frame.layout = QGridLayout(section_frame)
            section_frame.layout.setColumnStretch(0, 1)
            section_frame.layout.setColumnStretch(1, 1)

            # Loop over every key-value pair.
            for option in self.conf.get(section):
                label = QLabel(section_frame, text=self.map.get(option, option)[0])
                section_frame.layout.addWidget(label, row_count, 0, 1, 1)

                # Switch case for the different types of options.
                match self.map.get(option, option)[1]:
                    case 'bool':
                        entry = QCheckBox(section_frame)
                        entry.setChecked(self.conf.get(section)[option])

                        section_frame.layout.addWidget(entry, row_count, 1, 1, 2)

                    case 'string':
                        entry = QLineEdit(section_frame)
                        entry.setText(self.conf.get(section)[option])

                        section_frame.layout.addWidget(entry, row_count, 1, 1, 2)

                    case 'int':
                        entry = QLineEdit(section_frame)
                        entry.setValidator(QIntValidator(0, 65536, entry))
                        entry.setText(str(self.conf.get(section)[option]))

                        section_frame.layout.addWidget(entry, row_count, 1, 1, 2)

                    case 'color':
                        entry = RudeColorOption(section_frame)
                        entry.setText(self.conf.get(section)[option])

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
                            entry.setCurrentText(self.conf.get(section)[option])
                        
                        section_frame.layout.addWidget(entry, row_count, 1, 1, 2)

                row_count += 1
            
            self.content.layout.addWidget(section_frame)

class RudeNewConfig(QWidget):
    def __init__(self, close_callback):
        """
        New and improved RudeChat Config Menu! Now with more weed for RC4.20!
        
        :param close_callback: Function to call when the window is closed. TBD.
        """
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

        self.path = G_CONFIG_DIR + "/rude.json"
        self.config = {}
        self.loadConf()

        self.map = {
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
            'znc_password': ['Password', 'string'],


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

    def loadConf(self):
        """
        Loads the current rude.json file.
        """
        with open(self.path) as f:
            self.config = json.load(f)

    def saveConf(self):
        """
        Updates rude.json with the new config.
        """
        with open(self.path, "w") as f:
            json.dump(self.config, f, indent=4)

    def tabConnLogic(self):
        """
        Logic for the Connections Tab. This is where server connections are managed and configured.
        """
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

        # Loop over every server (section) in the Connections section.
        for server in self.config['Connections'].items():
            self.conn.connectionsList.addItem(server[0])

        self.conn.connectionsList.setCurrentRow(0)
        self.conn.connectionsList.currentItemChanged.connect(self.reloadServerConf)

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

        self.reloadServerConf()

    def reloadServerConf(self):
        """
        Replace the Connections OptionsView with a new one for the currently selected server - or make it for the first time.
        """
        self.conn.currentConn = self.conn.connectionsList.currentItem().text()
        
        try:
            self.conn.settings.setParent(None)
        except:
            print("No settings to replace.")

        self.conn.settings = OptionsView(self.config['Connections'][self.conn.currentConn], self.map, self.conn)

        self.conn.layout.addWidget(self.conn.settings, 0, 1, 4, 1)

    def tabLookLogic(self):
        """
        Logic for the Appearance Tab. This is where colours and such are configured.
        """
        # Basic Layout
        self.look = QWidget()
        self.look.layout = QVBoxLayout(self.look)
        self.look.layout.setContentsMargins(5, 5, 5, 5)
        self.look.layout.setSpacing(5)
        
        # Add this tab.
        self.tabs.addTab(self.look, "Appearance")

        # Let's populate the settings, using test_rudeserver.ini as a base.
        self.look.entries = {}

        self.look.settings = OptionsView(self.config['Appearance'], self.map, self.look)

        self.look.layout.addWidget(self.look.settings)

        self.look.btnSav = QPushButton("Save Changes", self.look.settings)

        self.look.layout.addWidget(self.look.btnSav)

    def tabBehvLogic(self):
        """
        Logic for the Behavior Tab. This is where various RudeChat behaviors are configured.
        """
        # Basic Layout
        self.behv = QWidget()
        self.behv.layout = QVBoxLayout(self.behv)
        self.behv.layout.setContentsMargins(5, 5, 5, 5)
        self.behv.layout.setSpacing(5)
        
        # Add this tab.
        self.tabs.addTab(self.behv, "Behaviour")

        # Let's populate the settings, using test_rudeserver.ini as a base.
        self.behv.entries = {}

        self.behv.settings = OptionsView(self.config['Behavior'], self.map, self.behv)

        self.behv.layout.addWidget(self.behv.settings)

        self.behv.btnSav = QPushButton("Save Changes", self.behv.settings)

        self.behv.layout.addWidget(self.behv.btnSav)

    def tabInfoLogic(self):
        """
        Logic for the Info Tab. This is where the truth about Irish is made public...\n
        TODO: Put version information and credits here, as well as a button that hyperlinks to the RudeChat repo maybe?
        """
        # Basic layout
        self.info = QWidget()
        self.info.layout = QGridLayout(self.info)
        self.info.layout.setContentsMargins(5, 5, 5, 5)
        self.info.layout.setSpacing(5)
        
        # Add this tab.
        self.tabs.addTab(self.info, "About")

        self.info.heehoo = QLabel("irish is a neeeeeeerd", self.info)

        self.info.layout.addWidget(self.info.heehoo)