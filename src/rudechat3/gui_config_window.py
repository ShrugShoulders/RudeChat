import tkinter as tk
from tkinter import ttk
import configparser

class GuiConfigWindow:
    def __init__(self, config_file):
        self.config_file = config_file
        self.root = tk.Tk()
        self.root.title("Rude GUI Configuration")
        
        # Create labels and entry fields for each configuration variable
        self.create_widgets()

    def create_widgets(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)

        for section in config.sections():
            tk.Label(self.root, text=section).pack()
            for option in config.options(section):
                self.create_setting_entry(section, option, config.get(section, option))

        # Button to save changes
        ttk.Button(self.root, text="Save", command=self.save_changes).pack()
        tk.Label(self.root, text="Once you click the Save button the GUI will automatically apply the settings.", wraplength=400).pack()

    def create_setting_entry(self, section, option, default_value):
        frame = tk.Frame(self.root)
        frame.pack(fill="x")

        label = tk.Label(frame, text=option.replace("_", " ").title(), anchor="w")
        label.pack(side="left")

        # Calculate the appropriate width for the label based on the length of setting_name
        label_width = max(20, len(option))  # Minimum width of 20 pixels
        label.config(width=label_width)

        entry = tk.Entry(frame)
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
