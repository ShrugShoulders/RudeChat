import json
import os
import tkinter as tk
from tkinter import messagebox, simpledialog, colorchooser
from tkcolorpicker import askcolor
from rudechat4.global_variables import *


class RudeColours:
    def __init__(self, root):
        self.root = root
        self.root.title("Colour Options Editor")

        self.color_options = {}
        
        self.colors_json_path = os.path.join(G_CONFIG_DIR, "nickname_colours.json")
        self.load_color_options()

        self.create_widgets()

    def load_color_options(self):
        try:
            with open(self.colors_json_path, "r") as file:
                self.color_options = json.load(file)
        except FileNotFoundError:
            self.color_options = {}

    def save_color_options(self):
        with open(self.colors_json_path, "w") as file:
            json.dump(self.color_options, file, indent=2)

    def create_widgets(self):
        # Create a search entry widget
        self.search_label = tk.Label(self.root, text="Search Nickname:")
        self.search_label.pack(pady=5)

        self.search_entry = tk.Entry(self.root, width=30)
        self.search_entry.pack(pady=5)
        self.search_entry.bind("<KeyRelease>", self.filter_list)

        # Create a scroll bar
        scrollbar = tk.Scrollbar(self.root, width=12)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(self.root, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set)
        self.listbox.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)

        # Attach the scroll bar to the listbox
        scrollbar.config(command=self.listbox.yview)

        # Insert the initial list of color options
        self.update_listbox()

        add_button = tk.Button(self.root, text="Add/Edit Color Option", command=self.add_edit_color_option)
        add_button.pack(pady=10)

    def update_listbox(self, filtered_options=None):
        # Clear the listbox and insert new items
        self.listbox.delete(0, tk.END)
        
        # If filtered options are provided, use them; otherwise, use all options
        color_options_to_display = filtered_options if filtered_options else self.color_options
        
        for key, value in color_options_to_display.items():
            self.listbox.insert(tk.END, f"{key}: {value}")

    def filter_list(self, event):
        # Get the search query
        query = self.search_entry.get().lower()
        
        # Filter the color options by the search query
        filtered_options = {key: value for key, value in self.color_options.items() if query in key.lower()}
        
        # Update the listbox with filtered results
        self.update_listbox(filtered_options)

    def add_edit_color_option(self):
        selected_index = self.listbox.curselection()

        if selected_index:
            selected_key = list(self.color_options.keys())[selected_index[0]]
            initial_value = self.color_options[selected_key]
        else:
            selected_key = ""
            initial_value = ""

        # Create a custom dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Add/Edit Color Option")
        dialog.transient(self.root)

        # Create entry fields for nickname and color
        nickname_label = tk.Label(dialog, text="Nickname:")
        nickname_label.grid(row=0, column=0, padx=5, pady=5)
        nickname_entry = tk.Entry(dialog, width=20)
        nickname_entry.insert(0, selected_key)
        nickname_entry.grid(row=0, column=1, padx=5, pady=5)

        color_label = tk.Label(dialog, text="Color:")
        color_label.grid(row=1, column=0, padx=5, pady=5)
        color_entry = tk.Entry(dialog, width=20)
        color_entry.insert(0, initial_value)
        color_entry.grid(row=1, column=1, padx=5, pady=5)

        # Button to open the color picker
        def pick_color():
            color = colorchooser.askcolor(color=initial_value)
            if color[1]:
                color_entry.delete(0, tk.END)
                color_entry.insert(0, color[1])

        pick_color_button = tk.Button(dialog, text="Pick Color", command=pick_color)
        pick_color_button.grid(row=1, column=2, padx=5, pady=5)

        # Function to remove the selected entry
        def remove_entry():
            if selected_key:
                del self.color_options[selected_key]
                self.save_color_options()

                # Update the listbox
                self.update_listbox()

                messagebox.showinfo("Success", f"Color option removed for {selected_key}!")

                dialog.destroy()

        # Function to save changes
        def save_changes():
            new_key = nickname_entry.get().strip()
            new_value = color_entry.get().strip()

            if new_key and new_value:
                self.color_options[new_key] = new_value

                if selected_key and new_key != selected_key:
                    del self.color_options[selected_key]

                self.save_color_options()

                # Update the listbox
                self.update_listbox()

                messagebox.showinfo("Success", f"Color option updated for {selected_key or new_key}!")

                dialog.destroy()

        # Create a button to save changes
        save_button = tk.Button(dialog, text="Save", command=save_changes)
        save_button.grid(row=2, column=0, pady=10)

        # Create a button to remove the entry
        remove_button = tk.Button(dialog, text="Remove", command=remove_entry)
        remove_button.grid(row=2, column=1, pady=10)
