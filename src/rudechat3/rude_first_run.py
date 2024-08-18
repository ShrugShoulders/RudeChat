from .shared_imports import *
from .server_config_window import ServerConfigWindow


class FirstRun:
    def __init__(self):
        self.first_run_detect = self.load_first_run()
        self.script_directory = os.path.dirname(os.path.abspath(__file__))
        self.read_config()

    def load_first_run(self):
        script_directory = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_directory, "first_run.txt")
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
        config_file = os.path.join(self.script_directory, 'gui_config.ini')

        if os.path.exists(config_file):
            color_config = configparser.ConfigParser()
            color_config.read(config_file)

            self.bg_color = color_config.get('GUI', 'master_color', fallback='black')
            self.fg_color = color_config.get('GUI', 'main_fg_color', fallback='#C0FFEE')

    def update_first_run(self):
        script_directory = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_directory, "first_run.txt")
        """
        Updates the first run file to indicate that the first run setup is complete.
        """
        try:
            with open(file_path, 'w') as file:
                file.write('1')
        except Exception as e:
            print(f"An error occurred while updating the first run file: {str(e)}")

    def open_client_config_window(self):
        script_directory = os.path.dirname(os.path.abspath(__file__))
        def after_config_window_close():
            self.update_first_run()
            self.first_run_detect = 1

        def close_window():
            root.destroy()

        def on_config_window_close():
            root.after(100, after_config_window_close)
            root.after(200, close_window)
            return

        root = tk.Tk()
        root.title("Rude Server configuration: FIRST RUN")

        files = os.listdir(script_directory)
        config_files = [f for f in files if f.startswith("conf.") and f.endswith(".rude")]
        config_files.sort()

        if not config_files:
            tk.messagebox.showwarning("Warning", "No configuration files found.")
            root.destroy()
            return

        config_window = ServerConfigWindow(root, os.path.join(script_directory, config_files[0]), on_config_window_close)

        def on_config_change(event):
            selected_config_file = selected_config_file_var.get()
            config_window.config_file = os.path.join(script_directory, selected_config_file)
            config_window.config.read(config_window.config_file)
            config_window.create_widgets()

        # Menu to choose configuration file
        selected_config_file_var = tk.StringVar(root, config_files[0])
        config_menu = ttk.Combobox(root, textvariable=selected_config_file_var, values=config_files)
        config_menu.pack(pady=10)
        config_menu.bind("<<ComboboxSelected>>", on_config_change)

        save_button = tk.Button(root, text="Start Client", command=config_window.save_config, bg=self.bg_color, fg=self.fg_color)
        save_button.pack(pady=10)

        instruction_label = tk.Label(root, text="Welcome to RudeChat First Run Config: To create a new config file simply change the data in the fields, then edit the file name in the file selection above, configuration files must follow conf.exampleserver.rude format.", bg=self.bg_color, fg=self.fg_color, wraplength=180)
        instruction_label.pack()

        root.mainloop()

