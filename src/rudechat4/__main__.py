#!/usr/bin/env python
"""
GPL-3.0 License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

# Import Config Copy Function
from rudechat4.copy_configs import CopyConfigs
# Import First Run Configs
from rudechat4.rude_first_run import FirstRun
# Import GUI
# from rudechat4.rude_gui import RudeGui
from rudechat4.rude_gui import RudeGui
# Import Client
from rudechat4.rude_client import RudeChatClient
# Import Initializer
from rudechat4.init_clients import initialize_clients
# Everything else.
from rudechat4.shared_imports import *
# Global variables
from rudechat4.global_variables import *

if platform.system() == "Darwin":
    from objc import lookUpClass

def clear_chat_window(): pass 
def reload_macros(): pass 

def open_color_selector(): pass 
def save_nickname_colors(): pass 
def reset_nick_colors(): pass 

def open_client_config_window(): pass 
def open_gui_config_window(): pass 

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self._createMenuBar()
        
    def _createMenuBar(self):
        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(True)

        if platform.system() == "Darwin":
            app_menu = menu_bar.addMenu("App")
            about_action = app_menu.addAction("About")
            about_action.triggered.connect(self.show_mac_about_panel)

        self.chat_menu = menu_bar.addMenu("Chat")
        self.chat_clear_chat_action = self.chat_menu.addAction("Clear Chat")
        self.chat_reload_macros_action = self.chat_menu.addAction("Reload Macros")

        self.colors_menu = menu_bar.addMenu("Colors")
        self.colors_color_selector_action = self.colors_menu.addAction("Color Selector")
        self.colors_save_colors_action = self.colors_menu.addAction("Save Colors")
        self.colors_reset_colors_action = self.colors_menu.addAction("Reset Colors")

        self.config_menu = menu_bar.addMenu("Config")
        self.config_edit_servers_action = self.config_menu.addAction("Edit Servers...")
        self.config_edit_gui_action = self.config_menu.addAction("Edit GUI")

    def show_mac_about_panel(self):
        NSApp = lookUpClass("NSApplication").sharedApplication()
        NSApp.orderFrontStandardAboutPanel_(None)

    def placeholder(self):
        print("Not inited yet.")

def main():
    CopyConfigs()
    app = QApplication(sys.argv)
    app.setApplicationName("RudeChat")
    app.setApplicationVersion("4.0.0")
    first_run = FirstRun(app)
    if first_run.first_run_detect == 0:
        first_run.open_client_config_window()
    
    root = Window()
    main = RudeGui(root)
    root.setCentralWidget(main)

    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)

    loop = asyncio.get_event_loop()
    loop.create_task(initialize_clients(main))

    def qt_update():
        try:
            loop.stop()
            loop.run_forever()
        finally:
            loop.stop()
            QTimer.singleShot(100, qt_update)

    # root.after(100, tk_update)
    QTimer.singleShot(100, qt_update)
    root.show()
    app.exec()

if __name__ == '__main__':
    main()
