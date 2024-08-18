import tkinter as tk
import configparser
import os

class GuiConfigWindow:
    def __init__(self, config_file):
        self.config_file = config_file
        self.root = tk.Tk()
        self.root.title("Rude GUI Configuration")
        self.script_directory = os.path.dirname(os.path.abspath(__file__))
        self.read_config()

        # Create main container frame
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(padx=1, pady=1, fill="both", expand=True)
        
        # Create frames for GUI and WIDGETS sections
        self.gui_frame = tk.LabelFrame(main_frame, text="GUI", padx=1, pady=1, bg=self.frame_bg_color, fg=self.fg_color)
        self.gui_frame.pack(side="left", padx=1, pady=1, fill="both", expand=True)
        
        self.widgets_frame = tk.LabelFrame(main_frame, text="WIDGETS", padx=1, pady=1, bg=self.frame_bg_color, fg=self.fg_color)
        self.widgets_frame.pack(side="left", padx=1, pady=1, fill="both", expand=True)
        
        # Create labels and entry fields for each configuration variable
        self.create_widgets()

        # Frame for save button and explanatory label
        bottom_frame = tk.Frame(self.root, bg=self.bg_color)
        bottom_frame.pack(padx=1, pady=1, fill="both", expand=True)
        
        # Button to save changes
        apply_button = tk.Button(bottom_frame, text="Apply", command=self.save_changes, bg=self.bg_color, fg=self.fg_color)
        apply_button.pack(pady=10)

    def read_config(self):
        config_file = os.path.join(self.script_directory, 'gui_config.ini')

        if os.path.exists(config_file):
            color_config = configparser.ConfigParser()
            color_config.read(config_file)

            self.bg_color = color_config.get('GUI', 'master_color', fallback='black')
            self.fg_color = color_config.get('GUI', 'main_fg_color', fallback='#C0FFEE')
            self.entry_bg_color = color_config.get('GUI', 'master_color', fallback='black')
            self.entry_fg_color = color_config.get('GUI', 'main_fg_color', fallback='#C0FFEE')
            self.frame_bg_color = color_config.get('GUI', 'master_color', fallback='black')
            self.root.configure(bg=self.bg_color)

    def create_widgets(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)

        for section in config.sections():
            if section == "GUI":
                frame = self.gui_frame
            elif section == "WIDGETS":
                frame = self.widgets_frame
            else:
                continue

            for option in config.options(section):
                self.create_setting_entry(frame, section, option, config.get(section, option))

    def create_setting_entry(self, frame, section, option, default_value):
        entry_frame = tk.Frame(frame, bg=self.frame_bg_color)
        entry_frame.pack(fill="x", pady=1)

        label = tk.Label(entry_frame, text=option.replace("_", " ").title(), anchor="w", bg=self.frame_bg_color, fg=self.fg_color)
        label.pack(side="left")

        # Calculate the appropriate width for the label based on the length of setting_name
        label_width = max(20, len(option))  # Minimum width of 20 pixels
        label.config(width=label_width)

        entry = tk.Entry(entry_frame, bg=self.entry_bg_color, fg=self.entry_fg_color)
        entry.insert(0, default_value)
        entry.pack(side="right", fill="x", expand=True)

        setattr(self, f"{section}_{option}", entry)

    def save_changes(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)

        for section in config.sections():
            for option in config.options(section):
                entry = getattr(self, f"{section}_{option}")
                config.set(section, option, entry.get())

        # Write the updated config back to the file
        with open(self.config_file, 'w') as configfile:
            config.write(configfile)

        # Close the window after saving changes
        self.root.destroy()