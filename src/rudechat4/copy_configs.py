from rudechat4.global_variables import *
from rudechat4.shared_imports import *

def CopyConfigs():
    source_file = os.path.join(G_SOURCE_DIR, 'gui_config.ini')
    destination_file = os.path.join(G_CONFIG_DIR, 'gui_config.ini')

    if not (os.path.exists(destination_file)):
        shutil.copy(source_file, destination_file)

    # Check for .rudeserver files
    rudeserver_files = [f for f in os.listdir(G_SOURCE_DIR) if f.endswith('.rudeserver')]
    existing_rudeserver_files = [f for f in os.listdir(G_CONFIG_DIR) if f.endswith('.rudeserver')]

    if not existing_rudeserver_files:
        for file in rudeserver_files:
            shutil.copy(os.path.join(G_SOURCE_DIR, file), os.path.join(G_CONFIG_DIR, file))
