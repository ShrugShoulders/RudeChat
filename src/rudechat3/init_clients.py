from .shared_imports import *

async def initialize_clients(app):
    MAX_RETRIES = 5  # Max number of times to retry on semaphore error
    RETRY_DELAY = 5  # Time in seconds to wait before retrying
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
            print(f"An unexpected OS error occurred: {str(e)}")
        except Exception as e:
            print(f"Failed to connect to Server_{i+1} due to {e}. Proceeding to the next server.")

    # Update the Listbox with the new list of servers
    if app.server_listbox.size() > 0:
        first_server = app.server_listbox.get(0)
        app.server_var.set(first_server)
        app.on_server_change(None)