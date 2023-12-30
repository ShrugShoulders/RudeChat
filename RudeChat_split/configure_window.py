#!/usr/bin/env python
"""
GPL-3.0 License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import os

class ConfigWindow:
    def __init__(self, parent, config_file):
        self.parent = parent
        self.config_file = config_file

        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        self.create_widgets()

    def create_widgets(self):
        if hasattr(self, 'main_frame') and self.main_frame.winfo_exists():
            # Update existing widgets
            for (section, option), entry in self.entries.items():
                value = self.config.get(section, option)
                entry.delete(0, tk.END)
                entry.insert(0, value)
        else:
            # Create new widgets
            self.main_frame = ttk.Frame(self.parent)
            self.main_frame.pack(fill='both', expand=True)

            self.entries = {}

            for section in self.config.sections():
                section_frame = ttk.LabelFrame(self.main_frame, text=section)
                section_frame.pack(padx=10, pady=5, fill='both', expand=True)

                for option in self.config.options(section):
                    label = ttk.Label(section_frame, text=option)
                    label.grid(row=len(self.entries), column=0, padx=5, pady=2, sticky='e')

                    entry = ttk.Entry(section_frame)
                    entry.insert(0, self.config.get(section, option))
                    entry.grid(row=len(self.entries), column=1, padx=5, pady=2, sticky='w')

                    self.entries[(section, option)] = entry

    def save_config(self):
        try:
            for (section, option), entry in self.entries.items():
                value = entry.get()
                self.config.set(section, option, value)

            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)

            messagebox.showinfo("Success", "Configuration saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving configuration: {e}")