from rudechat4.shared_imports import *
from rudechat4.global_variables import *


class GuiConfigWindow(QWidget):
    def __init__(self, parent, config_file, close_callback):
        super().__init__()
        self.parent = parent
        self.config_file = config_file
        self.close_callback = close_callback

        self.layout = QHBoxLayout(self)
        
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        self.create_widgets()

    def create_widgets(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)

        for section in config.sections():
            row_count = 0

            section_container = QScrollArea()
            section_container.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            section_container.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            section_container.setWidgetResizable(True)
            section_container.setFrameShape(QFrame.Shape.NoFrame)

            section_frame = QGroupBox(section_container)
            section_frame.layout = QGridLayout(section_frame)
            section_frame.layout.setColumnStretch(0, 1)
            section_frame.layout.setColumnStretch(1, 1)

            section_container.setWidget(section_frame)

            for option in config.options(section):
                label = QLabel(section_frame, text=option.replace("_", " ").title())
                label.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred))
                
                label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

                section_frame.layout.addWidget(label, row_count, 0, 1, 1)

                if config.get(section, option) in ["True", "False"]:
                    entry = QCheckBox(section_frame)
                    entry.setChecked(self.config.getboolean(section, option))

                else:
                    entry = QLineEdit(section_frame)
                    entry.setText(self.config.get(section, option))

                setattr(self, f"{section}_{option}", entry)

                section_frame.layout.addWidget(entry, row_count, 1, 1, 1)

                row_count += 1

            self.layout.addWidget(section_container)

    def save_changes(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)

        for section in config.sections():
            for option in config.options(section):
                entry = getattr(self, f"{section}_{option}")
                string_entry = type(entry).__name__
                if str(string_entry) == "QCheckBox":
                    config.set(section, option, str(entry.isChecked()))
                else:
                    config.set(section, option, entry.text())

        # Write the updated config back to the file
        with open(self.config_file, 'w') as configfile:
            config.write(configfile)

        # Close the window after saving changes
        self.close_callback()
