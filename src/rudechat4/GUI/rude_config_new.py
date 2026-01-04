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
        self.look = QWidget()
        
        self.tabs.addTab(self.look, "Appearance")

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