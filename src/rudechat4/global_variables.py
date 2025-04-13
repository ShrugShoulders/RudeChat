from rudechat4.shared_imports import *

G_SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
G_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "rudechat")

# Create the folder if it doesn't exist
if not os.path.exists(G_CONFIG_DIR):
    os.makedirs(G_CONFIG_DIR)

match platform.system():
    case "Darwin" | "Linux":
        ICON_FILE = os.path.join(G_CONFIG_DIR, 'rude_icon_roundedge.png')
    case "Windows":
        ICON_FILE = os.path.join(G_SOURCE_DIR, 'rude.ico')
    case _:
        ICON_FILE = os.path.join(G_CONFIG_DIR, 'rude_icon_roundedge.png')
