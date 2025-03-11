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

def main():
    CopyConfigs()
    app = QApplication(sys.argv)
    first_run = FirstRun(app)
    if first_run.first_run_detect == 0:
        first_run.open_client_config_window()
    
    root = QMainWindow()
    main = RudeGui(root)

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
