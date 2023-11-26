#!/usr/bin/env python
from shared_imports import *
class ConfigWindow(tk.Toplevel):
    def __init__(self, current_config):
        super().__init__()
        self.title("Configuration")
        self.geometry("500x400")
        self.config_font = tkFont.Font(family="Hack", size=10)

        # Labels
        label_name = tk.Label(self, text="Nickname:", font=self.config_font)
        label_name.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        label_server = tk.Label(self, text="Server Address:", font=self.config_font)
        label_server.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

        label_channels = tk.Label(self, text="Auto-join Channels (comma-separated):", font=self.config_font)
        label_channels.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)

        label_password = tk.Label(self, text="Password:", font=self.config_font)
        label_password.grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)

        label_port = tk.Label(self, text="Port:", font=self.config_font)
        label_port.grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)

        label_ssl = tk.Label(self, text="SSL Enabled:", font=self.config_font)
        label_ssl.grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)

        # Entry fields
        self.entry_name = tk.Entry(self)
        self.entry_name.grid(row=0, column=1, padx=5, pady=5)

        self.entry_server = tk.Entry(self)
        self.entry_server.grid(row=1, column=1, padx=5, pady=5)

        self.entry_channels = tk.Entry(self)
        self.entry_channels.grid(row=2, column=1, padx=5, pady=5)

        self.entry_password = tk.Entry(self, show="*")  # Mask the password with '*'
        self.entry_password.grid(row=3, column=1, padx=5, pady=5)

        self.entry_port = tk.Entry(self)
        self.entry_port.grid(row=4, column=1, padx=5, pady=5)

        self.entry_ssl = tk.BooleanVar()
        self.checkbox_ssl = tk.Checkbutton(self, variable=self.entry_ssl)
        self.checkbox_ssl.grid(row=5, column=1, padx=5, pady=5)

        # SASL Configuration
        label_sasl_enabled = tk.Label(self, text="SASL Enabled:", font=self.config_font)
        label_sasl_enabled.grid(row=8, column=0, padx=5, pady=5, sticky=tk.W)

        self.entry_sasl_enabled = tk.BooleanVar()
        self.checkbox_sasl_enabled = tk.Checkbutton(self, variable=self.entry_sasl_enabled)
        self.checkbox_sasl_enabled.grid(row=8, column=1, padx=5, pady=5)

        label_sasl_username = tk.Label(self, text="SASL Username:", font=self.config_font)
        label_sasl_username.grid(row=9, column=0, padx=5, pady=5, sticky=tk.W)

        self.entry_sasl_username = tk.Entry(self)
        self.entry_sasl_username.grid(row=9, column=1, padx=5, pady=5)

        label_sasl_password = tk.Label(self, text="SASL Password:", font=self.config_font)
        label_sasl_password.grid(row=10, column=0, padx=5, pady=5, sticky=tk.W)

        self.entry_sasl_password = tk.Entry(self, show="*")  # Mask the password with '*'
        self.entry_sasl_password.grid(row=10, column=1, padx=5, pady=5)

        # Font Selection
        label_font = tk.Label(self, text="Font:", font=self.config_font)
        label_font.grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)

        self.font_var = tk.StringVar(self)
        self.font_var.set(self.config_font.actual()['family'])  #set the default font based on current font
        fonts = ["Monospace", "Consolas", "Hack"]
        font_dropdown = tk.OptionMenu(self, self.font_var, *fonts, command=self.update_font)
        font_dropdown.grid(row=6, column=1, padx=5, pady=5)

        # Font Size Selection
        label_font_size = tk.Label(self, text="Font Size:", font=self.config_font)
        label_font_size.grid(row=7, column=0, padx=5, pady=5, sticky=tk.W)

        self.font_size_var = tk.StringVar(self)
        default_size = str(current_config.get("font_size", 10))  # Default to 10 if not in config
        self.font_size_var.set(default_size)
        font_sizes = [str(i) for i in range(8, 21)]  # List of font sizes from 8 to 20
        font_size_dropdown = tk.OptionMenu(self, self.font_size_var, *font_sizes)
        font_size_dropdown.grid(row=7, column=1, padx=5, pady=5)

        # Save Button
        save_button = tk.Button(self, text="Save Configuration", command=self.save_config)
        save_button.grid(row=11, column=0, columnspan=2, padx=5, pady=5)

        # Set the current configuration values in the entry fields
        self.entry_name.insert(0, current_config["nickname"])
        self.entry_server.insert(0, current_config["server"])
        self.entry_channels.insert(0, (current_config["auto_join_channels"]))
        self.entry_password.insert(0, current_config["nickserv_password"])
        self.entry_port.insert(0, current_config["port"])
        self.entry_ssl.set(current_config["ssl_enabled"])
        self.entry_sasl_enabled.set(current_config.get("sasl_enabled", False))
        self.entry_sasl_username.insert(0, current_config.get("sasl_username", ""))
        self.entry_sasl_password.insert(0, current_config.get("sasl_password", ""))

    def update_font(self, font_choice):
        """Updates the font when the user selects a new font from the dropdown."""
        self.config_font.config(family=font_choice)
        for widget in self.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(font=self.config_font)

    def save_config(self):
        user_nick = self.entry_name.get()
        server_address = self.entry_server.get()
        channels = self.entry_channels.get()
        password = self.entry_password.get()
        port = self.entry_port.get()
        ssl_enabled = self.entry_ssl.get()
        # Get SASL configurations from the entry fields
        sasl_enabled = self.entry_sasl_enabled.get()
        sasl_username = self.entry_sasl_username.get()
        sasl_password = self.entry_sasl_password.get()

        # Create a new configparser object
        config = configparser.ConfigParser()

        # Update the configuration values directly
        config["IRC"] = {
            "nickname": user_nick,
            "server": server_address,
            "auto_join_channels": channels,
            "nickserv_password": password,
            "port": port,
            "ssl_enabled": ssl_enabled,
            "font_family": self.font_var.get(),
            "font_size": self.font_size_var.get(),
            "sasl_enabled": sasl_enabled,
            "sasl_username": sasl_username,
            "sasl_password": sasl_password
        }

        # Determine if running as a script or as a frozen executable
        if getattr(sys, 'frozen', False):
            # Running as compiled
            script_directory = os.path.dirname(sys.executable)
        else:
            # Running as script
            script_directory = os.path.dirname(os.path.abspath(__file__))

        # Construct the full path for the conf.rude file
        config_file_path = os.path.join(script_directory, 'conf.rude')

        # Write the updated configuration to the conf.rude file using the full path
        with open(config_file_path, "w", encoding='utf-8') as config_file:
            config.write(config_file)

        self.destroy()
