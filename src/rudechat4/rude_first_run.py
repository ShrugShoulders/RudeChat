from rudechat4.shared_imports import *
from rudechat4.global_variables import *
from rudechat4.server_config_window import ServerConfigWindow

class FirstRun:
    def __init__(self):
        self.first_run_detect = self.load_first_run()
        
        self.window_size = "600x400"
        self.read_config()

    def load_first_run(self):
        config_directory = G_CONFIG_DIR
        file_path = os.path.join(config_directory, "first_run.txt")
        try:
            with open(file_path, 'r') as file:
                content = file.read().strip()
                if content == '1':
                    return 1
                else:
                    return 0
        except FileNotFoundError:
            # If the file does not exist, assume it is the first run.
            return 0
        except Exception as e:
            # Handle other exceptions if needed
            print(f"An error occurred while reading the first run file: {str(e)}")
            return 0

    def read_config(self):
        config_file = os.path.join(G_CONFIG_DIR, 'gui_config.ini')

        if os.path.exists(config_file):
            color_config = configparser.ConfigParser()
            color_config.read(config_file)

            self.bg_color = color_config.get('GUI', 'master_color', fallback='black')
            self.fg_color = color_config.get('GUI', 'main_fg_color', fallback='#C0FFEE')

    def update_first_run(self):
        config_directory = G_CONFIG_DIR
        file_path = os.path.join(config_directory, "first_run.txt")
        """
        Updates the first run file to indicate that the first run setup is complete.
        """
        try:
            with open(file_path, 'w') as file:
                file.write('1')
        except Exception as e:
            print(f"An error occurred while updating the first run file: {str(e)}")

    def set_screen_size(self, screen):
        try:
            width = screen.size().width()
            height = screen.size().height()
            screen_size = f"{width}x{height}"
        except Exception as e:
            logging.error(f"Unable to get screen size: {e} Using default variables.")
            self.app_size = "1100x900"
            self.config_window_size = "800x600"
            self.colour_selector_size = "450x900"

        # Determine window size based on screen resolution
        if screen_size == "3840x2160":  # 4K UHD
            self.window_size = "1650x1200"
        elif screen_size == "1920x1080":  # Full HD
            self.window_size = "1200x800" 
        elif screen_size == "2560x1440":  # QHD
            self.window_size = "1600x900" 
        elif screen_size == "1366x768":  # Common budget laptop
            self.window_size = "1024x600"
        elif screen_size == "2560x1600":  # MacBook Retina
            self.window_size = "1440x900" 
        elif screen_size == "3440x1440":  # Ultra-wide
            self.window_size = "2000x1000" 
        else:
            self.window_size = "800x600"  # Default fallback window size

        return self.window_size

    def open_client_config_window(self):
        config_directory = G_CONFIG_DIR
        
        def after_config_window_close():
            self.update_first_run()
            self.first_run_detect = 1

        def close_window():
            self.main_window.close()

        def on_config_window_close():
            QTimer.singleShot(100, after_config_window_close)
            QTimer.singleShot(200, close_window)
            return

        app = QApplication()
        self.main_window = QWidget()
        self.main_window.setWindowTitle("RudeChat: First Run Configuration")
        self.main_window.resize(450, 500)

        files = os.listdir(config_directory)
        config_files = [f for f in files if f.endswith(".rudeserver")]
        config_files.sort()

        if not config_files:
            QMessageBox.warning(self.main_window, "Warning", "No configuration files found.")
            self.main_window.close()
            return

        self.main_window.layout = QVBoxLayout(self.main_window)
        self.main_window.setContentsMargins(0, 0, 0, 0)

        config_window = ServerConfigWindow(self.main_window, os.path.join(config_directory, config_files[0]), on_config_window_close)

        def on_config_change():
            selected_config_file = selected_config_file_var.currentText()
            config_window.config_file = os.path.join(config_directory, selected_config_file)
            config_window.config.read(config_window.config_file)
            config_window.create_widgets()

        instruction_label = QLabel("Welcome to RudeChat's First Run Configuration. Please adjust your settings to your liking, then click Apply to start RudeChat. This will be the only time you see this menu.")
        instruction_label.setWordWrap(True)
        self.main_window.layout.addWidget(instruction_label)

        # Menu to choose configuration file
        selected_config_file_var = QComboBox()
        selected_config_file_var.addItems(config_files)
        selected_config_file_var.currentIndexChanged.connect(on_config_change)
        self.main_window.layout.addWidget(selected_config_file_var)

        self.main_window.layout.addWidget(config_window.frame)

        save_button = QPushButton("Start Client")
        save_button.clicked.connect(config_window.save_config)
        self.main_window.layout.addWidget(save_button)
        self.main_window.show()
        app.exec()

