#!/usr/bin/env python3
"""Startup helper that creates one IRC client per server config file."""
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

async def initialize_clients(app):
    # Construct absolute paths for *.rudeserver files
    """Start a client for every ``.rudeserver`` file in the config folder.

        Files are processed in sorted order and named ``Server_1``, ``Server_2``
        and so on as a fallback name. A failure on one server is printed and the
        next server is still tried. When at least one server was added, the first
        one is selected in the GUI.

        Args:
            app: The ``RudeGui`` instance that owns the server list and
                provides ``init_client_with_config``.
    """
    config_files = [os.path.join(G_CONFIG_DIR, f) for f in os.listdir(G_CONFIG_DIR) if f.endswith(".rudeserver")]
    config_files.sort()

    if not config_files:
        logging.error("No .rudeserver configuration files found.")
        return

    for i, config_file in enumerate(config_files):
        try:
            await app.init_client_with_config(config_file, f'Server_{i+1}')
        except OSError as e:
            logging.error(f"An unexpected OS error occurred: {str(e)}")
        except Exception as e:
            logging.error(f"Failed to connect to Server_{i+1} due to {e}. Proceeding to the next server.")

    # Update the Listbox with the new list of servers
    if app.server_selector_box.count() > 0:
        app.on_server_change(None)
