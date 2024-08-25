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

# Import First Run Configs
from rudechat3.rude_first_run import FirstRun
# Import GUI
from rudechat3.rude_gui import RudeGui
# Import Client
from rudechat3.rude_client import RudeChatClient
# Import Initializer
from rudechat3.init_clients import initialize_clients
# Everything else.
from rudechat3.shared_imports import *

def main():
    first_run = FirstRun()
    if first_run.first_run_detect == 0:
        first_run.open_client_config_window()

        root = tk.Tk()
        app = RudeGui(root)

        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)

        loop = asyncio.get_event_loop()
        loop.create_task(initialize_clients(app))
    else:
        root = tk.Tk()
        app = RudeGui(root)

        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)

        loop = asyncio.get_event_loop()
        loop.create_task(initialize_clients(app))

    def tk_update():
        try:
            loop.stop()
            loop.run_forever()
        finally:
            loop.stop()
            root.after(100, tk_update)

    root.after(100, tk_update)
    root.mainloop()

if __name__ == '__main__':
    main()
