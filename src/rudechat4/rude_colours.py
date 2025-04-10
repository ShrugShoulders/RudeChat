from rudechat4.shared_imports import *
from rudechat4.global_variables import *

class RudeColours(QWidget):
    def __init__(self):
        super().__init__()
        
        self.resize(300, 500)

        self.layout = QVBoxLayout(self)

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
        self.search_bar = QLineEdit(self, placeholderText="Search...")
        self.search_bar.textChanged.connect(self.filter_list)

        self.nicks_list = QTableWidget(self)
        self.nicks_list.setColumnCount(2)
        self.nicks_list.setRowCount(1)
        self.nicks_list.setHorizontalHeaderLabels(["Nickname", "Colour"])
        self.nicks_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.nicks_list.horizontalHeader().setStretchLastSection(True)
        self.nicks_list.verticalHeader().setVisible(False)

        self.layout.addWidget(self.search_bar)
        self.layout.addWidget(self.nicks_list)

        self.buttons = QHBoxLayout()
        self.buttons.setSpacing(5)

        self.add_button = QPushButton("Add", self)
        self.buttons.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit", self)
        self.buttons.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Delete", self)
        self.buttons.addWidget(self.delete_button)

        self.layout.addLayout(self.buttons)

        self.update_list()

    def update_list(self, filtered_options=None):
        # Clear the listbox and insert new items
        self.nicks_list.clearContents()
        self.nicks_list.setRowCount(len(self.color_options))

        # If filtered options are provided, use them; otherwise, use all options
        color_options_to_display = filtered_options if filtered_options else self.color_options

        index = 0
        for key, value in color_options_to_display.items():

            self.nicks_list.setItem(index, 0, QTableWidgetItem(key))
            self.nicks_list.setItem(index, 1, QTableWidgetItem(value))
            index += 1

    def filter_list(self, event):
        # Get the search query
        query = self.search_bar.text().lower()
        
        # Filter the color options by the search query
        filtered_options = {key: value for key, value in self.color_options.items() if query in key.lower()}
        
        # Update the listbox with filtered results
        self.update_list(filtered_options)

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
                self.update_list()

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
                self.update_list()

                messagebox.showinfo("Success", f"Color option updated for {selected_key or new_key}!")

                dialog.destroy()

        # Create a button to save changes
        save_button = tk.Button(dialog, text="Save", command=save_changes)
        save_button.grid(row=2, column=0, pady=10)

        # Create a button to remove the entry
        remove_button = tk.Button(dialog, text="Remove", command=remove_entry)
        remove_button.grid(row=2, column=1, pady=10)
