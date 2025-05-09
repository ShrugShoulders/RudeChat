from rudechat4.shared_imports import *
from rudechat4.global_variables import *

class RudeShutdown(QWidget):
    def __init__(self, master):
        super().__init__()
        self.master = master

        self.read_config()

        self.init_layout()
    
    def read_config(self): 
        config_file = os.path.join(G_CONFIG_DIR, 'gui_config.ini')

        if os.path.exists(config_file):
            config = configparser.ConfigParser()
            config.read(config_file)

            self.window_bg = config.get('Chat', 'window_bg', fallback='#1b1e20')
            self.window_fg = config.get('Chat', 'window_fg', fallback='#C0FFEE')

    def center(self):
        screen = QGuiApplication.primaryScreen().geometry()

        width = (screen.width() / 2) - 100
        height = (screen.height() / 2) - 75

        self.master.move(int(width), int(height))

    def init_layout(self):
        shutdown_messages = ["Closing RudeChat...", "Shutting Down...", "Goodbye <3...", "Exiting RudeChat...", "Hang on to your butts...", "racko says hi!", "All fear Irish!", "Sleep well...!", "please hire racko :("]
        chosen_message = random.choice(shutdown_messages)
        layout = QVBoxLayout()

        self.label = QLabel(chosen_message)
        layout.addWidget(self.label)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

        self.master.resize(200, 100)
        self.center()

        # Ensure the shutdown window is focused and on top
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.CustomizeWindowHint)
        self.setFocus()
        self.raise_()
        self.activateWindow()
