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

# Import GUI
from .rude_gui import RudeGui
# Import Client
from .rude_client import RudeChatClient
# Import Channel List Window.
from .list_window import ChannelListWindow
# Everything else.
from .shared_imports import *

MAX_RETRIES = 5  # Max number of times to retry on semaphore error
RETRY_DELAY = 5  # Time in seconds to wait before retrying

async def initialize_clients(app):
    script_directory = os.path.dirname(os.path.abspath(__file__))

    # Construct absolute paths for conf.*.rude files
    config_files = [os.path.join(script_directory, f) for f in os.listdir(script_directory) if f.startswith("conf.") and f.endswith(".rude")]
    config_files.sort()

    if not config_files:
        print("No .rude configuration files found.")
        return

    for i, config_file in enumerate(config_files):
        try:
            await app.init_client_with_config(config_file, f'Server_{i+1}')
        except OSError as e:
            if e.winerror == 121:  # The semaphore timeout error
                retries = 0
                while retries < MAX_RETRIES:
                    retries += 1
                    print(f"Semaphore timeout error. Retrying {retries}/{MAX_RETRIES}...")
                    await asyncio.sleep(RETRY_DELAY)
                    try:
                        await app.init_client_with_config(config_file, f'Server_{i+1}')
                        break
                    except OSError as e:
                        if e.winerror != 121:
                            print(f"An unexpected error occurred: {str(e)}")
                            break
                else:
                    print("Max retries reached. Skipping this server.")
            else:
                print(f"An unexpected error occurred: {str(e)}")
        except Exception as e:
            print(f"Failed to connect to Server_{i+1} due to {e}. Proceeding to the next server.")

    # Update the Listbox with the new list of servers
    if app.server_listbox.size() > 0:
        first_server = app.server_listbox.get(0)
        app.server_var.set(first_server)
        app.on_server_change(None)

def main():
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
