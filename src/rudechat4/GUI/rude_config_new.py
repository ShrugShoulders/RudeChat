#!/usr/bin/env python3
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

class RudeNewConfig(QWidget):
    def __init__(self, close_callback):
        super().__init__()
        self.close_callback = close_callback

        # Base Layout Setup
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        self.resize(600, 400)
        self.setWindowTitle("Configure RudeChat")

        # Let's tab it up! Each tab will hold all of its own variables and logic. 
        self.tabs  = QTabWidget(self)

        # Connections Tab
        self.makeConnTab()

        # Appearance Tab
        self.makeLookTab()

        # Behaviour Tab
        self.behv = QWidget()

        self.tabs.addTab(self.behv, "Behaviour")

        # About Tab
        self.help = QWidget()
        
        self.tabs.addTab(self.help, "About")

        # Add the tabs to the base layout
        self.layout.addWidget(self.tabs)
        
    def makeConnTab(self):
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

        # Big field where all the settings will go.
        self.conn.settings = QScrollArea(self.conn)
        self.conn.settings.setWidgetResizable(True)

        self.conn.settings.content = QWidget(self.conn.settings)
        self.conn.settings.content.layout = QVBoxLayout(self.conn.settings.content)
        self.conn.settings.content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.conn.settings.setWidget(self.conn.settings.content)

        # Let's populate the settings, using test_rudeserver.ini as a base.
        self.conn.entries = {}
        self.conn.parser = configparser.ConfigParser()
        self.conn.parser['General'] = { # These are default values according to the test ini file. Logic should include populating these fields with the first loaded .rudeserver file.
            'conn_name': 'Libera',
            'conn_addr': 'irc.libera.chat',
            'conn_port': 6697,
            'conn_nick': 'Rude',
            'conn_auth': 0,
            'conn_ssl': True,
            'conn_cert': False,
            'conn_chans': ['#rudechat','##'],
            'conn_enabled': True
        }

        self.conn.parser['NickServ'] = { 'nickserv_password': 'password' }

        self.conn.parser['SASL'] = { 'sasl_username': 'username', 'sasl_password': 'password'}
        
        self.conn.parser['ZNC'] = { 'znc_username': 'username', 'znc_password': 'password'}

        # Create group boxes for each INI section. This just looks good, tbqh.
        for section in self.conn.parser.sections():
            row_count = 0
            section_frame = QGroupBox(section)

            section_frame.layout = QGridLayout(section_frame)
            section_frame.layout.setColumnStretch(0, 1)
            section_frame.layout.setColumnStretch(1, 1)

            for option in self.conn.parser.options(section):
                label = QLabel(section_frame, text=option)
                section_frame.layout.addWidget(label, row_count, 0, 1, 1)

                entry = QLineEdit(section_frame)
                entry.setText(self.conn.parser.get(section, option))
                section_frame.layout.addWidget(entry, row_count, 1, 1, 2)

                row_count += 1
            
            self.conn.settings.content.layout.addWidget(section_frame)

        self.conn.layout.addWidget(self.conn.settings, 0, 1, 4, 1)

    def makeLookTab(self):
        # Basic Layout
        self.look = QWidget()
        self.look.layout = QVBoxLayout(self.look)
        self.look.layout.setContentsMargins(5, 5, 5, 5)
        self.look.layout.setSpacing(5)
        
        # Add this tab.
        self.tabs.addTab(self.look, "Appearance")

        # Big field where all the settings will go.
        self.look.settings = QScrollArea(self.look)
        self.look.settings.setWidgetResizable(True)

        self.look.settings.content = QWidget(self.look.settings)
        self.look.settings.content.layout = QVBoxLayout(self.look.settings.content)
        self.look.settings.content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.look.settings.setWidget(self.look.settings.content)

        # Let's populate the settings, using test_rudeserver.ini as a base.
        self.look.entries = {}
        self.look.parser = configparser.ConfigParser()
        self.look.parser['Chat'] = { # These are default values according to the test ini file. Logic should include populating these fields with the first loaded .rudeserver file.
            'window_bg': '#1b1e20',
            'window_fg': '#C0FFEE',
            'window_font_family': 'Courier',
            'window_font_size': 12,
            'chat_bg': '#1b1e20',
            'chat_fg': '#C0FFEE',
            'chat_font_family': 'Courier',
            'chat_font_size': 12,
        }

        self.look.parser['Entry'] = {
            'entry_bg': '#2a2e32',
            'entry_fg': '#C0FFEE',
            'entry_selected_bg': '#C0FFEE',
            'entry_font_family': 'Courier',
            'entry_font_size': 12,
        }

        self.look.parser['Lists'] = {
            'list_bg': '#1b1e20',
            'list_font_family': 'Courier',
            'list_font_size': 12,
            'list_channel_current_bg': '#2986cc',
            'list_channel_needwho_fg': '#a4a4a4',
            'list_channel_unread_bg': '#008000',
            'list_channel_mention_bg': '#ff0000',
            'list_server_fg': '#C0FFEE',
            'list_channel_fg': '#C0FFEE',
            'list_user_fg': '#C0FFEE',
            'list_user_away_fg': '#4c6c3b',
        }

        self.look.parser['Utility'] = {
            'main_nickname_color': '#39ff14',
            'generate_nickname_colors': True,
            'scrollbar_bg': '#2a2e32',
            'url_color': '#3d85c6',
            'green_text': False,
            'use_irc_colors': True,
            'show_join_part_quit_nick': True,
        }

        # Create group boxes for each INI section. This just looks good, tbqh.
        for section in self.look.parser.sections():
            row_count = 0
            section_frame = QGroupBox(section)

            section_frame.layout = QGridLayout(section_frame)
            section_frame.layout.setColumnStretch(0, 1)
            section_frame.layout.setColumnStretch(1, 1)

            for option in self.look.parser.options(section):
                label = QLabel(section_frame, text=option)
                section_frame.layout.addWidget(label, row_count, 0, 1, 1)

                entry = QLineEdit(section_frame)
                entry.setText(self.look.parser.get(section, option))
                section_frame.layout.addWidget(entry, row_count, 1, 1, 2)

                row_count += 1
            
            self.look.settings.content.layout.addWidget(section_frame)

        self.look.layout.addWidget(self.look.settings)

        self.look.btnSav = QPushButton("Save Changes", self.look.settings)

        self.look.layout.addWidget(self.look.btnSav)