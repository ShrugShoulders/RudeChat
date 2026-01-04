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
        self.conn = QWidget()

        self.tabs.addTab(self.conn, "Connections")

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