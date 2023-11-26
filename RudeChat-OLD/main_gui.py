#!/usr/bin/env python
from shared_imports import *
class IRCClientGUI:
    def __init__(self, irc_client):
        # Initialize attributes
        self.init_attributes(irc_client)
        
        # Set up the main GUI window
        self.setup_main_window()
        
        # Configure fonts and other styles
        self.configure_styles()
        
        # Set up the menu
        self.setup_menu()
        
        # Create and configure GUI widgets
        self.create_widgets()
        
        # Set up layout
        self.setup_layout()
        
        # Bind events
        self.bind_events()
        
        # Start threads
        self.start_threads()

    def init_attributes(self, irc_client):
        # Determine if running as a script or as a frozen executable
        if getattr(sys, 'frozen', False):
            # Running as compiled
            script_directory = os.path.dirname(sys.executable)
            # Directly append 'Art' to the script_directory
            self.ASCII_ART_DIRECTORY = os.path.join(script_directory, 'Art')
        else:
            # Running as script
            script_directory = os.path.dirname(os.path.abspath(__file__))
            self.ASCII_ART_DIRECTORY = os.path.join(script_directory, 'Art')

        self.irc_client = irc_client
        self.exit_event = irc_client.exit_event
        self.channels_with_mentions = []
        self.channels_with_activity = []
        self.input_history = []
        self.nickname_colors = {}
        self.channel_input_dict = {}
        self.current_channel = None
        self.ASCII_ART_MACROS = self.load_ascii_art_macros()
        self.current_config = self.load_config()
        self.selected_channel = None
        self.history_position = -1  
        self.MAX_HISTORY = 8 

    def setup_main_window(self):
        """Set up the main window of the GUI."""
        
        # Determine if running as a script or as a frozen executable
        if getattr(sys, 'frozen', False):
            # Running as compiled
            script_directory = os.path.dirname(sys.executable)
        else:
            # Running as script
            script_directory = os.path.dirname(os.path.abspath(__file__))
        
        self.root = tk.Tk()
        self.root.title("RudeChat")
        self.root.geometry("1200x800")
        
        # Platform-specific icon setting
        if platform.system() == "Windows":
            icon_path = os.path.join(script_directory, "rude.ico")
            self.root.iconbitmap(True, icon_path)
        else:
            icon_path = os.path.join(script_directory, "rude.png")
            self.icon_image = tk.PhotoImage(file=icon_path)
            self.root.iconphoto(True, self.icon_image)

        self.root.protocol("WM_DELETE_WINDOW", self.handle_exit)
            
    def configure_styles(self):
        default_font = self.current_config.get("font_family", "Hack")
        default_size = int(self.current_config.get("font_size", 10))
        self.chat_font = tkFont.Font(family=default_font, size=default_size)
        self.channel_user_list_font = tkFont.Font(family="Hack", size=9)
        self.server_font = tkFont.Font(family="Hack", size=9)

    def setup_menu(self):
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Settings", menu=self.settings_menu)
        self.settings_menu.add_command(label="Configure", command=self.open_config_window)
        self.settings_menu.add_command(label="Reload Macros", command=self.reload_ascii_macros)
        self.settings_menu.add_command(label="Reload Ignore List", command=self.irc_client.reload_ignore_list)
        self.settings_menu.add_command(label="Reset Nick Color", command=self.reset_nick_colors)
        self.settings_menu.add_command(label="Help", command=self.display_help)

    def create_widgets(self):
        self.server_feedback_text = scrolledtext.ScrolledText(self.root, state=tk.DISABLED, bg="black", fg="#ff0000", height=5, font=self.server_font)
        current_font = self.server_feedback_text.cget("font")
        self.server_feedback_text.tag_configure("bold", font=(current_font, 10, "bold")) 
        self.server_feedback_text.tag_configure("italic", font=(current_font, 10, "italic"))
        self.server_feedback_text.tag_configure("bold_italic", font=(current_font, 10, "bold italic"))
        self.server_feedback_text.tag_configure("server_feedback", foreground="#7882ff")
        self.bold_font = ("Hack", 10, "bold")
        self.italic_font = ("Hack", 10, "italic")
        self.bold_italic_font = ("Hack", 10, "bold italic") 

        self.paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.message_frame = tk.Frame(self.paned_window, bg="black")
        self.message_text = scrolledtext.ScrolledText(self.message_frame, state=tk.DISABLED, bg="black", fg="#C0FFEE", cursor="arrow", font=self.chat_font)
        self.user_list_frame = tk.Frame(self.paned_window, width=20, height=400, bg="black")
        self.user_list_label = tk.Label(self.user_list_frame, text="Users:", bg="black", fg="#39ff14")
        self.user_list_text = scrolledtext.ScrolledText(self.user_list_frame, width=5, height=20, bg="black", fg="#39ff14", cursor="arrow", font=self.channel_user_list_font)
        self.joined_channels_label = tk.Label(self.user_list_frame, text="Channels:", bg="black", fg="#00bfff")
        self.joined_channels_text = scrolledtext.ScrolledText(self.user_list_frame, width=5, height=20, bg="black", fg="#ffffff", cursor="arrow", font=self.channel_user_list_font)
        self.input_frame = tk.Frame(self.root)
        self.nickname_label = tk.Label(self.input_frame, font=("Hack", 9, "italic"), text=f" $ {self.irc_client.nickname} #> ")
        self.input_entry = tk.Entry(self.input_frame)
        self.exit_button = tk.Button(self.input_frame, text="Exit", command=self.handle_exit)
        self.init_input_menu()
        self.init_message_menu()
        self.init_server_menu()
        self.init_user_menu()
        self.init_channel_menu()

    def setup_layout(self):
        self.server_feedback_text.grid(row=1, column=0, sticky="nsew", padx=1, pady=1)
        self.paned_window.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        self.paned_window.add(self.message_frame)
        self.message_text.pack(fill=tk.BOTH, expand=True)
        self.paned_window.add(self.user_list_frame)
        self.user_list_label.pack()
        self.user_list_text.pack(fill=tk.BOTH, expand=True)
        self.joined_channels_label.pack()
        self.joined_channels_text.pack(fill=tk.BOTH, expand=True)
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=1, pady=1)
        self.nickname_label.pack(side=tk.LEFT)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.exit_button.pack(side=tk.RIGHT)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0) 
        self.root.grid_columnconfigure(0, weight=1)

    def bind_events(self):
        self.input_entry.bind("<Return>", self.handle_input)
        self.input_entry.bind("<Tab>", self.handle_tab_complete)
        self.input_entry.bind('<Up>', self.navigate_history)
        self.input_entry.bind('<Down>', self.navigate_history)
        self.joined_channels_text.bind("<Button-1>", self.switch_channel)
        self.joined_channels_text.bind("<B1-Motion>", lambda event: "break")
        self.joined_channels_text.bind("<ButtonRelease-1>", lambda event: "break")
        self.root.bind("<Configure>", self.delayed_sash_position)
        self.last_width = self.root.winfo_width()

    def start_threads(self):
        self.client_start_thread = threading.Thread(target=self.irc_client.start)
        self.client_start_thread.daemon = True 
        self.client_start_thread.start()
        self.irc_client.irc_client_gui = self

    def delayed_sash_position(self, event):
        # Cancel any previous delayed adjustments
        if hasattr(self, "sash_adjustment_id"):
            self.root.after_cancel(self.sash_adjustment_id)
        # Schedule a new adjustment 100ms in the future
        self.sash_adjustment_id = self.root.after(20, self.adjust_sash_position)

    def adjust_sash_position(self):
        new_width = self.root.winfo_width()
        if new_width != self.last_width:
            self.paned_window.sash_place(0, new_width - 170, 0)
            self.last_width = new_width

    def init_input_menu(self):
        """
        Right click menu.
        """
        self.input_menu = Menu(self.input_entry, tearoff=0)
        self.input_menu.add_command(label="Cut", command=self.cut_text)
        self.input_menu.add_command(label="Copy", command=self.copy_text)
        self.input_menu.add_command(label="Paste", command=self.paste_text)
        self.input_menu.add_command(label="Select All", command=self.select_all_text)

        self.input_entry.bind("<Button-3>", self.show_input_menu)

    def init_message_menu(self):
        """
        Right click menu for the main chat window.
        """
        self.message_menu = Menu(self.message_text, tearoff=0)
        self.message_menu.add_command(label="Copy", command=self.copy_text_message)
        
        self.message_text.bind("<Button-3>", self.show_message_menu)

    def init_server_menu(self):
        """
        Right click menu for the server window.
        """
        self.server_menu = Menu(self.server_feedback_text, tearoff=0)
        self.server_menu.add_command(label="Copy", command=self.copy_text_server)

        self.server_feedback_text.bind("<Button-3>", self.show_server_menu)

    def init_user_menu(self):
        self.user_list_menu = Menu(self.user_list_text, tearoff=0)
        self.user_list_menu.add_command(label="Copy", command=self.copy_text_user)
        self.user_list_menu.add_command(label="Whois", command=self.handle_whois)
        self.user_list_menu.add_command(label="Query", command=self.query_user)

        self.user_list_text.bind("<Button-3>", self.show_user_list_menu)

    def init_channel_menu(self):
        """
        Initialize right-click menu for the channel list.
        """
        self.channel_menu = Menu(self.joined_channels_text, tearoff=0)
        self.joined_channels_text.bind("<Button-3>", self.show_channel_menu)

    def handle_leave_channel(self):
        if self.selected_channel:
            self.irc_client.leave_channel(self.selected_channel)

    def handle_whois(self):
        if hasattr(self, 'selected_nick') and self.selected_nick:
            cleaned_nick = self.selected_nick.replace('+', '').replace('@', '')
            self.irc_client.whois(cleaned_nick)

    def show_channel_menu(self, event):
        try:
            # Get the channel name where the user right-clicked
            self.selected_channel = self.joined_channels_text.get("current linestart", "current lineend").strip()
            
            # Clear the existing menu items
            self.channel_menu.delete(0, 'end')

            if self.selected_channel.startswith("DM:"):  # If it's a DM
                self.channel_menu.add_command(label="Close Query", command=self.close_query)
            else:  # If it's a regular channel
                self.channel_menu.add_command(label="Leave Channel", command=self.handle_leave_channel)

            # Display the context menu
            if self.selected_channel:
                self.channel_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.channel_menu.grab_release()

    def show_user_list_menu(self, event):
        try:
            # Get the nickname where the user right-clicked
            self.selected_nick = self.user_list_text.get("current linestart", "current lineend").strip()
            if self.selected_nick:
                self.user_list_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.user_list_menu.grab_release()

    def show_message_menu(self, event):
        try:
            self.message_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.message_menu.grab_release()

    def show_input_menu(self, event):
        try:
            self.input_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.input_menu.grab_release()

    def show_server_menu(self, event):
        try:
            self.server_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.server_menu.grab_release()

    def cut_text(self):
        self.input_entry.event_generate("<<Cut>>")

    def copy_text(self):
        self.input_entry.event_generate("<<Copy>>")

    def copy_text_message(self):
        self.message_text.event_generate("<<Copy>>")

    def copy_text_server(self):
        self.server_feedback_text.event_generate("<<Copy>>")

    def copy_text_user(self):
        self.user_list_text.event_generate("<<Copy>>")

    def paste_text(self):
        self.input_entry.event_generate("<<Paste>>")

    def select_all_text(self):
        self.input_entry.select_range(0, tk.END)
        self.input_entry.icursor(tk.END)

    def query_user(self):
        target_user = self.selected_nick
        # Remove "@" and "+" from the beginning of the nick
        if target_user.startswith("@") or target_user.startswith("+"):
            target_user = target_user[1:]

        if target_user not in self.irc_client.dm_users:
            self.irc_client.dm_users.append(target_user)
            self.update_message_text(f"DM opened with {target_user}.\r\n")
            self.update_joined_channels_list("DM: " + target_user) 
        else:
            self.update_message_text(f"You already have a DM opened with {target_user}.\r\n")

    def close_query(self):
        target_channel = self.selected_channel

        # Check if the selected channel is a DM
        if target_channel.startswith("DM:"):
            target_user = target_channel.split("DM:")[1].strip()  # Extract the username from the "DM:username" format
            
            if target_user in self.irc_client.dm_users:
                self.irc_client.dm_users.remove(target_user)
                if target_user in self.irc_client.dm_messages:
                    del self.irc_client.dm_messages[target_user]  # Remove chat history
                self.update_message_text(f"DM closed with {target_user}.\r\n")
                self.update_joined_channels_list(None)
            else:
                self.update_message_text(f"You don't have a DM opened with {target_user}.\r\n")
        else:
            pass

    def open_config_window(self):
        from config_window import ConfigWindow
        config_window = ConfigWindow(self.current_config)
        config_window.mainloop()

    def check_for_channel_list_display(self):
        if self.show_channel_list_flag:
            self.display_channel_list()
            self.show_channel_list_flag = False
        self.after(100, self.check_for_channel_list_display)

    def reset_nick_colors(self):
        self.nickname_colors = {}
        self.update_message_text(f"Nick Colors Reset\r\n")

    def trigger_desktop_notification(self, channel_name=None, title="Ping", message_content=None):
        """
        Show a system desktop notification.
        """
        script_directory = os.path.dirname(os.path.abspath(__file__))
        # Check if the application window is the active window
        if self.is_app_focused():  # If the app is focused, return early
            return

        if channel_name:
            # Ensure channel_name is a string and replace problematic characters
            channel_name = str(channel_name).replace("#", "channel ")
            title = f"{title} from {channel_name}"
            if message_content:
                message = f"{channel_name}: {message_content}"
            else:
                message = f"You've been pinged in {channel_name}!"

        icon_path = os.path.join(script_directory, "rude.ico")

        try:
            # Desktop Notification
            notification.notify(
                title=title,
                message=message,
                app_icon=icon_path,  
                timeout=5,  
            )
        except Exception as e:
            print(f"Desktop notification error: {e}")

    def load_ascii_art_macros(self):
        """Load ASCII art from files into a dictionary."""
        ascii_macros = {}
        for file in os.listdir(self.ASCII_ART_DIRECTORY):
            if file.endswith(".txt"):
                with open(os.path.join(self.ASCII_ART_DIRECTORY, file), 'r', encoding='utf-8') as f:
                    macro_name, _ = os.path.splitext(file)
                    ascii_macros[macro_name] = f.read()
        return ascii_macros

    def reload_ascii_macros(self):
        """Clears and reloads the ASCII art macros from files."""
        self.ASCII_ART_MACROS.clear()  # Clear the current dictionary
        self.ASCII_ART_MACROS = self.load_ascii_art_macros()
        self.update_message_text(f'ASCII art macros reloaded!\r\n') 

    def is_app_focused(self):
        return bool(self.root.focus_displayof())

    def load_config(self):
        """Load the configuration file."""
        
        # Determine if running as a script or as a frozen executable
        if getattr(sys, 'frozen', False):
            # Running as compiled
            script_directory = os.path.dirname(sys.executable)
        else:
            # Running as script
            script_directory = os.path.dirname(os.path.abspath(__file__))
        
        config_file_path = os.path.join(script_directory, 'conf.rude')

        config = configparser.ConfigParser()
        config.read(config_file_path)
        
        return dict(config["IRC"]) # Convert to dictionary

    def switch_channel(self, event):
        # Save the current input to the old channel or DM
        old_channel = self.irc_client.current_channel
        self.channel_input_dict[old_channel] = self.input_entry.get()

        # get the selected channel or DM from the clicked position
        index = self.joined_channels_text.index("@%d,%d" % (event.x, event.y))
        line_num = int(index.split(".")[0])
        selection = self.joined_channels_text.get(f"{line_num}.0", f"{line_num}.end").strip()
        self.current_channel = selection

        # Clear the main chat window
        self.clear_chat_window()

        if selection.startswith("DM: "):  # If it's a DM
            user = selection[4:]
            if user in self.irc_client.dm_users:
                self.display_dm_messages(user)  # Display DMs with this user
                self.update_window_title(self.irc_client.nickname, f"DM with {user}")
                self.irc_client.current_channel = user  # Since it's a DM, not a channel
                self.joined_channels_text.tag_remove("dm", f"{line_num}.0", f"{line_num}.end")

        elif selection in self.irc_client.joined_channels:  # If it's a channel
            self.irc_client.current_channel = selection
            self.display_channel_messages()  # Display messages from this channel
            self.update_window_title(self.irc_client.nickname, selection)

        # Highlight the selected channel/DM
        if self.selected_channel:
            self.joined_channels_text.tag_remove("selected", 1.0, tk.END)
        self.joined_channels_text.tag_add("selected", f"{line_num}.0", f"{line_num}.end")
        self.selected_channel = selection

        # Load the saved input for the new channel or DM
        new_channel = self.irc_client.current_channel
        saved_input = self.channel_input_dict.get(new_channel, "")
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, saved_input)

        # Reset the color of the clicked channel by removing the "mentioned" and "activity" tags
        self.joined_channels_text.tag_remove("mentioned", f"{line_num}.0", f"{line_num}.end")
        self.channels_with_mentions = []
        self.joined_channels_text.tag_remove("activity", f"{line_num}.0", f"{line_num}.end")
        if selection in self.channels_with_activity:
            self.channels_with_activity.remove(selection)
            
        return "break"

    def clear_chat_window(self):
        self.message_text.config(state=tk.NORMAL)
        self.message_text.delete(1.0, tk.END)
        self.message_text.config(state=tk.DISABLED)

    def generate_random_color(self):
        # Randomly pick which channel will be bright
        bright_channel = random.choice(['r', 'g', 'b'])
        
        # Generate random values for each channel
        r = random.randint(50, 255) if bright_channel != 'r' else random.randint(200, 255)
        g = random.randint(50, 255) if bright_channel != 'g' else random.randint(200, 255)
        b = random.randint(50, 255) if bright_channel != 'b' else random.randint(200, 255)

        return "#{:02x}{:02x}{:02x}".format(r, g, b)

    def handle_input(self, event):
        """
        This handles the user input, passes to command parser if needed.
        """
        user_input = self.input_entry.get()
        
        # Check for empty input
        if not user_input:
            return  # Exit the method without doing anything if input is empty

        current_channel = self.irc_client.current_channel
        self.channel_input_dict[current_channel] = self.input_entry.get()
        
        # Add the input to history and adjust the position
        if len(self.input_history) >= self.MAX_HISTORY:
            self.input_history.pop(0)  # Remove the oldest entry if history is full
        self.input_history.append(user_input)
        self.history_position = len(self.input_history)  # Reset the position to the end
        
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
        if user_input[0] == "/":
            self._command_parser(user_input, user_input[1:].split()[0])
        else:
            self.irc_client._send_message(f'PRIVMSG {self.irc_client.current_channel} :{user_input}')
            self.update_message_text(f'{timestamp} <{self.irc_client.nickname}> {user_input}\r\n')
        self.input_entry.delete(0, tk.END)

    def _command_parser(self, user_input:str, command: str):
        """
        It's the command parser, thanks cow!
        """
        args = user_input[1:].split()
        primary_command = args[0]
        match command:
            case "quit": #exits client.
                self.handle_exit()
            case "disconnect": #disconnects from network.
                self.irc_client._send_message('QUIT')
                time.sleep(1)
                self.irc_client.disconnect()
            case "reconnect": #reconnects to network
                self.irc_client.reconnect()
            case "connect": #connects to new network.
                server = args[1] if len(args) > 1 else None
                port = int(args[2]) if len(args) > 2 else None
                self.irc_client.reconnect(server, port)
            case "join": #joing channel
                channel_name = user_input.split()[1]
                self.irc_client.join_channel(channel_name)
            case "part": #part channel
                channel_name = user_input.split()[1]
                self.irc_client.leave_channel(channel_name)
            case "quote": #sends raw IRC message to the server
                if len(args) > 1:
                    raw_message = ' '.join(args[1:])
                    self.irc_client._send_message(raw_message)
                else:
                    print("Usage: /quote [raw IRC message]")
            case "query": #open a DM with a user
                target_user = user_input.split()[1] if len(user_input.split()) > 1 else None
                if not target_user:
                    self.update_message_text("Invalid usage. Usage: /query <nickname>\r\n")
                    return
                if target_user not in self.irc_client.dm_users:
                    self.irc_client.dm_users.append(target_user)
                    self.update_message_text(f"DM opened with {target_user}.\r\n")
                    self.update_joined_channels_list("DM: " + target_user) 
                else:
                    self.update_message_text(f"You already have a DM opened with {target_user}.\r\n")
            case "away": # set the user as away
                if len(args) > 1:  # Check if an away message has been provided
                    away_message = ' '.join(args[1:])
                    self.irc_client._send_message(f'AWAY :{away_message}')
                else:  # If no away message, it typically removes the away status.
                    self.irc_client._send_message('AWAY')
            case "back": # remove the "away" status
                self.irc_client._send_message('AWAY')
            case "msg": #send a message to a user
                parts = user_input.split(' ', 2)
                if len(parts) >= 3:
                    receiver = parts[1]
                    message_content = parts[2]
                    self.irc_client._send_message(f'PRIVMSG {receiver} :{message_content}')
                    self.update_message_text(f'<{self.irc_client.nickname} -> {receiver}> {message_content}\r\n')
                else:
                    self.update_message_text(f"Invalid usage. Usage: /msg <nickname> <message_content>\r\n")
            case "cq": #close a DM with a user
                target_user = user_input.split()[1] if len(user_input.split()) > 1 else None
                if not target_user:
                    self.update_message_text("Invalid usage. Usage: /cq <nickname>\r\n")
                    return
                if target_user in self.irc_client.dm_users:
                    self.irc_client.dm_users.remove(target_user)
                    if target_user in self.irc_client.dm_messages:
                        del self.irc_client.dm_messages[target_user]  # Remove chat history
                    self.update_message_text(f"DM closed with {target_user}.\r\n")
                    self.update_joined_channels_list(None)  # Call the update method to refresh the GUI
                else:
                    self.update_message_text(f"You don't have a DM opened with {target_user}.\r\n")
            case "sw": #switch channels.
                channel_name = user_input.split()[1]
                self.irc_client.current_channel = channel_name
                self.display_channel_messages()
                self.update_window_title(self.irc_client.nickname, channel_name)
            case "topic": #requests topic only for right now
                self.irc_client._send_message(f'TOPIC {self.irc_client.current_channel}')
            case "help": #HELP!
                self.display_help()
            case "names": #refreshes user list
                self.irc_client.sync_user_list()
            case "nick": #changes nickname
                new_nickname = user_input.split()[1]
                self.irc_client.change_nickname(new_nickname)
            case "me": #ACTION command
                parts = user_input.split(' ', 1)
                if len(parts) > 1:
                    action_content = parts[1]
                    current_time = datetime.datetime.now().strftime('%H:%M:%S')
                    action_message = f'\x01ACTION {action_content}\x01'
                    self.irc_client._send_message(f'PRIVMSG {self.irc_client.current_channel} :{action_message}')
                    self.update_message_text(f'[{current_time}] * {self.irc_client.nickname} {action_content}\r\n')
                else:
                    self.update_message_text("Invalid usage. Usage: /me <action_content>\r\n")
            case "whois": #who is that?
                target = user_input.split()[1]
                self.irc_client.whois(target)
            case "who":
                self.handle_who_command(args[1:])
            case "ping": #PNOG
                parts = user_input.split()
                target = parts[1] if len(parts) > 1 else None
                self.irc_client.ping_server(target)
            case "clear": #Clears the screen
                self.clear_chat_window()
            case "ignore": #ignores a user
                user_to_ignore = " ".join(user_input.split()[1:])
                if user_to_ignore:
                    if user_to_ignore not in self.irc_client.ignore_list:
                        self.irc_client.ignore_list.append(user_to_ignore)
                        self.update_message_text(f"You've ignored {user_to_ignore}.\r\n")
                    else:
                        self.update_message_text(f"{user_to_ignore} is already in your ignore list.\r\n")
                else:
                    self.update_message_text("Invalid usage. Usage: /ignore <nickname|hostmask>\r\n")
            case "unignore": #unignores a user
                user_to_unignore = user_input.split()[1]
                if user_to_unignore in self.irc_client.ignore_list:
                    self.irc_client.ignore_list.remove(user_to_unignore)
                    self.update_message_text(f"You've unignored {user_to_unignore}.\r\n")
                else: 
                    self.update_message_text(f"{user_to_unignore} is not in your ignore list.\r\n")
            case "sa": #sends to all channels
                message = ' '.join(user_input.split()[1:])
                for channel in self.irc_client.joined_channels:
                    self.irc_client._send_message(f'PRIVMSG {channel} :{message}')
                self.update_message_text(f'Message sent to all joined channels: {message}\r\n')
            case "friend":  # adds friend
                self.add_friend(user_input)
            case "friends":
                self.update_message_text(f"<Friends List>\r\n")
                for person in self.irc_client.friend_list:
                    self.update_message_text(f"{person}\r\n")
            case "unfriend": #removes friend
                unfriend_name = user_input.split()[1]
                if unfriend_name in self.irc_client.friend_list:
                    self.irc_client.friend_list.remove(unfriend_name)
                    self.irc_client.save_friend_list()
                    self.update_message_text(f"{unfriend_name} removed from friends.\r\n")
                else:
                    self.update_message_text(f"{unfriend_name} is not in your friend list.\r\n")
            case "CTCP":
                if len(args) < 3:
                    self.update_message_text("Invalid usage. Usage: /CTCP <nickname> <command> [parameters]\r\n")
                    return
                target = args[1]
                ctcp_command = args[2].upper()
                parameter = ' '.join(args[3:]) if len(args) > 3 else None
                self.irc_client.send_ctcp_request(target, ctcp_command, parameter)
            case "banlist":
                channel = args[1] if len(args) > 1 else self.irc_client.current_channel
                if channel:
                    self.irc_client._send_message(f'MODE {channel} +b')
            case "motd":
                self.irc_client._send_message('MOTD')
            case "time":
                self.irc_client._send_message('TIME')
            case "list":
                self.irc_client._send_message('LIST')
            case "mac":
                self.handle_mac_command(args)
            case "syscowsay":
                self.handle_syscowsay_command(args)
            case "sysfortune":
                self.handle_sysfortune_command(args[1:])
            case "roll":  
                self.dice_roll(args)
            case "exec":
                self._handle_exec_command(args)
            case "mode":
                self.handle_mode_command(args)
            case "notice":
                self.handle_notice_command(args)
            case "invite":
                self.handle_invite_command(args)
            case "kick":
                self.handle_kick_command(args)
            case "fortune":
                file_name_arg = args[1] if len(args) > 1 else None
                self.fortune(file_name_arg)
            case "cowsay":
                self.handle_cowsay_command(args)
            case _:
                self.update_message_text(f"Unkown Command! Type '/help' for help.\r\n")
        self.input_entry.delete(0, tk.END)

    def add_friend(self, user_input):
        user_input_split = user_input.split()
        
        # Check if the user has provided a friend's name to add
        if len(user_input_split) < 2:
            self.update_message_text("Usage: /friend <person> to add a friend.\r\n")
            self.update_message_text("Use /friends to list all friends.\r\n")
            return
        
        friend_name = user_input_split[1]
        
        # Check if friend_name is not empty or None
        if not friend_name:
            self.update_message_text("Friend name cannot be empty.\r\n")
            return
        
        if friend_name not in self.irc_client.friend_list:
            self.irc_client.friend_list.append(friend_name)
            self.irc_client.save_friend_list()
            self.update_message_text(f"{friend_name} added to friends.\r\n")
        else:
            self.update_message_text(f"{friend_name} is already in your friend list.\r\n")

    def handle_cowsay_command(self, args):
        script_directory = os.path.dirname(os.path.abspath(__file__))

        if len(args) > 1:
            file_name_arg = args[1]
            # Construct the potential file path using the absolute path
            potential_path = os.path.join(script_directory, "Fortune Lists", f"{file_name_arg}.txt")

            # Check if the provided argument corresponds to a valid fortune file
            if os.path.exists(potential_path):
                self.fortune_cowsay(file_name_arg)
            else:
                # If not a valid file name, consider the rest of the arguments as a custom message
                custom_message = ' '.join(args[1:])
                self.cowsay_custom_message(custom_message)
        else:
            self.fortune_cowsay()

    def navigate_history(self, event):
        """Navigate through the input history using the arrow keys."""
        if event.keysym == 'Up':
            # Move to the previous history entry
            self.history_position = max(0, self.history_position - 1)
            self.show_history_entry()
        elif event.keysym == 'Down':
            # Move to the next history entry
            self.history_position = min(len(self.input_history) - 1, self.history_position + 1)
            self.show_history_entry()

    def show_history_entry(self):
        """Display the history entry at the current position in the input field."""
        if 0 <= self.history_position < len(self.input_history):
            entry = self.input_history[self.history_position]
            self.input_entry.delete(0, tk.END)  # Clear current input
            self.input_entry.insert(tk.END, entry)  # Insert the history entry

    def cowsay(self, message):
        """Formats the given message in a 'cowsay' format."""

        # Find the longest line in the input message to determine the maximum width.
        max_line_length = max(len(line) for line in message.split('\n'))
        # Adjust for the added spaces and border characters
        adjusted_width = max_line_length - 4  # 2 for initial and end space + 2 for border characters

        # Manually split lines to check for one-word lines.
        raw_lines = message.split('\n')
        wrapped_lines = []
        for line in raw_lines:
            if len(line.split()) == 1:  # Single word line
                wrapped_lines.append(line)
            else:
                wrapped_lines.extend(textwrap.wrap(line, adjusted_width))

        # Format lines using cowsay style.
        if len(wrapped_lines) == 1:
            # Special case: single line message.
            combined_message = f"/ {wrapped_lines[0].ljust(adjusted_width)} \\"
        else:
            lines = [f"/ {wrapped_lines[0].ljust(adjusted_width)} \\"]
            for line in wrapped_lines[1:-1]:
                lines.append(f"| {line.ljust(adjusted_width)} |")
            lines.append(f"\\ {wrapped_lines[-1].ljust(adjusted_width)} /")
            combined_message = '\n'.join(lines)

        # Find the longest line again (after formatting) to adjust the borders accordingly.
        max_line_length = max(len(line) for line in combined_message.split('\n'))

        top_border = ' ' + '_' * (max_line_length - 2)
        
        # Set the bottom border to match the max line length
        bottom_border = ' ' + '-' * (max_line_length - 2)

        cow = """
       \\   ^__^
        \\  (oo)\\_______
           (__)\\       )\\/\\
               ||----w |
               ||     ||"""

        return f"{top_border}\n{combined_message}\n{bottom_border}{cow}"

    def wrap_text(self, text, width=100):
        """Dont spam that channel"""
        return textwrap.fill(text, width)

    def get_fortune_file(self, file_name=None):
        script_directory = os.path.dirname(os.path.abspath(__file__))
        fortune_directory = os.path.join(script_directory, "Fortune Lists")
        
        if file_name:
            return os.path.join(fortune_directory, file_name + ".txt")
        
        fortune_files = [os.path.join(fortune_directory, f) for f in os.listdir(fortune_directory) if f.endswith('.txt')]
        return random.choice(fortune_files)

    def fortune_cowsay(self, file_name=None):
        file_name = self.get_fortune_file(file_name)
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')

        with open(file_name, 'r', encoding='utf-8') as f:
            fortunes = f.read().strip().split('%')
            chosen_fortune = random.choice(fortunes).strip()

        wrapped_fortune_text = self.wrap_text(chosen_fortune)
        cowsay_fortune = self.cowsay(wrapped_fortune_text)
        for line in cowsay_fortune.split('\n'):
            self.irc_client._send_message(f'PRIVMSG {self.irc_client.current_channel} :{line}')
            self.update_message_text(line + "\r\n")
            time.sleep(0.4)

    def cowsay_custom_message(self, message):
        """Wrap a custom message using the cowsay format."""
        wrapped_message = self.wrap_text(message)
        cowsay_output = self.cowsay(wrapped_message)
        
        for line in cowsay_output.split('\n'):
            self.irc_client._send_message(f'PRIVMSG {self.irc_client.current_channel} :{line}')
            self.update_message_text(line + "\r\n")
            time.sleep(0.4)

    def fortune(self, file_name=None):
        """Choose a random fortune from one of the lists"""
        file_name = self.get_fortune_file(file_name)

        with open(file_name, 'r', encoding='utf-8') as f:  # Notice the encoding parameter
            fortunes = f.read().strip().split('%')
            chosen_fortune = random.choice(fortunes).strip()

        for line in chosen_fortune.split('\n'):
            self.irc_client._send_message(f'PRIVMSG {self.irc_client.current_channel} :{line}')
            self.update_message_text(line + "\r\n")
            time.sleep(0.4)

    def dice_roll(self, args):
        # Default to d20 if no arguments are provided
        die_type = "d20" if len(args) < 2 else args[1].lower()
        
        # Map the die type to its maximum value
        dice_map = {
            "d4": 4,
            "d6": 6,
            "d8": 8,
            "d10": 10,
            "d100": 100,
            "d12": 12,
            "d20": 20,
            "d120": 120
        }

        # Check if the die_type is in the predefined dice_map or if it's a custom dice size (e.g., d25, d30, etc.)
        if die_type in dice_map:
            max_value = dice_map[die_type]
        elif re.match(r'd(\d+)', die_type):
            max_value = int(re.match(r'd(\d+)', die_type).group(1))
        else:
            self.update_message_text(f"Invalid die type: {die_type}.\r\n")
            return

        number = random.randint(1, max_value)
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')

        action_message = f"\x01ACTION rolled a {number} on a {die_type}\x01"
        display_message = f"{timestamp} * {self.irc_client.nickname} rolled a {number} on a {die_type}"

        self.update_message_text(display_message + "\r\n")
        self.irc_client._send_message(f'PRIVMSG {self.irc_client.current_channel} :{action_message}')

    def handle_who_command(self, args):
        """
        Handle the WHO command entered by the user.
        """
        if not args:
            # General WHO
            self.irc_client._send_message('WHO')
        elif args[0].startswith('#'):
            # WHO on a specific channel
            channel = args[0]
            self.irc_client._send_message(f'WHO {channel}')
        else:
            # WHO with mask or user host
            mask = args[0]
            self.irc_client._send_message(f'WHO {mask}')

    def handle_kick_command(self, args):
        if len(args) < 3:
            self.update_message_text("Usage: /kick <user> <channel> [reason]\r\n")
            return
        user = args[1]
        channel = args[2]
        reason = ' '.join(args[3:]) if len(args) > 3 else None
        kick_message = f'KICK {channel} {user}' + (f' :{reason}' if reason else '')
        self.irc_client._send_message(kick_message)
        self.update_message_text(f"Kicked {user} from {channel} for {reason}\r\n")

    def handle_invite_command(self, args):
        if len(args) < 3:
            self.update_message_text("Usage: /invite <user> <channel>\r\n")
            return
        user = args[1]
        channel = args[2]
        self.irc_client._send_message(f'INVITE {user} {channel}\r\n')
        self.update_message_text(f"Invited {user} to {channel}\r\n")

    def handle_mode_command(self, args):
        if len(args) < 3:
            self.update_message_text("Usage: /mode [channel] <target> <mode>\r\n")
            return

        # Check if a channel is explicitly specified
        if args[1].startswith("#"):
            channel = args[1]
            target = args[2]
            mode = args[3]
        else:  # If no channel is specified, use the current channel
            channel = self.irc_client.current_channel
            target = args[1]
            mode = args[2]

        # Send the MODE command to the IRC server
        self.irc_client._send_message(f'MODE {channel} {mode} {target}')
        self.update_message_text(f"Attempting to set mode {mode} for {target} in {channel}\r\n")

    def handle_notice_command(self, args):
        if len(args) < 3:
            self.update_message_text("Usage: /notice <target> <message>\r\n")
            return
        target = args[1]
        message = ' '.join(args[2:])
        self.irc_client._send_message(f'NOTICE {target} :{message}\r\n')
        self.update_message_text(f"Sent NOTICE to {target}: {message}\r\n")

    def _handle_exec_command(self, args):
        """
        Executes an OS command and sends its output to the current IRC channel line by line.
        """
        os_command = ' '.join(args[1:])
        try:
            # Run the command and capture its output
            result = subprocess.run(os_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output_lines = (result.stdout + result.stderr).splitlines()
            
            for line in filter(lambda l: l.strip(), output_lines):  # Skip empty or whitespace-only lines
                # Send the line to the current IRC channel
                self.irc_client._send_message(f'PRIVMSG {self.irc_client.current_channel} :{line}')
                # Update the GUI with the message
                self.update_message_text(line + "\r\n")
                time.sleep(0.5)

        except Exception as e:
            self.update_message_text(f"Error executing command: {e}\r\n")

    def handle_mac_command(self, args):
        if len(args) < 2:
            available_macros = ", ".join(self.ASCII_ART_MACROS.keys())
            self.update_message_text(f"Available ASCII art macros: {available_macros}\r\n")
            self.update_message_text("Usage: /mac <macro_name>\r\n")
            return

        macro_name = args[1]
        if macro_name in self.ASCII_ART_MACROS:
            current_time = datetime.datetime.now().strftime('%H:%M:%S')
            for line in self.ASCII_ART_MACROS[macro_name].splitlines():
                self.irc_client._send_message(f'PRIVMSG {self.irc_client.current_channel} :{line}')
                time.sleep(0.5)
                formatted_line = f"[{current_time}]  <{self.irc_client.nickname}> {line}\r\n"
                self.update_message_text(formatted_line)
        else:
            self.update_message_text(f"Unknown ASCII art macro: {macro_name}. Type '/mac' to see available macros.\r\n")

    def handle_syscowsay_command(self, args):
        try:
            # Determine if we're dealing with a category, custom message, or default
            if len(args) == 1:
                message = self.cowsay_fortune()  # Default random fortune
            elif len(args) == 2 and self.is_fortune_category(args[1]):
                message = self.cowsay_fortune(category=args[1])  # Specific fortune category
            else:
                message = self.cowsay_custom(' '.join(args[1:]))  # Custom message

            # Send the message to the channel
            for line in message.split("\n"):
                if not line.strip():
                    continue

                self.irc_client._send_message(f'PRIVMSG {self.irc_client.current_channel} :{line}')
                time.sleep(0.3)

                current_time = datetime.datetime.now().strftime('%H:%M:%S')
                formatted_line = f"[{current_time}]  <{self.irc_client.nickname}> {line}"
                self.update_message_text(formatted_line + "\r\n")
        except Exception as e:
            self.update_message_text(f"Error executing cowsay: {e}\r\n")

    def is_fortune_category(self, category):
        try:
            # Attempt to get a fortune for the category; if it fails, it's not a valid category
            subprocess.check_output(f"fortune {category}", shell=True)
            return True
        except:
            return False

    def cowsay_fortune(self, category=None):
        cow_mode = {
            1: "-b",
            2: "-d",
            3: "",  # default
            4: "-g",
            5: "-p",
            6: "-s",
            7: "-t",
            8: "-w",
            9: "-y"
        }

        rng = random.randint(1, 9)

        # Getting the list of cowfiles
        result = subprocess.run(['cowsay', '-l'], capture_output=True, text=True)
        cowfiles = result.stdout.split()[1:]
        cowfile = random.choice(cowfiles)

        # Running the fortune with cowsay command
        if category:
            fortune_result = subprocess.run(['fortune', '-s', category], capture_output=True, text=True)
        else:
            fortune_result = subprocess.run(['fortune', '-s'], capture_output=True, text=True)
        
        cowsay_command = ['cowsay', '-W', '100', cow_mode[rng], '-f', cowfile]
        print(f"DEBUG: Running cowsay command: {fortune_result} {' '.join(cowsay_command)}")
        cowsay_result = subprocess.run(cowsay_command, input=fortune_result.stdout, capture_output=True, text=True)

        return cowsay_result.stdout

    def cowsay_custom(self, message):
        # Just a simple cowsay with the provided message
        cowsay_result = subprocess.run(['cowsay', '-W', '100', '-f', 'flaming-sheep'], input=message, capture_output=True, text=True)
        return cowsay_result.stdout

    def handle_sysfortune_command(self, args=[]):
        try:
            # Build the fortune command with the given arguments.
            # We use shlex.quote to safely escape any argument passed to the command.
            fortune_args = ' '.join(shlex.quote(arg) for arg in args)
            command = f"fortune -as {fortune_args}"
            result = subprocess.check_output(command, shell=True).decode('utf-8')
            
            for line in result.split("\n"):
                if not line.strip():
                    continue
                self.irc_client._send_message(f'PRIVMSG {self.irc_client.current_channel} :{line}')
                current_time = datetime.datetime.now().strftime('%H:%M:%S')
                formatted_line = f"[{current_time}]  <{self.irc_client.nickname}> {line}"
                self.update_message_text(formatted_line + "\r\n")
        except Exception as e:
            self.update_message_text(f"Error executing fortune: {e}\r\n")

    def display_help(self):
        # === General & Utility Commands ===
        self.update_message_text("=== General & Utility Commands ===\r\n")
        self.update_message_text(f'/help - Display this help menu\r\n')
        self.update_message_text(f'/clear - Clear the chat window\r\n')
        self.update_message_text(f'Exit button - Send /quit and close client\r\n')
        self.update_message_text(f'Tab - Auto-complete nicknames\r\n')
        self.update_message_text(f'/mac to see available macros /mac <macroname> sends that macro\r\n')

        # === Connection & Server Commands ===
        self.update_message_text("\r\n=== Connection & Server Commands ===\r\n")
        self.update_message_text(f'/connect <server> <port> - Connect to a specific server\r\n')
        self.update_message_text(f'/disconnect - Disconnect from the server\r\n')
        self.update_message_text(f'/reconnect - Reconnect to the last server\r\n')
        self.update_message_text(f'/quit - Close connection and exit client\r\n')
        self.update_message_text(f'/ping - Ping the connected server or /ping <usernick> to ping a specific user\r\n')
        self.update_message_text(f'/who - Shows who is on the channel or server\r\n')
        self.update_message_text(f'/motd - View Message of the Day\r\n')
        self.update_message_text(f'/time - Check server time\r\n')
        self.update_message_text(f'/list - List available channels\r\n')
        self.update_message_text(f'/names - reloads the user list\r\n')

        # === Channel & Message Management ===
        self.update_message_text("\r\n=== Channel & Message Management ===\r\n")
        self.update_message_text(f'/join <channel> - Join a channel\r\n')
        self.update_message_text(f'/part <channel> - Leave a channel\r\n')
        self.update_message_text(f'/sw <channel> - Switch to a given channel. Clicking on channels also switches\r\n')
        self.update_message_text(f'/msg <nickname> <message> - Send a direct message, e.g., /msg NickServ IDENTIFY\r\n')
        self.update_message_text(f'/query <nickname> - Open a DM with a user\r\n')
        self.update_message_text(f'/cq <nickname> - Close the DM with a user\r\n')
        self.update_message_text(f'/sa - Send a message to all joined channels\r\n')
        self.update_message_text(f'/notice - Sends a notice message\r\n')
        self.update_message_text(f'/invite - Invites a user to a channel\r\n')
        self.update_message_text(f'/kick - Kicks a user from a channel\r\n')
        self.update_message_text(f'/banlist - shows the banlist for the channel.')

        # === User & Interaction Commands ===
        self.update_message_text("\r\n=== User & Interaction Commands ===\r\n")
        self.update_message_text(f'/whois <nickname> - Whois a specific user\r\n')
        self.update_message_text(f'/ignore <nickname> & /unignore <nickname> - Ignore/Unignore a user\r\n')
        self.update_message_text(f'/friend <nickname> - Add a user to your friend list\r\n')
        self.update_message_text(f'/friends will show the friends list\r\n')
        self.update_message_text(f'/unfriend <nickname> - Remove a user from your friend list\r\n')
        self.update_message_text(f'/away to set yourself as away\r\n')
        self.update_message_text(f'/back to return (removes AWAY status)\r\n')
        self.update_message_text(f'/mode - Sets or removes user/channel modes\r\n')

        # === Advanced & Fun Commands ===
        self.update_message_text("\r\n=== Advanced & Fun Commands ===\r\n")
        self.update_message_text(f'/CTCP <nickname> <command> [parameters] - CTCP command, e.g., /CTCP Rudie CLIENTINFO\r\n')
        self.update_message_text(f'/syscowsay to generate and send a cowsay to the channel\r\n')
        self.update_message_text(f'/cowsay to generate and send a cowsay to the channel\r\n')
        self.update_message_text(f'/sysfortune to tell fortune. /sysfortune <library> gives a fortune from that library\r\n')
        self.update_message_text(f'/fortune to tell fortune. /fortune <library> gives a fortune from that library\r\n')
        self.update_message_text(f'/exec command will run the following command on your machine and output to the channel youre in\r\n')
        self.update_message_text(f'Example: /exec ping -c 1 www.google.com\r\n')
        self.update_message_text(f'Note: syscowsay & sysfortune will only work if you have both installed on your LINUX system\r\n')
        self.update_message_text(f'Note: cowsay & fortune are internal within the client and will pull from the Fortune Lists folder\r\n')

    def format_message_for_display(self, message):
        #print("Original Message:", message)
        
        # Remove color codes
        message_no_colors = re.sub(r'\x03(\d{1,2}(,\d{1,2})?)?', '', message)
        #print("Message without colors:", message_no_colors)
        
        # Define patterns for bold, italic, and reset
        bold_pattern = r'\x02(.*?)(?:\x02|\x0F|$)'
        italic_pattern = r'\x1D(.*?)(?:\x1D|\x0F|$)'
        
        # Function to extract ranges from matches
        def get_ranges(pattern, msg):
            ranges = []
            for match in re.finditer(pattern, msg):
                start = match.start()
                end = match.end()
                for group in match.groups():
                    if group is not None:
                        end = start + len(group) + 2  
                        ranges.append((start, end - 1))
                        break
            return ranges

        bold_ranges = get_ranges(bold_pattern, message_no_colors)
        #print("Bold Ranges:", bold_ranges)
        
        italic_ranges = get_ranges(italic_pattern, message_no_colors)
        #print("Italic Ranges:", italic_ranges)

        # For bold-italic, we'll look for overlapping ranges
        bold_italic_ranges = set([(b_start, b_end) for b_start, b_end in bold_ranges 
                                  for i_start, i_end in italic_ranges 
                                  if b_start <= i_start and b_end >= i_end])
        #print("Bold-Italic Ranges:", bold_italic_ranges)
        
        # Remove the formatting characters to get the formatted message
        formatted_message = re.sub(r'[\x02\x1D\x0F]', '', message_no_colors)
        #print("Formatted Message:", formatted_message)

        return formatted_message, bold_ranges, italic_ranges, list(bold_italic_ranges)

    def display_dm_messages(self, user):
        if user in self.irc_client.dm_messages:
            new_messages = self.irc_client.dm_messages[user]

            # Check if there are any new messages
            if not new_messages:
                return

            self.message_text.config(state=tk.NORMAL)  # Assuming you're using a Tkinter Text widget

            # Delete existing messages to make way for the updated messages with formatting
            self.message_text.delete(1.0, tk.END)

            for message in new_messages:
                # Apply the message formatting
                formatted_text, bold_ranges, italic_ranges, bold_italic_ranges = self.format_message_for_display(message)

                # Remove trailing '\r' characters from each line
                cleaned_formatted_text = "\n".join([line.rstrip('\r') for line in formatted_text.split('\n')])

                start_insert_index = self.message_text.index(tk.END)

                self.message_text.insert(tk.END, cleaned_formatted_text)

                # Apply the formatting tags
                self._apply_formatting(cleaned_formatted_text, bold_ranges, italic_ranges, bold_italic_ranges, start_insert_index)

            self.message_text.see(tk.END)  # Move scrollbar to the bottom
            self.message_text.config(state=tk.DISABLED)  # Disable editing again

    def update_server_feedback_text(self, message):
        """
        This updates the server feedback, it takes into account ascii.
        """
        def update_text(message_to_update):
            message_to_update = message_to_update.replace('\r', '')
            formatted_message, bold_ranges, italic_ranges, bold_italic_ranges = self.format_message_for_display(message_to_update)

            # Insert the message into the Text widget
            self.server_feedback_text.config(state=tk.NORMAL)
            start_index = self.server_feedback_text.index(tk.END)  # Get the starting index for this message
            self.server_feedback_text.insert(tk.END, formatted_message + "\n", "server_feedback")
            self.server_feedback_text.config(state=tk.DISABLED)

            # Apply bold formatting
            for start, end in bold_ranges:
                start_bold_index = f"{start_index}+{start}c"
                end_bold_index = f"{start_index}+{end}c"
                self.server_feedback_text.tag_add("bold", start_bold_index, end_bold_index)

            # Apply italic formatting
            for start, end in italic_ranges:
                start_italic_index = f"{start_index}+{start}c"
                end_italic_index = f"{start_index}+{end}c"
                self.server_feedback_text.tag_add("italic", start_italic_index, end_italic_index)

            # Apply bold-italic formatting
            for start, end in bold_italic_ranges:
                start_bold_italic_index = f"{start_index}+{start}c"
                end_bold_italic_index = f"{start_index}+{end}c"
                self.server_feedback_text.tag_add("bold_italic", start_bold_italic_index, end_bold_italic_index)

            # Ensure the message is visible in the widget
            self.server_feedback_text.see(tk.END)
            self.server_feedback_text.tag_configure("server_feedback", foreground="#7882ff")  # Make the server output blue

        # Schedule the update_text function to be run in the main thread
        self.root.after(0, lambda: update_text(message))

    def update_user_list(self, channel):
        """
        This is responsible for updating the user list within the GUI.
        """
        current_position = self.user_list_text.yview()
        if channel in self.irc_client.user_list:
            users = self.irc_client.user_list[channel]

            # Sort users based on symbols @, +, and none
            users_sorted = sorted(users, key=lambda user: (not user.startswith('@'), not user.startswith('+'), user))

            user_list_text = "\n".join(users_sorted)
        else:
            user_list_text = "No users in the channel."

        self.user_list_text.config(state=tk.NORMAL)
        self.user_list_text.delete(1.0, tk.END)
        self.user_list_text.insert(tk.END, user_list_text)
        self.user_list_text.config(state=tk.DISABLED)
        self.user_list_text.yview_moveto(current_position[0])

    def update_joined_channels_list(self, channel):
        """
        This handles all the fancy tags for channel notifications, mentions, etc.
        """
        # Create tags for highlighting
        self.joined_channels_text.tag_configure("selected", background="#2375b3")
        self.joined_channels_text.tag_configure("mentioned", background="red")
        self.joined_channels_text.tag_configure("activity", background="green")
        self.joined_channels_text.tag_configure("green_text", foreground="#39ff14")

        # Set certain tags to raise over others.
        self.joined_channels_text.tag_raise("mentioned")
        self.joined_channels_text.tag_raise("selected")

        # Combine channels and DM users for display
        all_items = self.irc_client.joined_channels + [f"DM: {user}" for user in self.irc_client.dm_users]
        all_items_text = "\n".join(all_items)

        self.joined_channels_text.config(state=tk.NORMAL)
        self.joined_channels_text.delete(1.0, tk.END)
        self.joined_channels_text.insert(tk.END, all_items_text)

        # Iterate through the lines in the joined_channels_text widget
        for idx, line in enumerate(self.joined_channels_text.get("1.0", tk.END).splitlines()):
            start_idx = f"{idx + 1}.0"
            end_idx = f"{idx + 1}.end"

            is_selected = (line == self.irc_client.current_channel) or (line == f"DM: {self.irc_client.current_channel}")

            # If the line is selected, apply the "selected" tag and remove all other tags
            if is_selected:
                for tag in ["activity", "mentioned"]:
                    self.joined_channels_text.tag_remove(tag, start_idx, end_idx)
                self.joined_channels_text.tag_add("selected", start_idx, end_idx)
                self.update_window_title(self.irc_client.nickname, self.irc_client.current_channel)
                continue  # Skip to next iteration since 'selected' takes precedence

            # Check if the line is mentioned
            if line in self.channels_with_mentions:
                self.joined_channels_text.tag_add("mentioned", start_idx, end_idx)

            # If the line has activity and is not selected, apply the "activity" tag
            if line in self.channels_with_activity and not is_selected:
                self.joined_channels_text.tag_add("activity", start_idx, end_idx)

        ascii_art = """
        .-.-.
       (_\\|/_)
       ( /|\\ )    
        '-'-'`-._"""

        # Add the ASCII art at the end
        self.joined_channels_text.insert(tk.END, "\n" + ascii_art)
        start_index = self.joined_channels_text.index(tk.END + "- {} lines linestart".format(ascii_art.count("\n") + 1))
        end_index = self.joined_channels_text.index(tk.END)
        self.joined_channels_text.tag_add("green_text", start_index, end_index)

        self.joined_channels_text.config(state=tk.DISABLED)

    def handle_exit(self):
        """
        Gracefully exits
        """
        self.irc_client.save_ignore_list()
        self.irc_client.save_friend_list()
        self.irc_client.exit_event.set() 
        
        # Check if the socket is still open before attempting to shut it down
        if hasattr(self.irc_client, 'irc'):
            try:
                self.irc_client._send_message('QUIT')
                self.irc_client.irc.shutdown(socket.SHUT_RDWR)
            except OSError as e:
                if e.errno == 9:  # Bad file descriptor
                    print("Socket already closed.")
                else:
                    print(f"Unexpected error during socket shutdown: {e}")
        
        self.root.destroy()

    def handle_tab_complete(self, event):
        """
        Tab complete with cycling through possible matches.
        """
        # Get the current input in the input entry field
        user_input = self.input_entry.get()
        cursor_pos = self.input_entry.index(tk.INSERT)

        # Find the partial nick before the cursor position
        partial_nick = ''
        for i in range(cursor_pos - 1, -1, -1):
            char = user_input[i]
            if not char.isalnum() and char not in "_-^[]{}\\`|":
                break
            partial_nick = char + partial_nick

        # Cancel any previous timers
        if hasattr(self, 'tab_completion_timer'):
            self.root.after_cancel(self.tab_completion_timer)

        # Get the user list for the current channel
        current_channel = self.irc_client.current_channel
        if current_channel in self.irc_client.user_list:
            user_list = self.irc_client.user_list[current_channel]
        else:
            return

        # Remove @ and + symbols from nicknames
        user_list_cleaned = [nick.lstrip('@+') for nick in user_list]

        # Initialize or update completions list
        if not hasattr(self, 'tab_complete_completions') or not hasattr(self, 'last_tab_time') or (time.time() - self.last_tab_time) > 1.0:
            self.tab_complete_completions = [nick for nick in user_list_cleaned if nick.startswith(partial_nick)]
            self.tab_complete_index = 0

        # Update the time of the last tab press
        self.last_tab_time = time.time()

        if self.tab_complete_completions:
            # Fetch the next completion
            completed_nick = self.tab_complete_completions[self.tab_complete_index]
            remaining_text = user_input[cursor_pos:]
            completed_text = user_input[:cursor_pos - len(partial_nick)] + completed_nick + remaining_text
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, completed_text)
            # Cycle to the next completion
            self.tab_complete_index = (self.tab_complete_index + 1) % len(self.tab_complete_completions)

        # Set up a timer to append ": " after half a second if no more tab presses
        self.tab_completion_timer = self.root.after(300, self.append_colon_to_nick)

        # Prevent default behavior of the Tab key
        return 'break'

    def append_colon_to_nick(self):
        current_text = self.input_entry.get()
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, current_text + ": ")

    def update_window_title(self, nickname, channel_name):
        """
        This provides some fancy feedback when switching channels. 
        """
        title_parts = []
        if nickname:
            title_parts.append(nickname)
        if channel_name:
            title_parts.append(channel_name)
        if title_parts:
            self.root.title("RudeChat " + " | ".join(title_parts))
        else:
            self.root.title("RudeChat ")

        self.nickname_label.config(font=("Hack", 9, "bold italic"), text=f"{channel_name} $ {nickname} $> ")

    def update_message_text(self, text, sender=None, is_dm=False):
        """
        This method is responsible for updating the message text, it adds tags for the users nick, colors the other users nicks, and chooses the color for the main text. 
        """
        def _update_message_text():
            self.message_text.config(state=tk.NORMAL)
                
            # Process the message for bold, italic, and bold-italic formatting
            formatted_text, bold_ranges, italic_ranges, bold_italic_ranges = self.format_message_for_display(text)
                
            # Remove trailing '\r' characters from each line
            cleaned_formatted_text = "\n".join([line.rstrip('\r') for line in formatted_text.split('\n')])

            start_insert_index = self.message_text.index(tk.END)

            self.message_text.insert(tk.END, cleaned_formatted_text)
            
            self._apply_formatting(cleaned_formatted_text, bold_ranges, italic_ranges, bold_italic_ranges, start_insert_index)
                
            self.message_text.config(state=tk.DISABLED)
            self.message_text.see(tk.END)

        self.root.after(0, _update_message_text)
        
    def _apply_formatting(self, cleaned_formatted_text, bold_ranges, italic_ranges, bold_italic_ranges, start_insert_index):
        # Process nicknames and color them
        start_idx = "1.0"
        while True:
            # Find the opening '<'
            start_idx = self.message_text.search('<', start_idx, stopindex=tk.END)
            if not start_idx:
                break
            # Find the closing '>' ensuring no newlines between
            end_idx = self.message_text.search('>', start_idx, f"{start_idx} lineend")
            if end_idx:
                end_idx = f"{end_idx}+1c"  # Include the '>' character
                # Extract the nickname
                nickname = self.message_text.get(start_idx + "+1c", end_idx + "-1c")

                # If nickname doesn't have an assigned color, generate one
                if nickname not in self.nickname_colors:
                    self.nickname_colors[nickname] = self.generate_random_color()
                nickname_color = self.nickname_colors[nickname]

                # If it's the main user's nickname, set color to green
                if nickname == self.irc_client.nickname:
                    nickname_color = "#39ff14"

                self.message_text.tag_configure(f"nickname_{nickname}", foreground=nickname_color)
                self.message_text.tag_add(f"nickname_{nickname}", start_idx, end_idx)
                start_idx = end_idx
            else:
                start_idx = f"{start_idx}+1c"

        main_user_name = self.irc_client.nickname
        start_idx = "1.0"
        while True:
            start_idx = self.message_text.search(main_user_name, start_idx, stopindex=tk.END)
            if not start_idx:
                break
            end_idx = f"{start_idx}+{len(main_user_name)}c"
            self.message_text.tag_configure("main_user_color", foreground="#39ff14")
            self.message_text.tag_add("main_user_color", start_idx, end_idx)
            start_idx = end_idx

            # Check if the start index has reached the end of the text
            if start_idx == tk.END:
                break

        urls = self.find_urls(cleaned_formatted_text)
        for index, url in enumerate(urls):
            # Mark found URLs in the text to avoid them being treated as channels
            cleaned_formatted_text = cleaned_formatted_text.replace(url, f"<URL>{url}</URL>")
            start_idx = "1.0"
            while True:
                start_idx = self.message_text.search(url, start_idx, tk.END)
                if not start_idx:
                    break
                end_idx = f"{start_idx}+{len(url)}c"
                
                # Create a unique tag for each URL
                url_tag = f"url_{index}_{start_idx}"  # Make it unique per occurrence
                
                self.message_text.tag_add(url_tag, start_idx, end_idx)
                self.message_text.tag_configure(url_tag, foreground="blue", underline=1)
                
                # Bind the URL to the open_url method using partial
                self.message_text.tag_bind(url_tag, "<Button-1>", partial(self.open_url, url=url))
                
                # Move the start index to after the current found URL to continue the search
                start_idx = end_idx

        channels = self.find_channels(cleaned_formatted_text)
        for channel in channels:
            start_idx = "1.0"
            while True:
                # Search for the channel from the current start index
                start_idx = self.message_text.search(channel, start_idx, stopindex=tk.END)
                if not start_idx:
                    break
                end_idx = f"{start_idx}+{len(channel)}c"
                
                # Ensure we're not treating marked URLs as channels
                if "<URL>" not in self.message_text.get(start_idx, end_idx) and "</URL>" not in self.message_text.get(start_idx, end_idx):
                    tag_name = f"channel_{channel}"  # Create a unique tag for the channel
                    self.message_text.tag_add(tag_name, start_idx, end_idx)
                    self.message_text.tag_configure(tag_name, foreground="cyan", underline=1)
                    self.message_text.tag_bind(tag_name, "<Button-1>", lambda e, ch=channel: self.join_channel(ch))
                
                # Move the start index to after the current found channel to continue the search
                start_idx = end_idx

        # Apply bold formatting
        for start, end in bold_ranges:
            if (start, end) not in bold_italic_ranges:  
                start_idx = f"{start_insert_index}+{start}c"
                end_idx = f"{start_insert_index}+{end}c"
                self.message_text.tag_add("bold", start_idx, end_idx)
                self.message_text.tag_configure("bold", font=self.bold_font)

        # Apply italic formatting
        for start, end in italic_ranges:
            if (start, end) not in bold_italic_ranges:  
                start_idx = f"{start_insert_index}+{start}c"
                end_idx = f"{start_insert_index}+{end}c"
                self.message_text.tag_add("italic", start_idx, end_idx)
                self.message_text.tag_configure("italic", font=self.italic_font)

        # Apply bold-italic formatting
        for start, end in bold_italic_ranges:
            start_idx = f"{start_insert_index}+{start}c"
            end_idx = f"{start_insert_index}+{end}c"
            self.message_text.tag_add("bold_italic", start_idx, end_idx)
            self.message_text.tag_configure("bold_italic", font=self.bold_italic_font)

        # Adjusting tag priorities at the end
        if self.message_text.tag_ranges("bold_italic"):
            self.message_text.tag_raise("bold_italic")
        if self.message_text.tag_ranges("bold"):
            self.message_text.tag_raise("bold")
        if self.message_text.tag_ranges("italic"):
            self.message_text.tag_raise("italic")

    def display_channel_messages(self):
        """
        This is responsible for showing the channels scrollback / history
        """
        channel = self.irc_client.current_channel
        if channel in self.irc_client.channel_messages:
            messages = self.irc_client.channel_messages[channel]
            text = ''
            for message_data in messages:
                if len(message_data) == 3:
                    timestamp, sender, message = message_data
                    # Check if the message is already formatted with the sender's nickname for CTCP ACTION
                    if message.startswith('* '):
                        text += f'{timestamp} {message}\n'
                    else:
                        text += f'{timestamp} <{sender}> {message}\n'
                else:  # Assuming the other format is (timestamp, formatted_message)
                    timestamp, formatted_message = message_data
                    text += f'{timestamp} {formatted_message}\n'
            self.update_message_text(text)
        else:
            self.update_message_text('No messages to display in the current channel.\n')
        self.update_user_list(channel)

    def display_message_in_chat(self, message):
        """
        Special method for showing nick changes, yellow.
        """
        def _append_message_to_chat():
            self.message_text.config(state=tk.NORMAL)
            self.message_text.insert(tk.END, message + "\n")
            self.message_text.config(state=tk.DISABLED)
            self.message_text.see(tk.END)
            
            # Apply a specific color (gold) for system messages (like nick changes)
            self.message_text.tag_configure("system_message", foreground="#FFD700")
            start_idx = self.message_text.search(message, "1.0", stopindex=tk.END)
            if start_idx:
                end_idx = f"{start_idx}+{len(message)}c"
                self.message_text.tag_add("system_message", start_idx, end_idx)

        self.root.after(0, _append_message_to_chat)

    def update_ban_list(self, channel, ban_info=None, end_message=None):
        """
        Update the GUI with ban list information or an end message.
        """
        def _update_ban_list():
            self.message_text.config(state=tk.NORMAL)
                
            if ban_info:
                # Append the ban information to the message text
                self.message_text.insert(tk.END, ban_info)
                
            if end_message:
                # Append the end of ban list message
                self.message_text.insert(tk.END, end_message)
                
            self.message_text.config(state=tk.DISABLED)
            self.message_text.see(tk.END)

        self.root.after(0, _update_ban_list)

    def find_urls(self, text):
        # A simple regex to detect URLs
        url_pattern = re.compile(r'(\w+://\S+|www\.\S+)')
        return url_pattern.findall(text)

    def open_url(self, event, url):
        import webbrowser
        webbrowser.open(url)

    def find_channels(self, text):
        # A regex to detect channel names starting with #
        channel_pattern = re.compile(r'(?i)(#+[^\s,]+)(?![.:/])')
        return channel_pattern.findall(text)

    def join_channel(self, channel):
        if channel not in self.irc_client.joined_channels:
            # Add the channel to the irc_client's list of channels
            self.irc_client.joined_channels.append(channel)
        self.irc_client._send_message(f"JOIN {channel}")
        # Update the GUI's list of channels
        self.update_joined_channels_list(channel)

    def start(self):
        """
        It's Alive!
        """
        self.root.mainloop()
        while not self.exit_event.is_set():
            self.root.update()
            if self.exit_event.is_set():
                break
            time.sleep(0.1)
        self.irc_client.receive_thread.join()
        self.root.quit()
