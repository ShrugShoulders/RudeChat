from rudechat4.shared_imports import *
from rudechat4.global_variables import *


async def initialize_clients(app):
    config_directory = G_CONFIG_DIR

    # Construct absolute paths for *.rudeserver files
    config_files = [os.path.join(config_directory, f) for f in os.listdir(config_directory) if f.endswith(".rudeserver")]
    config_files.sort()

    if not config_files:
        print("No .rudeserver configuration files found.")
        return

    for i, config_file in enumerate(config_files):
        try:
            await app.init_client_with_config(config_file, f'Server_{i+1}')
        except OSError as e:
            print(f"An unexpected OS error occurred: {str(e)}")
        except Exception as e:
            print(f"Failed to connect to Server_{i+1} due to {e}. Proceeding to the next server.")

    # Update the Listbox with the new list of servers
    if app.serverList.count() > 0:
        first_server = app.serverList.item(0)
        app.server_var = first_server
        app.on_server_change(None)
