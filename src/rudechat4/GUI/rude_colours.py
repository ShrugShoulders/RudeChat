#!/usr/bin/env python3
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

from rudechat4.GUI.nick_editor import NickEditor

class RudeColours(QWidget):
    def __init__(self, reset_colors):
        super().__init__()

        self.resize(350, 500)

        self.layout = QVBoxLayout(self)

        self.selectedKey = None
        self.selectedIndex = -1

        self.color_options = {}
        self.colors_json_path = os.path.join(G_CONFIG_DIR, "nickname_colours.json")
        self.reset = reset_colors

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
        self.nicks_list.setHorizontalHeaderLabels(["Nickname", "Colour"])
        self.nicks_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.nicks_list.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.nicks_list.horizontalHeader().setStretchLastSection(True)
        self.nicks_list.verticalHeader().setVisible(False)

        self.layout.addWidget(self.search_bar)
        self.layout.addWidget(self.nicks_list)

        self.buttons = QHBoxLayout()
        self.buttons.setSpacing(5)

        self.add_button = QPushButton("Add", self)
        self.add_button.clicked.connect(self.add_option)
        self.buttons.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit", self)
        self.edit_button.setEnabled(False)
        self.edit_button.clicked.connect(self.edit_option)
        self.buttons.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete", self)
        self.delete_button.clicked.connect(self.delete_option)
        self.buttons.addWidget(self.delete_button)

        self.nicks_list.itemSelectionChanged.connect(self.update_index)

        self.layout.addLayout(self.buttons)

        self.update_list()

    def update_index(self):
        selected_items = self.nicks_list.selectedItems()
        if selected_items:
            key_item = self.nicks_list.item(self.nicks_list.currentRow(), 0)
            
            if key_item:
                self.selectedKey = key_item.text()
                self.selectedIndex = self.nicks_list.currentRow()
                self.edit_button.setEnabled(True)
            else:
                self.selectedKey = None
                self.selectedIndex = -1
                self.edit_button.setEnabled(False)
        else:
            self.edit_button.setEnabled(False)
            self.selectedKey = None
            self.selectedIndex = -1

    def update_list(self, filtered_options=None):
        # Clear the listbox and insert new items
        self.nicks_list.clearContents()
        
        self.nicks_list.setRowCount(len(self.color_options)) 

        # If filtered options are provided, use them; otherwise, use all options
        color_options_to_display = filtered_options if filtered_options else self.color_options

        self.nicks_list.setRowCount(len(color_options_to_display))

        index = 0
        for key, value in color_options_to_display.items():
            self.nicks_list.setItem(index, 0, QTableWidgetItem(key))
            self.nicks_list.setItem(index, 1, QTableWidgetItem(value))
            index += 1

        # After updating the list, reset the selected index and key if the previous selection is no longer valid
        if self.selectedIndex >= self.nicks_list.rowCount():
            self.selectedIndex = -1
            self.selectedKey = None
            self.edit_button.setEnabled(False)
        elif self.selectedIndex != -1 and self.selectedKey not in self.color_options:
            # This can happen if the selected item was deleted
            self.selectedIndex = -1
            self.selectedKey = None
            self.edit_button.setEnabled(False)

        elif self.nicks_list.rowCount() == 0:
            self.selectedIndex = -1
            self.selectedKey = None
            self.edit_button.setEnabled(False)

    def filter_list(self, event):
        # Get the search query
        query = self.search_bar.text().lower()

        # Filter the color options by the search query
        filtered_options = {key: value for key, value in self.color_options.items() if query in key.lower()}

        # Update the listbox with filtered results
        self.update_list(filtered_options)

    def add_option(self):
        self.editor = NickEditor(self.save_changes)

        self.editor.show()

    def edit_option(self):
        if self.selectedKey:
            initial_value = self.color_options[self.selectedKey]
            self.editor = NickEditor(self.save_changes, self.selectedKey, initial_value)
            self.editor.show()

    def delete_option(self):
        if self.selectedKey:
            del self.color_options[self.selectedKey]
            self.save_color_options()

            # Update the listbox
            self.update_list()
            self.selectedKey = None
            self.selectedIndex = -1
            self.edit_button.setEnabled(False)

    def save_changes(self, key, value):
        new_key = key.strip()
        new_value = value.strip()

        if new_key and new_value:
            if self.selectedKey and new_key != self.selectedKey and new_key in self.color_options:
                QMessageBox.warning(self, "Warning", f"Nickname '{new_key}' already exists.")
                return

            if self.selectedKey and new_key != self.selectedKey:
                del self.color_options[self.selectedKey]
                self.selectedKey = new_key
            elif not self.selectedKey:
                self.selectedKey = new_key

            self.color_options[new_key] = new_value
            self.save_color_options()

            # Update the listbox
            self.update_list()
            # Try to re-select the edited item
            try:
                index = list(self.color_options.keys()).index(new_key)
                self.nicks_list.setCurrentCell(index, 0)
            except ValueError:
                pass
            self.reset()
