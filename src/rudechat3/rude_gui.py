#!/usr/bin/env python
from rudechat3.rude_client import RudeChatClient
from rudechat3.server_config_window import ServerConfigWindow
from rudechat3.rude_colours import RudeColours
from rudechat3.format_decoder import Attribute, decoder
from rudechat3.gui_config_window import GuiConfigWindow
from rudechat3.rude_popout import RudePopOut
from rudechat3.shared_imports import *
from rudechat3.rude_dragndrop import DragDropListbox
from rudechat3.nick_cleaner import clean_nicknames


class RudeGui:
    def __init__(self, master):
        self.master = master
        self.master.title("RudeChat")
        self.master.geometry("1100x900")
        self.master.configure(bg="black")
        self.script_directory = os.path.dirname(os.path.abspath(__file__))
        if sys.platform.startswith('win'):
            icon_path = os.path.join(self.script_directory, "rude.ico")
            self.master.iconbitmap(icon_path)
        else:
            icon_path = os.path.join(self.script_directory, "rude.png")
            img = PhotoImage(file=icon_path)
            self.master.iconphoto(True, img)

        self.create_tray_icon(icon_path)

        self.read_config()

        self.irc_colors = {
            '00': '#ffffff', '01': '#000000', '02': '#0000AA', '03': '#00AA00',
            '04': '#AA0000', '05': '#AA5500', '06': '#AA00AA', '07': '#FFAA00',
            '08': '#FFFF00', '09': '#00ff00', '10': '#00AAAA', '11': '#00FFAA',
            '12': '#2576ff', '13': '#ff00ff', '14': '#AAAAAA', '15': '#D3D3D3',
            '16': '#470000', '17': '#472100', '18': '#474700', '19': '#324700',
            '20': '#004700', '21': '#00472c', '22': '#004747', '23': '#002747',
            '24': '#000047', '25': '#2e0047', '26': '#470047', '27': '#47002a',
            '28': '#740000', '29': '#743a00', '30': '#747400', '31': '#517400',
            '32': '#007400', '33': '#007449', '34': '#007474', '35': '#004074',
            '36': '#000074', '37': '#4b0074', '38': '#740074', '39': '#740045',
            '40': '#b50000', '41': '#b56300', '42': '#b5b500', '43': '#7db500',
            '44': '#00b500', '45': '#00b571', '46': '#00b5b5', '47': '#0063b5',
            '48': '#0000b5', '49': '#7500b5', '50': '#b500b5', '51': '#b5006b',
            '52': '#ff0000', '53': '#ff8c00', '54': '#ffff00', '55': '#b2ff00',
            '56': '#00ff00', '57': '#00ffa0', '58': '#00ffff', '59': '#008cff',
            '60': '#0000ff', '61': '#a500ff', '62': '#ff00ff', '63': '#ff0098',
            '64': '#ff5959', '65': '#ffb459', '66': '#ffff71', '67': '#cfff60',
            '68': '#6fff6f', '69': '#65ffc9', '70': '#6dffff', '71': '#59b4ff',
            '72': '#5959ff', '73': '#c459ff', '74': '#ff66ff', '75': '#ff59bc', 
            '76': '#ff9c9c', '77': '#ffd39c', '78': '#ffff9c', '79': '#e2ff9c', 
            '80': '#9cff9c', '81': '#9cffdb', '82': '#9cffff', '83': '#9cd3ff', 
            '84': '#9c9cff', '85': '#dc9cff', '86': '#ff9cff', '87': '#ff94d3', 
            '88': '#000000', '89': '#131313', '90': '#282828', '91': '#363636', 
            '92': '#4d4d4d', '93': '#656565', '94': '#818181', '95': '#9f9f9f',
            '96': '#bcbcbc', '97': '#e2e2e2', '98': '#ffffff'
        }

        # Main frame
        self.frame = tk.Frame(self.master, bg="black")
        self.frame.grid(row=1, column=0, columnspan=2, sticky="nsew")

        # Initialize other instance variables
        self.channel_lists = {}
        self.nickname_colors = self.load_nickname_colors()
        self.clients = {}
        self.channel_topics = {}
        self.url_cache = {}
        self.tag_cache = {}
        self.entry_history = []
        self.popped_out_channels = []
        self.pop_out_windows = {}
        self.server_colors = {}
        self.history_index = 0
        self.last_selected_index = None
        self.previous_server_index = None
        self.url_pattern = re.compile(r'(\w+://[^\s()<>]*\([^\s()<>]*\)[^\s()<>]*(?<![.,;!?])|www\.[^\s()<>]*\([^\s()<>]*\)[^\s()<>]*(?<![.,;!?])|\w+://[^\s()<>]+(?<![.,;!?])|www\.[^\s()<>]+(?<![.,;!?]))')

        # Server and Topic Frame
        self.server_topic_frame = tk.Frame(self.master, bg="black")
        self.server_topic_frame.grid(row=0, column=0, columnspan=2, sticky='nsew')

        # Topic label
        self.current_topic = tk.StringVar(value="Topic: ")
        self.topic_label = tk.Label(self.server_topic_frame, textvariable=self.current_topic, padx=5, pady=1)
        self.topic_label.grid(row=1, column=0, sticky='w')
        self.topic_label.bind("<Enter>", self.show_topic_tooltip)
        self.topic_label.bind("<Leave>", self.hide_topic_tooltip)
        self.tooltip = None

        # Main text widget
        self.text_widget = ScrolledText(self.frame, wrap='word', cursor="arrow")
        self.text_widget.grid(row=0, column=0, sticky="nsew")
        self.show_startup_art()

        # List frames
        self.list_frame = tk.Frame(self.frame, bg="black")
        self.list_frame.grid(row=0, column=1, sticky="nsew")

        # User frame
        self.user_frame = tk.Frame(self.list_frame, bg="black")
        self.user_frame.grid(row=0, column=0, sticky="nsew")

        self.user_label = tk.Label(self.user_frame, text="Users(0)")
        self.user_label.grid(row=0, column=0, sticky='ew')

        self.user_listbox = tk.Listbox(self.user_frame, height=25, width=16)
        self.user_scrollbar = tk.Scrollbar(self.user_frame, orient="vertical", command=self.user_listbox.yview)
        self.user_listbox.config(yscrollcommand=self.user_scrollbar.set)
        self.user_listbox.grid(row=1, column=0, sticky='nsew')
        self.user_scrollbar.grid(row=1, column=1, sticky='ns')
        self.user_listbox.bind("<Button-3>", self.show_user_list_menu)

        # Channel frame
        self.channel_frame = tk.Frame(self.list_frame, bg="black")
        self.channel_frame.grid(row=1, column=0, sticky="nsew")

        # Label for Servers
        self.servers_label = tk.Label(self.channel_frame, text="Servers")
        self.servers_label.grid(row=0, column=0, sticky='ew')  # Make sure label is above the server_listbox

        # Server selection
        self.server_var = tk.StringVar(self.master)
        self.server_listbox = tk.Listbox(self.channel_frame, selectmode=tk.SINGLE, width=16, height=4)
        self.server_listbox.grid(row=1, column=0, sticky='w')  # Adjust column to display server_listbox

        # Server listbox scrollbar
        self.server_scrollbar = tk.Scrollbar(self.channel_frame, orient="vertical", command=self.server_listbox.yview)
        self.server_listbox.config(yscrollcommand=self.server_scrollbar.set)
        self.server_scrollbar.grid(row=1, column=1, sticky='ns')

        self.server_listbox.bind('<<ListboxSelect>>', self.on_server_change)

        self.channel_label = tk.Label(self.channel_frame, text="Channels (0)")
        self.channel_label.grid(row=2, column=0, sticky='ew')  # Make sure label is below the server_listbox

        self.channel_listbox = DragDropListbox(self.channel_frame, height=17, width=16, update_callback=self.update_joined_channels)
        self.channel_scrollbar = tk.Scrollbar(self.channel_frame, orient="vertical", command=self.channel_listbox.yview)
        self.channel_listbox.config(yscrollcommand=self.channel_scrollbar.set)
        self.channel_listbox.grid(row=3, column=0, sticky='nsew')  # Adjust row to display channel_listbox
        self.channel_scrollbar.grid(row=3, column=1, sticky='ns')
        self.channel_listbox.bind('<ButtonRelease-1>', self.on_channel_click)
        self.channel_listbox.bind("<Button-3>", self.show_channel_list_menu)
        self.master.bind("<Alt-KeyPress>", self._switch_to_index)
        self.master.bind("<Alt-s>", self.cycle_servers)

        # Server frame
        self.server_frame = tk.Frame(self.master, height=100, bg="black")
        self.server_frame.grid(row=2, column=0, columnspan=2, sticky='ew')

        # Configure column to expand
        self.server_frame.grid_columnconfigure(0, weight=1)

        self.server_text_widget = ScrolledText(self.server_frame, wrap='word', height=5, cursor="arrow")
        self.server_text_widget.grid(row=0, column=0, sticky='nsew')

        # Entry widget
        self.entry_widget = tk.Entry(self.master)
        self.entry_widget.grid(row=3, column=1, sticky='ew', columnspan=1)  # Adjust column span to cover only one column
        self.entry_widget.bind('<Tab>', self.handle_tab_complete)
        self.entry_widget.bind('<Up>', self.handle_arrow_keys)
        self.entry_widget.bind('<Down>', self.handle_arrow_keys)

        # Label for nickname and channel
        self.current_nick_channel = tk.StringVar(value="Nickname | #Channel" + " ▶")
        self.nick_channel_label = tk.Label(self.master, textvariable=self.current_nick_channel, padx=5, pady=1)
        self.nick_channel_label.grid(row=3, column=0, sticky='w')

        # Initialize the RudeChatClient and set the GUI reference
        self.irc_client = RudeChatClient(self.text_widget, self.server_text_widget, self.entry_widget, self.master, self)
        self.init_input_menu()
        self.init_message_menu()
        self.init_server_menu()
        self.apply_settings()
        self.master.protocol("WM_DELETE_WINDOW", self.client_shutdown)

        # Configure grid weights
        self.master.grid_rowconfigure(0, weight=0)
        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_columnconfigure(0, weight=0)
        self.master.grid_columnconfigure(1, weight=1)

        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=0)

        self.list_frame.grid_rowconfigure(0, weight=1)
        self.list_frame.grid_columnconfigure(0, weight=0)

        self.user_frame.grid_rowconfigure(1, weight=1)
        self.user_frame.grid_columnconfigure(0, weight=1)

        self.channel_frame.grid_rowconfigure(1, weight=1)
        self.channel_frame.grid_columnconfigure(0, weight=1)

        self.master.after(0, self.bind_return_key)

        self.master.bind('<Control-a>', self.select_short_all_text)
        self.master.bind('<Control-Prior>', self.switch_to_previous_channel)
        self.master.bind('<Control-Next>', self.switch_to_next_channel)
        self.entry_widget.bind("<Control-i>", lambda event: self.insert_text_format("\x1D"))  # Italic
        self.entry_widget.bind("<Control-b>", lambda event: self.insert_text_format("\x02"))  # Bold
        self.entry_widget.bind("<Control-u>", lambda event: self.insert_text_format("\x1F"))  # Underline
        self.entry_widget.bind("<Control-s>", lambda event: self.insert_text_format("\x1E"))  # Strike through
        self.entry_widget.bind("<Control-slash>", lambda event: self.insert_text_format("\x16"))  # Inverse

    def create_tray_icon(self, icon_path):
        """Create the system tray icon and menu."""
        
        # Define the callback for quitting the application
        def on_quit(icon, item):
            self.master.quit()  # Close the application when tray icon is clicked to quit

        # Load the tray icon image from the given path
        image = Image.open(icon_path)

        # Create a menu with a single "Quit" item that calls the on_quit callback
        menu = pystray.Menu(pystray.MenuItem("Quit", self.client_shutdown))

        # Create and run the system tray icon with the given image and menu
        self.tray_icon = pystray.Icon("RudeChat", image, "RudeChat", menu)

    def select_short_all_text(self, event):
        try:
            # Select all text in the entry widget
            self.entry_widget.focus_set()
            self.entry_widget.select_range(0, tk.END)
        except tk.TclError:
            pass

    def client_shutdown(self):
        # Close all pop-out windows
        if self.pop_out_windows:
            for target, window in self.pop_out_windows.items():
                window.destroy_window()

        # Shutdown the client
        loop = asyncio.get_event_loop()
        loop.create_task(self.irc_client.command_parser("/quit"), name="quit_client_task")

    def hidden_windows(self):
        if not self.show_server_window:
            self.server_frame.grid_forget()
            self.server_text_widget.grid_forget()
        elif self.show_server_window:
            self.server_frame.grid(row=2, column=0, columnspan=2, sticky='ew')
            self.server_text_widget.grid(row=0, column=0, sticky='nsew')

    def apply_settings(self):
        # Create font object
        user_listbox_font = tkFont.Font(family=self.list_boxs_font_family, size=self.user_font_size)
        channel_listbox_font = tkFont.Font(family=self.list_boxs_font_family, size=self.channel_font_size)
        server_listbox_font = tkFont.Font(family=self.list_boxs_font_family, size=self.server_font_size)
        topic_label_font = tkFont.Font(family=self.topic_label_font_family, size=self.topic_label_font_size)

        # Apply font settings to text widgets
        self.master.configure(bg=self.master_bg)
        self.text_widget.configure(font=(self.font_family, self.font_size))
        self.server_text_widget.configure(font=(self.font_family, self.font_size))
        self.entry_widget.configure(bg=self.input_bg, fg=self.input_fg, insertbackground=self.input_insertbackground, font=(self.font_family, self.font_size))
        self.nick_channel_label.configure(fg=self.input_label_fg, bg=self.input_label_bg, font=(self.font_family, self.font_size))

        # Apply maing GUI color settings
        self.text_widget.configure(fg=self.main_fg_color, bg=self.main_bg_color)
        self.server_text_widget.configure(fg=self.server_fg_color, bg=self.server_bg_color)

        # Apply Widget color settings
        self.user_listbox.configure(bg=self.user_listbox_bg, fg=self.user_listbox_fg, font=user_listbox_font)
        self.channel_listbox.configure(bg=self.channel_listbox_bg, fg=self.need_who_chan_fg, font=channel_listbox_font)
        self.server_listbox.configure(bg=self.server_list_bg, fg=self.server_list_fg, font=server_listbox_font)
        self.channel_label.configure(bg=self.channel_label_bg, fg=self.channel_label_fg)
        self.servers_label.configure(bg=self.servers_label_bg, fg=self.servers_label_fg)
        self.user_label.configure(bg=self.user_label_bg, fg=self.user_label_fg)
        self.topic_label.configure(bg=self.topic_label_bg, fg=self.topic_label_fg, font=topic_label_font)
        self.user_nickname_color = self.user_nickname_color
        self.tab_complete_terminator = self.tab_complete_terminator
        self.generate_nickname_colors = self.generate_nickname_colors
        self.channel_select_color = self.channel_select_color
        self.hidden_windows()
        self.highlight_nickname()
        self.highlight_away_users()

    def read_config(self):
        config_file = os.path.join(self.script_directory, 'gui_config.ini')

        if os.path.exists(config_file):
            config = configparser.ConfigParser()
            config.read(config_file)

            # Read main GUI settings
            self.user_nickname_color = config.get('GUI', 'main_nickname_color', fallback='#39ff14')
            self.generate_nickname_colors = config.getboolean('GUI', 'generate_nickname_colors', fallback=True)
            self.master_bg = config.get('GUI', 'master_color', fallback='black')
            self.font_family = config.get('GUI', 'family', fallback='Hack')
            self.font_size = config.getint('GUI', 'size', fallback=10)
            self.main_fg_color = config.get('GUI', 'main_fg_color', fallback='#C0FFEE')
            self.main_bg_color = config.get('GUI', 'main_bg_color', fallback='black')
            self.server_fg_color = config.get('GUI', 'server_fg', fallback='#7882ff')
            self.server_bg_color = config.get('GUI', 'server_bg', fallback='black')
            self.selected_list_server = config.get('GUI', 'selected_list_server', fallback='blue')
            self.user_font_size = config.getint('GUI', 'user_font_size', fallback=10)
            self.channel_font_size = config.getint('GUI', 'channel_font_size', fallback=10)
            self.server_font_size = config.getint('GUI', 'server_font_size', fallback=10)
            self.list_boxs_font_family = config.get('GUI', 'list_boxs_font_family', fallback='Hack') 
            self.topic_label_font_size = config.getint('GUI', 'topic_label_font_size', fallback=10)
            self.topic_label_font_family = config.get('GUI', 'topic_label_font_family', fallback='Hack')

            # Read Widget Settings
            self.user_listbox_fg = config.get('WIDGETS', 'users_fg', fallback='#39ff14')
            self.user_listbox_bg = config.get('WIDGETS', 'users_bg', fallback='black')
            self.user_label_bg = config.get('WIDGETS', 'user_label_bg', fallback='black')
            self.user_label_fg = config.get('WIDGETS', 'user_label_fg', fallback='white')
            self.away_user_fg = config.get('WIDGETS', 'away_user_fg', fallback='red')
            self.need_who_chan_fg = config.get('WIDGETS', 'need_who_chan_fg', fallback='red')
            self.channel_listbox_fg = config.get('WIDGETS', 'channels_fg', fallback='white')
            self.channel_listbox_bg = config.get('WIDGETS', 'channels_bg', fallback='black')
            self.input_fg = config.get('WIDGETS', 'entry_fg', fallback='#C0FFEE')
            self.input_bg = config.get('WIDGETS', 'entry_bg', fallback='black')
            self.input_insertbackground = config.get('WIDGETS', 'entry_insertbackground', fallback='#C0FFEE')
            self.input_label_bg = config.get('WIDGETS', 'entry_label_bg', fallback='black')
            self.input_label_fg = config.get('WIDGETS', 'entry_label_fg', fallback='#C0FFEE')
            self.server_list_bg = config.get('WIDGETS', 'server_listbox_bg', fallback='black')
            self.server_list_fg = config.get('WIDGETS', 'server_listbox_fg', fallback='white')
            self.channel_label_bg = config.get('WIDGETS', 'channel_label_bg', fallback='black')
            self.channel_label_fg = config.get('WIDGETS', 'channel_label_fg', fallback='white')
            self.servers_label_bg = config.get('WIDGETS', 'servers_label_bg', fallback='black')
            self.servers_label_fg = config.get('WIDGETS', 'servers_label_fg', fallback='white')
            self.topic_label_bg = config.get('WIDGETS', 'topic_label_bg', fallback='black')
            self.topic_label_fg = config.get('WIDGETS', 'topic_label_fg', fallback='white')
            self.show_server_window = config.getboolean('WIDGETS', 'show_server_window', fallback=True)
            self.channel_select_color = config.get('WIDGETS', 'channel_select_color', fallback='blue')
            self.tab_complete_terminator = config.get('WIDGETS', 'tab_complete_terminator', fallback=':')

        else:
            # Use default font settings if config file doesn't exist
            self.user_nickname_color = '#39ff14'
            self.generate_nickname_colors = True
            self.master_bg = 'black'
            self.font_family = 'Hack'
            self.font_size = 10
            self.main_fg_color = '#C0FFEE'
            self.main_bg_color = 'black'
            self.server_fg_color = '#7882ff'
            self.server_bg_color = 'black'
            self.selected_list_server = 'blue'
            self.user_listbox_fg = '#39ff14'
            self.user_listbox_bg = 'black'
            self.user_label_bg = 'black'
            self.user_label_fg = 'white'
            self.channel_listbox_fg = 'white'
            self.channel_listbox_bg = 'black'
            self.input_fg = '#C0FFEE'
            self.input_bg = 'black'
            self.input_insertbackground = '#C0FFEE'
            self.input_label_bg = 'black'
            self.input_label_fg = '#C0FFEE'
            self.server_list_bg = 'black'
            self.server_list_fg = 'white'
            self.channel_label_bg = 'black'
            self.channel_label_fg = 'white'
            self.servers_label_fg = 'white'
            self.servers_label_bg = 'black'
            self.topic_label_bg = 'black'
            self.topic_label_fg = 'white'
            self.show_server_window = True
            self.channel_select_color = 'blue'
            self.tab_complete_terminator = ":"
            print("GUI Fallbacks hit.")

    def open_gui_config_window(self):
        config_file = os.path.join(self.script_directory, 'gui_config.ini')
        config_window = GuiConfigWindow(config_file)
        config_window.root.wait_window()
        self.read_config()
        self.apply_settings()

    def show_startup_art(self):
        splash_directory = os.path.join(self.script_directory, "Splash")

        try:
            # List all .txt files in the Splash directory
            txt_files = [f for f in os.listdir(splash_directory) if f.endswith(".txt")]

            if not txt_files:
                raise FileNotFoundError("No .txt files found in the Splash directory")

            # Choose a random .txt file
            random_art_file = random.choice(txt_files)
            art_path = os.path.join(splash_directory, random_art_file)

            with open(art_path, "r", encoding='utf-8') as art_file:
                art_content = art_file.read()

                # Escape color codes in the art content
                escaped_art_content = self.escape_color_codes(art_content)

                self.insert_text_widget(escaped_art_content)
        except FileNotFoundError as e:
            print(f"Error displaying startup art: {e}")

    def highlight_away_users(self):
        # Loop through the items in the user_listbox
        for index in range(self.user_listbox.size()):
            # Get the username from the listbox
            username = self.user_listbox.get(index)
            
            # Strip any mode symbols from the username
            stripped_username = username.lstrip(''.join(self.irc_client.mode_values))
            
            # Check if the stripped username is in the away_users list
            if stripped_username in self.irc_client.away_users:
                # Change the foreground color of the user to red
                self.user_listbox.itemconfig(index, {'fg': self.away_user_fg})
            else:
                # Reset the foreground color if the user is not away
                self.user_listbox.itemconfig(index, {'fg': self.user_listbox_fg})

    def highlight_who_channels(self):
        # Loop through the items in the channel_listbox
        for index in range(self.channel_listbox.size()):
            # Get the channel from the listbox
            channel = self.channel_listbox.get(index)

            # Check if the stripped channel is in the away_users list
            if channel in self.irc_client.cap_who_for_chan:
                # Make sure the index exists in the channel_listbox
                if 0 <= index < self.channel_listbox.size():
                    # Change the foreground color 
                    self.channel_listbox.itemconfig(index, {'fg': self.channel_listbox_fg})
            else:
                # Make sure the index exists in the channel_listbox
                if 0 <= index < self.channel_listbox.size():
                    # Reset the foreground color 
                    self.channel_listbox.itemconfig(index, {'fg': self.need_who_chan_fg})

    def return_channel_to_listbox(self, entry):
        if entry in self.pop_out_windows:
            self.popped_out_channels.remove(entry)
        # Get all items in the listbox
        listbox_items = self.channel_listbox.get(0, tk.END)
        
        # Check if the entry is already in the listbox
        if entry not in listbox_items:
            # Insert the entry into the listbox if not found
            self.channel_listbox.insert(tk.END, entry)

    def clear_channel_listbox(self):
        self.channel_listbox.delete(0, tk.END)

    def scroll_channel_list(self):
        self.channel_listbox.see(0)

    def clear_user_listbox(self):
        self.user_listbox.delete(0, tk.END)

    def clear_topic_label(self):
        self.current_topic.set("")

    def clear_text_widget(self):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.config(state=tk.DISABLED)

    def clear_server_widget(self):
        self.server_text_widget.config(state=tk.NORMAL)
        self.server_text_widget.delete(1.0, tk.END)
        self.server_text_widget.config(state=tk.DISABLED)

    def update_joined_channels(self):
        """Update the joined_channels list."""
        self.irc_client.joined_channels = list(self.channel_listbox.get(0, tk.END))
        self.highlight_who_channels()

    def escape_color_codes(self, line):
        # Escape color codes in the string
        escaped_line = re.sub(r'\\x([0-9a-fA-F]{2})', lambda match: bytes.fromhex(match.group(1)).decode('utf-8'), line)
        
        return escaped_line

    def remove_server_from_listbox(self, server_name=None, reconnect=False):
        if server_name is None and reconnect is False:
            server_name = self.server_var.get()

        # Check if the server_name is in the Listbox (case-insensitive)
        if server_name:
            # Get the list of items in the Listbox and convert to lowercase for comparison
            listbox_items = [item.lower() for item in self.server_listbox.get(0, tk.END)]
            server_name_lower = server_name.lower()

            # Find the first item that starts with server_name_lower
            index_to_delete = None
            for index, item in enumerate(listbox_items):
                if item.startswith(server_name_lower):
                    index_to_delete = index
                    break

            # If a match is found, remove the item from the Listbox
            if index_to_delete is not None:
                self.server_listbox.delete(index_to_delete)

        # Set the first available server as the current one
        if self.server_listbox.size() > 0:
            self.server_var.set(self.server_listbox.get(0))
            self.server_listbox.select_set(0)
        else:
            self.server_var.set("")  # No servers left, clear the current selection

        # If reconnect is True and server_name is None, clear the entire listbox
        if reconnect and server_name is None:
            self.server_listbox.delete(0, tk.END)

        self.update_nick_channel_label()

    def load_nickname_colors(self):
        nickname_colors_path = os.path.join(self.script_directory, 'nickname_colours.json')

        try:
            with open(nickname_colors_path, 'r') as file:
                nickname_colors = json.load(file)
            return nickname_colors
        except FileNotFoundError:
            print(f"Nickname colors file not found at {nickname_colors_path}. Returning an empty dictionary.")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in nickname colors file: {e}. Returning an empty dictionary.")
            return {}
        except Exception as e:
            print(f"An unexpected error occurred while loading nickname colors: {e}. Returning an empty dictionary.")
            return {}

    def save_nickname_colors(self):
        clean_nicks = clean_nicknames(self.nickname_colors)
        nickname_colors_path = os.path.join(self.script_directory, 'nickname_colours.json')

        try:
            with open(nickname_colors_path, 'w') as file:
                json.dump(clean_nicks, file, indent=2)
        except Exception as e:
            print(f"An unexpected error occurred while saving nickname colors: {e}. Unable to save nickname colors.")

    def init_input_menu(self):
        """
        Right click menu for the Input Widget.
        """
        self.input_menu = Menu(self.entry_widget, tearoff=0)
        self.input_menu.add_command(label="Cut", command=self.cut_text)
        self.input_menu.add_command(label="Copy", command=self.copy_text)
        self.input_menu.add_command(label="Paste", command=self.paste_text)
        self.input_menu.add_command(label="Select All", command=self.select_all_text)

        # First set of IRC colors
        irc_colors_menu = Menu(self.input_menu, tearoff=0)
        irc_colors = [
            ("White", "00"),
            ("Black", "01"),
            ("Blue", "02"),
            ("Green", "03"),
            ("Red", "04"),
            ("Brown", "05"),
            ("Purple", "06"),
            ("Orange", "07"),
            ("Yellow", "08"),
            ("Lime", "09"),
            ("Teal", "10"),
            ("Cyan", "11"),
            ("Royal", "12"),
            ("Pink", "13"),
            ("Grey", "14"),
            ("Silver", "15"),
        ]

        for color_name, color_code in irc_colors:
            irc_colors_menu.add_command(label=color_name, command=lambda code=color_code: self.insert_irc_color(code))

        self.input_menu.add_cascade(label="IRC Color", menu=irc_colors_menu)

        # Additional IRC colors
        additional_irc_colors_menu = Menu(self.input_menu, tearoff=0)
        # Simple representation for color names
        additional_irc_colors = [(f"Color {i}", f"{i:02}") for i in range(16, 99)]

        for color_name, color_code in additional_irc_colors:
            additional_irc_colors_menu.add_command(label=color_name, command=lambda code=color_code: self.insert_irc_color(code))

        self.input_menu.add_cascade(label="Extended IRC Color", menu=additional_irc_colors_menu)

        text_format_menu = Menu(self.input_menu, tearoff=0)
        text_format_options = [
            ("Bold", "\x02"),
            ("Italic", "\x1D"),
            ("Underline", "\x1F"),
            ("Strike Through", "\x1E"),
            ("Inverse", "\x16")
        ]

        for format_name, format_code in text_format_options:
            text_format_menu.add_command(label=format_name, command=lambda code=format_code: self.insert_text_format(code))

        self.input_menu.add_cascade(label="Text Format", menu=text_format_menu)

        self.entry_widget.bind("<Button-3>", self.show_input_menu)

    def insert_irc_color(self, color_code):
        """
        Insert IRC color code around selected text or at cursor position.
        """
        try:
            selected_text = self.entry_widget.selection_get()
            start_index = self.entry_widget.index(tk.SEL_FIRST)
            end_index = self.entry_widget.index(tk.SEL_LAST)
        except Exception as e:
            selected_text = None

        if selected_text:
            self.entry_widget.delete(start_index, end_index)
            self.entry_widget.insert(start_index, f"\x03{color_code}{selected_text}\x03")
            self.entry_widget.select_range(start_index, end_index + 3)
            self.entry_widget.icursor(end_index + 4)
        else:
            self.entry_widget.insert("insert", f"\x03{color_code}")

    def insert_text_format(self, format_code):
        """
        Insert text format code around selected text or at cursor position.
        """
        try:
            selected_text = self.entry_widget.selection_get()
            start_index = self.entry_widget.index(tk.SEL_FIRST)
            end_index = self.entry_widget.index(tk.SEL_LAST)
        except Exception as e:
            selected_text = None

        if selected_text:
            self.entry_widget.delete(start_index, end_index)
            self.entry_widget.insert(start_index, f"{format_code}{selected_text}\x0F")
            self.entry_widget.select_range(start_index, end_index + len(format_code) + 1)
            self.entry_widget.icursor(end_index + len(format_code) + 1)
        else:
            self.entry_widget.insert("insert", format_code)

    def show_input_menu(self, event):
        try:
            self.input_menu.tk_popup(event.x_root, event.y_root)
            self.master.bind("<Motion>", self.check_input_mouse_position)
        finally:
            self.input_menu.grab_release()

    def init_message_menu(self):
        """
        Right click menu for the main chat window.
        """
        self.message_menu = Menu(self.text_widget, tearoff=0)
        self.message_menu.add_command(label="Copy", command=self.copy_text_message)
        self.message_menu.add_command(label="Reset Colors", command=self.reset_nick_colors)
        self.message_menu.add_command(label="Save Colors", command=self.save_nickname_colors)
        self.message_menu.add_command(label="Color Selector", command=self.open_color_selector)
        self.message_menu.add_command(label="Reload Macros", command=self.reload_macros)
        self.message_menu.add_command(label="Clear", command=self.clear_chat_window)
        self.message_menu.add_command(label="Server Config", command=self.open_client_config_window)
        self.message_menu.add_command(label="GUI Config", command=self.open_gui_config_window)
        
        self.text_widget.bind("<Button-3>", self.show_message_menu)

    def open_color_selector(self):
        root = tk.Toplevel(self.master)  # Use Toplevel instead of Tk for a new window
        app = RudeColours(root)
        root.geometry("400x300")  # Set the initial size of the window
        root.transient(self.master)  # Set the main window as the transient master
        root.mainloop()

    def reload_macros(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.irc_client.update_available_macros())
    
    def open_client_config_window(self):
        def after_config_window_close():
            # Reload configuration after the configuration window is closed
            self.irc_client.reload_config(config_window.config_file)

        def close_window():
            root.destroy()

        def on_config_window_close():
            root.after(100, after_config_window_close)  # Wait a short time before reloading config
            root.after(200, close_window)

        root = tk.Tk()
        root.title("Rude Server configuration")

        files = os.listdir(self.script_directory)
        config_files = [f for f in files if f.startswith("conf.") and f.endswith(".rude")]
        config_files.sort()

        if not config_files:
            tk.messagebox.showwarning("Warning", "No configuration files found.")
            root.destroy()
            return

        config_window = ServerConfigWindow(root, os.path.join(self.script_directory, config_files[0]), on_config_window_close)

        def on_config_change(event):
            selected_config_file = selected_config_file_var.get()
            config_window.config_file = os.path.join(self.script_directory, selected_config_file)
            config_window.config.read(config_window.config_file)
            config_window.create_widgets()

        # Menu to choose configuration file
        selected_config_file_var = tk.StringVar(root, config_files[0])
        config_menu = ttk.Combobox(root, textvariable=selected_config_file_var, values=config_files)
        config_menu.pack(pady=10)

        config_menu.bind("<<ComboboxSelected>>", on_config_change)

        save_button = tk.Button(root, text="Apply", command=config_window.save_config, bg=self.main_bg_color, fg=self.main_fg_color)
        save_button.pack(pady=10)

        instruction_label = tk.Label(root, text="To create a new config file simply change the data in the fields, then edit the file name in the file selection above Apply, configuration files must follow conf.exampleserver.rude format.", bg=self.main_bg_color, fg=self.main_fg_color, wraplength=180)
        instruction_label.pack()

        root.mainloop()

    def show_message_menu(self, event):
        try:
            # Open the popup menu
            self.message_menu.tk_popup(event.x_root, event.y_root)
            # Bind the <Motion> event to a function that checks if the mouse is over the menu
            self.master.bind("<Motion>", self.check_message_mouse_position)
        finally:
            self.message_menu.grab_release()

    def check_mouse_position(self, event, menu):
        try:
            # Get the position of the menu
            menu_x1 = menu.winfo_rootx()
            menu_y1 = menu.winfo_rooty()
            menu_x2 = menu_x1 + menu.winfo_width()
            menu_y2 = menu_y1 + menu.winfo_height()

            # Check if the mouse is outside the menu
            if not (menu_x1 <= event.x_root <= menu_x2 and menu_y1 <= event.y_root <= menu_y2):
                menu.unpost()
                self.master.unbind("<Motion>")
        except Exception as e:
            print(f"Exception in check_mouse_position: {e}")

    def check_input_mouse_position(self, event):
        self.check_mouse_position(event, self.input_menu)

    def check_message_mouse_position(self, event):
        self.check_mouse_position(event, self.message_menu)

    def check_user_mouse_position(self, event, menu):
        self.check_mouse_position(event, menu)

    def init_server_menu(self):
        """
        Right click menu for the server window.
        """
        self.server_menu = Menu(self.server_text_widget, tearoff=0)
        self.server_menu.add_command(label="Copy", command=self.copy_text_server)
        self.server_menu.add_command(label="Clear", command=self.clear_server_widget)

        self.server_text_widget.bind("<Button-3>", self.show_server_menu)

    def show_server_menu(self, event):
        try:
            self.server_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.server_menu.grab_release()

    def open_popout_query_from_menu(self):
        modes_to_strip = ''.join(self.irc_client.mode_values)
        selected_user_index = self.user_listbox.curselection()
        
        if selected_user_index:
            selected_user = self.user_listbox.get(selected_user_index)
            cleaned_nickname = selected_user.lstrip(modes_to_strip)

            # Check if the cleaned nickname is in the channel listbox and remove it
            listbox_items = self.channel_listbox.get(0, tk.END)
            if cleaned_nickname in listbox_items:
                index_to_remove = listbox_items.index(cleaned_nickname)
                self.channel_listbox.delete(index_to_remove)

            # Append to joined_channels if it's not already there
            if cleaned_nickname not in self.irc_client.joined_channels:
                self.irc_client.joined_channels.append(cleaned_nickname)
            
            # Update the channel list for the current server
            self.channel_lists[self.irc_client.server] = self.irc_client.joined_channels
            self.irc_client.update_gui_channel_list()

            # Open the direct message pop-out window
            self.open_dm_pop_out_from_window(cleaned_nickname)

    def create_user_list_menu(self):
        menu = tk.Menu(self.user_listbox, tearoff=0)
        menu.add_command(label="Open Query", command=self.open_query_from_menu)
        menu.add_command(label="Open Query Pop Out", command=self.open_popout_query_from_menu)
        menu.add_command(label="Copy", command=self.copy_text_user)
        menu.add_command(label="Whois", command=self.whois_from_menu)
        menu.add_command(label="Kick", command=self.kick_user_from_channel)
        return menu

    def show_user_list_menu(self, event):
        menu = self.create_user_list_menu()
        menu.post(event.x_root, event.y_root)
        self.master.bind("<Motion>", lambda e: self.check_user_mouse_position(e, menu))

    def create_channel_list_menu(self):
        menu = tk.Menu(self.channel_listbox, tearoff=0)
        
        # Assume self.channel_listbox is a list of channel names or DM nicknames
        selected_channel_index = self.channel_listbox.curselection()
        if selected_channel_index:
            selected_channel = self.channel_listbox.get(selected_channel_index)
            if selected_channel.startswith('#'):
                menu.add_command(label="Leave Channel", command=self.leave_channel_from_menu)
                menu.add_command(label="Pop Out Channel", command=self.open_pop_out_window)
            elif selected_channel.startswith('&'):
                menu.add_command(label="Close", command=self.close_query_from_menu)
            else:
                menu.add_command(label="Close Query", command=self.close_query_from_menu)
                menu.add_command(label="Pop Out Query", command=self.open_pop_out_window)
        
        return menu

    def open_pop_out_window(self):
        self.clear_text_widget()
        self.clear_user_listbox()
        self.clear_topic_label()
        self.irc_client.pop_out_switch()
        selected_channel = self.channel_listbox.get(self.channel_listbox.curselection())
        if selected_channel not in self.pop_out_windows:
            self.popped_out_channels.append(selected_channel)
            self.channel_listbox.delete(self.channel_listbox.curselection())
            root = tk.Tk()
            app = RudePopOut(root, selected_channel, self.irc_client, self.irc_client.nickname, self)
            self.pop_out_windows[selected_channel] = app
            root.mainloop()

    def open_dm_pop_out_from_window(self, user):
        if user not in self.pop_out_windows:
            self.popped_out_channels.append(user)
            
            # Get all items in the channel_listbox
            channel_list = self.channel_listbox.get(0, self.channel_listbox.size())
            
            # Find the index of the given user
            if user in channel_list:
                user_index = channel_list.index(user)
                # Delete the user from the channel_listbox using the found index
                self.channel_listbox.delete(user_index)
            
            root = tk.Tk()
            app = RudePopOut(root, user, self.irc_client, self.irc_client.nickname, self)
            self.pop_out_windows[user] = app
            root.mainloop()

    def show_channel_list_menu(self, event):
        menu = self.create_channel_list_menu()
        menu.post(event.x_root, event.y_root)
        self.master.bind("<Motion>", lambda e: self.check_user_mouse_position(e, menu))

    def copy_text_user(self):
        self.user_listbox.event_generate("<<Copy>>")

    def cut_text(self):
        self.entry_widget.event_generate("<<Cut>>")

    def copy_text(self):
        self.entry_widget.event_generate("<<Copy>>")

    def copy_text_message(self):
        self.text_widget.event_generate("<<Copy>>")

    def copy_text_server(self):
        self.server_text_widget.event_generate("<<Copy>>")

    def paste_text(self):
        self.entry_widget.event_generate("<<Paste>>")

    def select_all_text(self):
        self.entry_widget.select_range(0, tk.END)
        self.entry_widget.icursor(tk.END)

    def kick_user_from_channel(self):
        selected_user_index = self.user_listbox.curselection()
        channel = self.irc_client.current_channel
        if selected_user_index:
            selected_user = self.user_listbox.get(selected_user_index)
            loop = asyncio.get_event_loop()
            loop.create_task(self.irc_client.handle_kick_command(["/kick", selected_user, channel, "Bye <3"]))

    def open_query_from_menu(self):
        selected_user_index = self.user_listbox.curselection()
        if selected_user_index:
            selected_user = self.user_listbox.get(selected_user_index)
            loop = asyncio.get_event_loop()
            loop.create_task(self.irc_client.handle_query_command(["/query", selected_user], "<3 "))

    def close_query_from_menu(self):
        selected_channel_index = self.channel_listbox.curselection()
        if selected_channel_index:
            selected_channel = self.channel_listbox.get(selected_channel_index)
            self.irc_client.handle_cq_command(["/cq", selected_channel], "</3 ")

    def leave_channel_from_menu(self, reason=None):
        selected_channel_index = self.channel_listbox.curselection()
        if selected_channel_index:
            selected_channel = self.channel_listbox.get(selected_channel_index)
            if '#' in selected_channel:
                loop = asyncio.get_event_loop()
                loop.create_task(self.irc_client.leave_channel(selected_channel, reason))

    def whois_from_menu(self):
        modes_to_strip = ''.join(self.irc_client.mode_values)
        selected_user_index = self.user_listbox.curselection()
        if selected_user_index:
            selected_user = self.user_listbox.get(selected_user_index)
            cleaned_nickname = selected_user.lstrip(modes_to_strip)
            loop = asyncio.get_event_loop()
            loop.create_task(self.irc_client.whois(cleaned_nickname))

    def reset_nick_colors(self):
        self.nickname_colors = self.load_nickname_colors()
        self.highlight_nickname()

    def add_server_to_listbox(self, server_name):
        # Get the current list of servers from the Listbox
        current_servers = list(self.server_listbox.get(0, tk.END))
        
        # Check if any server in the list starts with server_name
        if not any(server.startswith(server_name) for server in current_servers):
            # Add the new server_name to the list if it's not already there
            current_servers.append(server_name)
        
        # Update the Listbox with the new list of servers
        self.server_listbox.delete(0, tk.END)  # Clear the existing items
        for server in current_servers:
            self.server_listbox.insert(tk.END, server)

    def show_topic_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
        x, y, _, _ = self.topic_label.bbox("insert")
        x += self.topic_label.winfo_rootx() + 25
        y += self.topic_label.winfo_rooty() + 25
        self.tooltip = tk.Toplevel(self.topic_label)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        # Specify the wraplength in pixels (e.g., 200 pixels)
        label = tk.Label(self.tooltip, text=self.current_topic.get(), justify='left', wraplength=800)
        label.pack()

    def hide_topic_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
        self.tooltip = None

    def insert_text_widget(self, message):
        try:
            self.trim_text_widget()
            urls = self.find_urls(message)

            # Set the Text widget state to NORMAL before inserting and configuring tags
            self.text_widget.config(state=tk.NORMAL)

            formatted_text = decoder(message)
            self.tag_text(formatted_text)

            # Start tagging URLs using the non-blocking approach
            self.tag_urls(urls)
        except Exception as e:
            print(f"Exception in insert_text {e}")

    def tag_text(self, formatted_text):
        for text, attributes in formatted_text:
            # Create a tag name based on the attributes
            tag_name = "_".join(str(attr) for attr in attributes)

            # Check if the tag configuration has changed
            if tag_name not in self.tag_cache:
                # If tag configuration is new, determine and cache it
                tag_config = self.configure_tag_based_on_attributes(attributes)
                self.text_widget.tag_configure(tag_name, **tag_config)
                self.tag_cache[tag_name] = tag_config

            # Insert the formatted text with the current tag
            self.text_widget.insert(tk.END, text, (tag_name,))

    def configure_tag_based_on_attributes(self, attributes):
        # This method configures tag based on attributes efficiently
        tag_config = {}
        if any(attr.bold for attr in attributes):
            tag_config['font'] = (self.font_family, self.font_size, 'bold')
        if any(attr.italic for attr in attributes):
            tag_config['font'] = (self.font_family, self.font_size, 'italic')
        if any(attr.underline for attr in attributes):
            tag_config['underline'] = True
        if any(attr.strikethrough for attr in attributes):
            tag_config['overstrike'] = True
        if attributes and attributes[0].colour != 0:
            irc_color_code = f"{attributes[0].colour:02d}"
            hex_color = self.irc_colors.get(irc_color_code, 'white')
            tag_config['foreground'] = hex_color
        if attributes and attributes[0].background != 1:
            irc_background_code = f"{attributes[0].background:02d}"
            hex_background = self.irc_colors.get(irc_background_code, 'black')
            tag_config['background'] = hex_background
        return tag_config

    def tag_urls(self, urls, index=0):
        if index < len(urls):
            url = urls[index]
            if url in self.url_cache:
                tag_name = self.url_cache[url]
            else:
                tag_name = f"url_{url}"
                self.url_cache[url] = tag_name
                self.text_widget.tag_configure(tag_name, foreground="blue", underline=1)

            start_idx = "1.0"
            while True:
                start_idx = self.text_widget.search(url, start_idx, tk.END)
                if not start_idx:
                    break
                end_idx = f"{start_idx}+{len(url)}c"
                self.text_widget.tag_add(tag_name, start_idx, end_idx)
                self.text_widget.tag_bind(tag_name, "<Button-1>", lambda event, url=url: self.open_url(event, url))
                start_idx = end_idx

            # Schedule the next URL tagging
            self.text_widget.after(1, self.tag_urls, urls, index + 1)
        else:
            # Set the Text widget state back to DISABLED after configuring tags
            self.text_widget.config(state=tk.DISABLED)
            self.insert_and_scroll()

    def find_urls(self, text):
        # Use the precompiled regex pattern to find URLs
        return self.url_pattern.findall(text)

    def open_url(self, event, url):
        webbrowser.open(url)

    def insert_server_widget(self, message):
        self.server_text_widget.config(state=tk.NORMAL)
        self.server_text_widget.insert(tk.END, message)
        self.server_text_widget.config(state=tk.DISABLED)
        self.insert_and_scroll()

    async def send_quit_to_all_clients(self, quit_message=None):
        try:       
            for irc_client in self.clients.values():
                await irc_client.save_channel_messages()
                quit_cmd = f'QUIT :{quit_message}' if quit_message else 'QUIT :RudeChat3 https://github.com/ShrugShoulders/RudeChat'
                await self.irc_client.send_message(quit_cmd)
        except Exception as e:
            print(f"Exception in send_quit_to_all_clients: {e}")

    async def stop_all_tasks(self):
        try:
            for irc_client in self.clients.values():
                await irc_client.stop_tasks()
        except Exception as e:
            print(f"Exception in stop_all_tasks: {e}")

    def add_client(self, server_name, irc_client):
        self.clients[server_name] = irc_client # Store clients here.

        # Get the current list of servers from the Listbox
        current_servers = list(self.server_listbox.get(0, tk.END))

        # Add the new server_name to the list if it's not already there
        if not any(server.startswith(server_name) for server in current_servers):
            current_servers.append(server_name)

        # Update the Listbox with the new list of servers
        self.server_listbox.delete(0, tk.END)  # Clear the existing items
        for server in current_servers:
            self.server_listbox.insert(tk.END, server)

        self.server_var.set(server_name)  # Set the current server
        self.server_listbox.select_set(0)
        self.channel_lists[server_name] = irc_client.joined_channels

    def server_checker(self, existing_server):
        # Convert the existing server to lowercase
        existing_server_lower = existing_server.lower()

        # Get the number of items in the Listbox
        num_items = self.server_listbox.size()

        # Iterate through each item in the Listbox
        for i in range(num_items):
            # Get the text of the current item and convert it to lowercase
            item_text_lower = self.server_listbox.get(i).lower()

            # Check if the current item starts with the server (case insensitive)
            if item_text_lower.startswith(existing_server_lower):
                # Server found, return True
                return True

        # Server not found, return False
        return False

    def cycle_servers(self, event):
        num_servers = self.server_listbox.size()
        current_index = self.server_listbox.curselection()

        if current_index:
            current_index = int(current_index[0])
            next_index = (current_index + 1) % num_servers
        else:
            next_index = 0

        # Select the next server in the listbox
        self.server_listbox.selection_clear(0, tk.END)
        self.server_listbox.selection_set(next_index)
        self.server_listbox.see(next_index)
        self.on_server_change(None)

    def on_server_change(self, event):
        # Get the index of the currently selected server
        selected_server_index_tuple = self.server_listbox.curselection()

        # If there's a selected server
        if selected_server_index_tuple:
            selected_server_index = selected_server_index_tuple[0]  # Extract the integer index

            # If there's a previous server, reset its background color to black
            if self.previous_server_index is not None:
                self.server_listbox.itemconfig(self.previous_server_index, {'bg': self.server_list_bg, 'fg': self.server_list_fg})

            # Get the selected server from the listbox
            selected_server = self.server_listbox.get(selected_server_index)
            clean_name = selected_server.split(" ")
            actual_server = clean_name[0]

            # Update the current server in the IRC client
            self.irc_client.current_server = actual_server
            self.irc_client = self.clients.get(actual_server, None)

            # If the IRC client exists
            if self.irc_client:
                # Set the server name in the RudeChatClient instance
                self.irc_client.set_server_name(actual_server)

                # Set the currently selected channel to None
                self.irc_client.current_channel = None

                # Set the GUI reference and update the GUI components
                self.irc_client.set_gui(self)
                self.irc_client.update_gui_channel_list()

                # Clear Widgets
                self.clear_topic_label()
                self.clear_user_listbox()
                self.clear_text_widget()

                # Display the MOTD if available
                self.show_startup_art()
                self.irc_client.display_server_motd(actual_server)
                self.update_users_label()
                self.highlight_nickname()
                self.highlight_who_channels()
                self.update_channel_label()
                self.text_widget.see(tk.END)

                # Set the background color of the selected server to blue
                self.server_listbox.itemconfig(selected_server_index, {'bg': self.selected_list_server, 'fg': self.server_list_fg})

                # Store the foreground and background colors for the selected server
                self.server_colors[selected_server_index] = {'fg': self.server_list_fg, 'bg': self.selected_list_server}
                
                if self.previous_server_index is not None:
                    if self.previous_server_index != selected_server_index:
                        # Check if the previous server color is not a mention or activity highlight before updating
                        prev_bg = self.server_colors[self.previous_server_index].get('bg', '')
                        if prev_bg not in [self.irc_client.activity_note_color, self.irc_client.mention_note_color]:
                            self.server_colors[self.previous_server_index] = {'bg': self.server_list_bg, 'fg': self.server_list_fg}

            for server_index, colors in self.server_colors.items():
                # Get the stored foreground and background colors
                fg_color = colors.get('fg', self.server_list_fg)
                bg_color = colors.get('bg', self.server_list_bg)

                # Apply the stored colors to each server in the listbox
                self.server_listbox.itemconfig(server_index, foreground=fg_color, background=bg_color)

            # Update the previous_server_index to the currently selected server index
            self.previous_server_index = selected_server_index

    def get_server_color(self, index):
        # Get the colors from the dictionary
        return self.server_colors.get(index, {'fg': None, 'bg': None})

    async def init_client_with_config(self, config_file, fallback_server_name):
        irc_client = None
        try:
            irc_client = RudeChatClient(self.text_widget, self.server_text_widget, self.entry_widget, self.master, self)
            irc_client.client_event_loops[irc_client] = asyncio.get_event_loop()  # Store a reference to the event loop
            irc_client.tasks = {}  # Create a dictionary to store references to tasks
        except Exception as e:
            print(f"Error initializing IRC client: {e}")
            return  # Stop further execution if client initialization fails

        try:
            irc_client.tasks["load_ascii_art_macros"] = asyncio.create_task(irc_client.load_ascii_art_macros(), name="load_ascii_art_macros_task")
        except Exception as e:
            print(f"Error loading ASCII art macros: {e}")

        try:
            await irc_client.read_config(config_file)
        except Exception as e:
            print(f"Error reading configuration from {config_file}: {e}")

        try:
            await irc_client.connect(config_file)
        except Exception as e:
            print(f"Error connecting with configuration {config_file}: {e}")

        try:
            # Use the server_name from config, otherwise fallback
            server_name = irc_client.server_name if irc_client.server_name else fallback_server_name
            self.add_client(server_name, irc_client)
        except Exception as e:
            print(f"Error adding client {server_name}: {e}")

        try:
            # Create and store references to tasks
            irc_client.tasks["keep_alive"] = asyncio.create_task(irc_client.keep_alive(config_file), name="keep_alive_task")
        except Exception as e:
            print(f"Error starting keep_alive task: {e}")

        try:
            irc_client.tasks["auto_save"] = asyncio.create_task(irc_client.auto_save(), name="auto_save_task")
        except Exception as e:
            print(f"Error starting auto_save task: {e}")

        try:
            irc_client.tasks["auto_trim"] = asyncio.create_task(irc_client.auto_trim(), name="auto_trim_task")
        except Exception as e:
            print(f"Error starting auto_trim task: {e}")

        try:
            irc_client.tasks["handle_incoming_message"] = asyncio.create_task(irc_client.handle_incoming_message(config_file), name="handle_incoming_message_task")
        except Exception as e:
            print(f"Error starting handle_incoming_message task: {e}")

        try:
            irc_client.tasks["auto_who"] = asyncio.create_task(irc_client.request_who_for_all_channels(), name="auto_who_task")
        except Exception as e:
            print(f"Error starting auto_who task: {e}")

        try:
            irc_client.tasks["auto_away"] = asyncio.create_task(irc_client.away_watcher(), name="auto_away_task")
        except Exception as e:
            print(f"Error starting auto_away task: {e}")

        try:
            self.bind_return_key()
        except Exception as e:
            print(f"Error binding return key: {e}")

    def bind_return_key(self):
        loop = asyncio.get_event_loop()
        self.entry_widget.bind('<Return>', lambda event: loop.create_task(self.on_enter_key(event), name="on_enter_key"))

    async def on_enter_key(self, event):
        try:
            user_input = self.entry_widget.get()

            # Save the entered message to entry_history
            if user_input:
                self.entry_history.append(user_input)

                # Limit the entry_history to the last 10 messages
                if len(self.entry_history) > 10:
                    self.entry_history.pop(0)

                # Reset history_index to the end of entry_history
                self.history_index = len(self.entry_history)

            self.entry_widget.delete(0, tk.END)
            await self.irc_client.command_parser(user_input)
            if hasattr(self, 'text_widget') and self.text_widget.winfo_exists():
                self.text_widget.see(tk.END)
        except Exception as e:
            pass

    def handle_arrow_keys(self, event):
        if event.keysym == 'Up':
            self.show_previous_entry()
        elif event.keysym == 'Down':
            self.show_next_entry()

    def show_previous_entry(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.entry_widget.delete(0, tk.END)
            self.entry_widget.insert(0, self.entry_history[self.history_index])

    def show_next_entry(self):
        if self.history_index < len(self.entry_history) - 1:
            self.history_index += 1
            self.entry_widget.delete(0, tk.END)
            self.entry_widget.insert(0, self.entry_history[self.history_index])
        elif self.history_index == len(self.entry_history) - 1:
            self.history_index += 1
            self.entry_widget.delete(0, tk.END)

    def _switch_to_index(self, event):
        key = event.char
        if key.isdigit():
            index = int(key) - 1
            if index == -1:
                index = 9  # Make the '0' key correspond to the tenth channel
            self.switch_to_index(event, index)

    def switch_to_index(self, event, index):
        # Set background of currently selected channel back to default
        current_selected_channel = self.irc_client.current_channel
        if current_selected_channel:
            for i in range(self.channel_listbox.size()):
                if self.channel_listbox.get(i) == current_selected_channel:
                    self.channel_listbox.itemconfig(i, {'bg': self.channel_listbox_bg})
                    break

        # Get the channel name at the specified index
        next_channel = self.channel_listbox.get(index)

        # Switch to the channel at the specified index
        self.switch_channel(next_channel)

        # Turn background blue for the next channel
        self.channel_listbox.itemconfig(index, {'bg': self.channel_select_color})
        self.highlight_nickname()

        # Remove the next channel from highlighted_channels dictionary if present
        if self.irc_client.server_name in self.irc_client.highlighted_channels:
            server_highlighted_channels = self.irc_client.highlighted_channels[self.irc_client.server_name]
            if next_channel in server_highlighted_channels:
                del server_highlighted_channels[next_channel]

        self.channel_listbox.see(index)
        return "break"

    def switch_to_next_channel(self, event):
        # Set background of currently selected channel back to default
        current_selected_channel = self.irc_client.current_channel
        if current_selected_channel:
            for i in range(self.channel_listbox.size()):
                if self.channel_listbox.get(i) == current_selected_channel:
                    self.channel_listbox.itemconfig(i, {'bg': self.channel_listbox_bg})
                    break

        # Get index of currently selected item
        selected_index = self.channel_listbox.curselection()

        # Calculate index of the next item down
        if self.last_selected_index is None:
            next_index = 0
        else:
            next_index = (self.last_selected_index + 1) % self.channel_listbox.size()

        # Get the channel name of the next item down
        next_channel = self.channel_listbox.get(next_index)

        # Switch to the next channel
        self.switch_channel(next_channel)

        # Turn background blue for the next channel
        self.channel_listbox.itemconfig(next_index, {'bg': self.channel_select_color})
        self.highlight_nickname()

        # Remove the next channel from highlighted_channels dictionary if present
        if self.irc_client.server_name in self.irc_client.highlighted_channels:
            server_highlighted_channels = self.irc_client.highlighted_channels[self.irc_client.server_name]
            if next_channel in server_highlighted_channels:
                del server_highlighted_channels[next_channel]

        # Update last selected index
        self.last_selected_index = next_index
        self.channel_listbox.see(next_index)

        # Prevent further event processing
        return "break"

    def switch_to_previous_channel(self, event):
        # Set background of currently selected channel back to default
        current_selected_channel = self.irc_client.current_channel
        if current_selected_channel:
            for i in range(self.channel_listbox.size()):
                if self.channel_listbox.get(i) == current_selected_channel:
                    self.channel_listbox.itemconfig(i, {'bg': self.channel_listbox_bg})
                    break

        # Get index of currently selected item
        selected_index = self.channel_listbox.curselection()

        # Calculate index of the previous item up
        if self.last_selected_index is None:
            previous_index = self.channel_listbox.size() - 1
        else:
            previous_index = (self.last_selected_index - 1) % self.channel_listbox.size()

        # Get the channel name of the previous item up
        previous_channel = self.channel_listbox.get(previous_index)

        # Switch to the previous channel
        self.switch_channel(previous_channel)

        # Turn background blue for the previous channel
        self.channel_listbox.itemconfig(previous_index, {'bg': self.channel_select_color})
        self.highlight_nickname()

        # Remove the previous channel from highlighted_channels dictionary if present
        if self.irc_client.server_name in self.irc_client.highlighted_channels:
            server_highlighted_channels = self.irc_client.highlighted_channels[self.irc_client.server_name]
            if previous_channel in server_highlighted_channels:
                del server_highlighted_channels[previous_channel]

        # Update last selected index
        self.last_selected_index = previous_index
        self.channel_listbox.see(previous_index)

        return "break"

    def on_channel_click(self, event):
        # Set background of currently selected channel back to default
        current_selected_channel = self.irc_client.current_channel
        if current_selected_channel:
            for i in range(self.channel_listbox.size()):
                if self.channel_listbox.get(i) == current_selected_channel:
                    self.channel_listbox.itemconfig(i, {'bg': self.channel_listbox_bg})
                    break

        # Get index of clicked item
        clicked_index = self.channel_listbox.curselection()
        if clicked_index:
            clicked_channel = self.channel_listbox.get(clicked_index[0])
            self.switch_channel(clicked_channel)

            # Turn background blue
            self.channel_listbox.itemconfig(clicked_index, {'bg': self.channel_select_color})
            self.highlight_nickname()
            self.highlight_away_users()
            self.update_users_label()

            # Remove the clicked channel from highlighted_channels dictionary
            if self.irc_client.server_name in self.irc_client.highlighted_channels:
                server_highlighted_channels = self.irc_client.highlighted_channels[self.irc_client.server_name]
                if clicked_channel in server_highlighted_channels:
                    del server_highlighted_channels[clicked_channel]

    def the_force_click(self, index):
        # Set background of currently selected channel back to default
        current_selected_channel = self.irc_client.current_channel
        if current_selected_channel:
            for i in range(self.channel_listbox.size()):
                if self.channel_listbox.get(i) == current_selected_channel:
                    self.channel_listbox.itemconfig(i, {'bg': self.channel_listbox_bg})
                    break

        # Get index of clicked item
        clicked_index = index
        if clicked_index:
            clicked_channel = self.channel_listbox.get(clicked_index)
            self.switch_channel(clicked_channel)

            # Turn background blue
            self.channel_listbox.itemconfig(clicked_index, {'bg': self.channel_select_color})
            self.highlight_nickname()
            self.highlight_away_users()
            self.update_users_label()

            # Remove the clicked channel from highlighted_channels dictionary
            if self.irc_client.server_name in self.irc_client.highlighted_channels:
                server_highlighted_channels = self.irc_client.highlighted_channels[self.irc_client.server_name]
                if clicked_channel in server_highlighted_channels:
                    del server_highlighted_channels[clicked_channel]

    def trim_text_widget(self):
        """Trim the text widget to only hold a maximum of 120 lines."""
        lines = self.text_widget.get("1.0", tk.END).split("\n")
        if len(lines) > 125:
            self.text_widget.config(state=tk.NORMAL)  # Enable text widget editing
            self.text_widget.delete("1.0", f"{len(lines) - 125}.0")  # Delete excess lines
            self.text_widget.config(state=tk.DISABLED)  # Disable text widget editing

    def switch_channel(self, channel_name):
        try:
            server = self.irc_client.server  # Assume the server is saved in the irc_client object
        except AttributeError as e:
            print(f"AttributeError in switch_channel: server assignment {e}")
            return

        # Clear the text window
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.config(state=tk.DISABLED)

        # Print the current channel topics dictionary

        is_channel = any(channel_name.startswith(prefix) for prefix in self.irc_client.chantypes)

        if is_channel:
            # It's a channel
            if server in self.irc_client.channel_messages:

                self.irc_client.current_channel = channel_name
                self.update_nick_channel_label()

                # Update topic label
                current_topic = self.channel_topics.get(self.irc_client.server, {}).get(channel_name, "N/A")
                self.current_topic.set(f"{current_topic}")

                # Display the last messages for the current channel
                self.irc_client.display_last_messages(channel_name, server_name=server)
                self.highlight_nickname()

                self.irc_client.update_gui_user_list(channel_name)
                self.insert_and_scroll()

            else:
                self.insert_text_widget(f"Not a member of channel {channel_name}\n")

        else:
            self.clear_user_listbox()
            # Set current channel to the DM
            nickname = self.irc_client.nickname
            self.irc_client.current_channel = channel_name
            self.user_listbox.insert(tk.END, nickname)
            self.user_listbox.insert(tk.END, channel_name)
            self.update_nick_channel_label()

            # Display the last messages for the current DM
            self.irc_client.display_last_messages(channel_name, server_name=server)
            self.insert_and_scroll()
            self.highlight_nickname()

            # No topic for DMs
            self.current_topic.set(f"{channel_name}")

    def insert_and_scroll(self):
        self.text_widget.see(tk.END)

    def clear_chat_window(self):
        current_channel = self.irc_client.current_channel

        if current_channel:
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.config(state=tk.DISABLED)
            self.irc_client.channel_messages[self.irc_client.server][current_channel] = []

    def get_mode_symbol(self, mode):
        """Return the symbol corresponding to the IRC mode."""
        return self.irc_client.mode_to_symbol.get(mode, '')

    def get_user_mode(self, user, channel):
        """Retrieve the user's mode for the given channel."""
        channel_modes = self.irc_client.user_modes.get(channel, {})
        user_modes = channel_modes.get(user, set())
        return next(iter(user_modes), None)  # Get the first mode if available, else None

    def update_nick_channel_label(self):
        """Update the label with the current nickname and channel."""
        nickname = self.irc_client.nickname if self.irc_client.nickname else "Nickname"
        channel = self.irc_client.current_channel if self.irc_client.current_channel else "#Channel"
        user_mode = self.get_user_mode(nickname, channel)
        mode_symbol = self.get_mode_symbol(user_mode) if user_mode else ''
        self.current_nick_channel.set(f"{mode_symbol}{nickname} | {channel}" + " ▷")

    def highlight_nickname(self):
        """Highlight the user's nickname in the text_widget."""
        modes = self.irc_client.mode_values + ['']
        user_nickname = self.irc_client.nickname
        if not user_nickname:
            return

        # Configure the color for the user's nickname
        self.text_widget.tag_configure("nickname", foreground=self.user_nickname_color)

        # Start at the beginning of the text_widget
        start_idx = "1.0"
        while True:
            # Find the position of the next instance of the user's nickname
            start_idx = self.text_widget.search(user_nickname, start_idx, stopindex=tk.END, regexp=True, nocase=True)
            if not start_idx:
                break

            # Calculate the end index based on the length of the nickname
            end_idx = self.text_widget.index(f"{start_idx}+{len(user_nickname)}c")

            # Apply the tag to the found nickname
            self.text_widget.tag_add("nickname", start_idx, end_idx)

            # Update the start index to search from the position after the current found nickname
            start_idx = end_idx

        # Start again at the beginning of the text_widget for other nicknames enclosed in <>
        start_idx = "1.0"
        while True:
            # Find the opening '<'
            start_idx = self.text_widget.search('<', start_idx, stopindex=tk.END)
            if not start_idx:
                break
            # Find the closing '>' ensuring no newlines between
            end_idx = self.text_widget.search('>', start_idx, f"{start_idx} lineend")
            if end_idx:
                end_idx = f"{end_idx}+1c"  # Include the '>' character
                # Extract the nickname with '<' and '>'
                nickname_with_brackets = self.text_widget.get(start_idx, end_idx)

                # Extract the nickname without modes
                modes_to_strip = ''.join(self.irc_client.mode_values)
                nickname = nickname_with_brackets.strip('<>')
                plain_nickname = nickname.lstrip(modes_to_strip)

                # Check if the plain nickname color is already in the cache
                if f"<{plain_nickname}>" in self.nickname_colors:
                    nickname_color = self.nickname_colors[f"<{plain_nickname}>"]
                    # Cache the color for the nickname with modes
                    self.nickname_colors[nickname_with_brackets] = nickname_color
                else:
                    # If nickname doesn't have an assigned color, generate one
                    if self.generate_nickname_colors:
                        nickname_color = self.generate_random_color()
                    else:
                        nickname_color = self.main_fg_color

                    # If it's the main user's nickname, set color to user_nickname_color
                    for mode in modes:
                        if nickname_with_brackets == f"<{mode}{self.irc_client.nickname}>":
                            nickname_color = self.user_nickname_color

                    # Cache the color
                    self.nickname_colors[nickname_with_brackets] = nickname_color
                    self.nickname_colors[f"<{plain_nickname}>"] = nickname_color

                self.text_widget.tag_configure(f"nickname_{nickname_with_brackets}", foreground=nickname_color)
                self.text_widget.tag_add(f"nickname_{nickname_with_brackets}", start_idx, end_idx)
                start_idx = end_idx
            else:
                start_idx = f"{start_idx}+1c"

    def generate_random_color(self):
        while True:
            # Generate random values for each channel
            r = random.randint(50, 255)
            g = random.randint(50, 255)
            b = random.randint(50, 255)
            
            # Ensure the difference between the maximum and minimum channel values is above a threshold
            if max(r, g, b) - min(r, g, b) > 50:  # 50 is the threshold, you can adjust this value as needed
                return "#{:02x}{:02x}{:02x}".format(r, g, b)

    def trigger_desktop_notification(self, channel_name=None, title="RudeChat", message_content=None):
        """
        Show a system desktop notification.
        """
        script_directory = os.path.dirname(os.path.abspath(__file__))

        # Check if the application window is the active window
        if self.is_app_focused():  # If the app is focused, return early
            return

        if channel_name:
            # Ensure channel_name is a string
            channel_name = str(channel_name)

            # Remove any prefix from self.irc_client.chantypes
            for prefix in self.irc_client.chantypes:
                if channel_name.startswith(prefix):
                    channel_name = channel_name[len(prefix):]
                    break  # Break after the first matching prefix is removed

            # Construct the notification title and message
            title = f"{title}"
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

    def is_app_focused(self):
        return bool(self.master.focus_displayof())

    def update_ping_label(self, server_name, ping_time):
        # Retrieve all items from the listbox
        servers = self.server_listbox.get(0, tk.END)
        
        # Iterate through the servers and update the one with the matching server_name
        updated_servers = []
        for index, server in enumerate(servers):
            if server.startswith(server_name):
                updated_server = f'{server_name} PT{ping_time}'
            else:
                updated_server = server
            updated_servers.append(updated_server)
        
        # Clear the current listbox and insert updated items
        self.server_listbox.delete(0, tk.END)  # Clear listbox
        for index, server in enumerate(updated_servers):
            self.server_listbox.insert(tk.END, server)  # Add updated items back into the listbox
            
            # Get the color configuration for the current index
            server_colors = self.get_server_color(index)
            
            # Apply the foreground and background colors if available
            if server_colors['fg'] or server_colors['bg']:
                self.server_listbox.itemconfig(index, foreground=server_colors['fg'], background=server_colors['bg'])

    def update_users_label(self):
        if self.irc_client.server_name in self.irc_client.away_servers:
            away_text = f"You're Away"
            self.user_label.config(text=away_text, fg="red")
        else:
            user_num = len(self.irc_client.channel_users.get(self.irc_client.current_channel, []))
            back_text = f"Users ({user_num})"
            self.user_label.config(text=back_text, fg=self.user_label_fg)
            if self.irc_client.server_name in self.irc_client.away_servers:
                self.irc_client.away_servers.remove(self.irc_client.server_name)

    def update_channel_label(self):
        channel_num = len(self.irc_client.joined_channels)
        label_text = f"Channels ({channel_num})"
        self.channel_label.config(text=label_text)

    def handle_tab_complete(self, event):
        """
        Tab complete with cycling through possible matches.
        """
        modes_to_strip = ''.join(self.irc_client.mode_values)
        # Get the current input in the input entry field
        user_input = self.entry_widget.get()
        cursor_pos = self.entry_widget.index(tk.INSERT)

        # Find the partial nick before the cursor position
        partial_nick = ''
        for i in range(cursor_pos - 1, -1, -1):
            char = user_input[i]
            if not char.isalnum() and char not in "_-^[]{}\\`|":
                break
            partial_nick = char + partial_nick

        # Cancel any previous timers
        if hasattr(self, 'tab_completion_timer'):
            self.master.after_cancel(self.tab_completion_timer)

        # Get the user list for the current channel
        current_channel = self.irc_client.current_channel
        if current_channel in self.irc_client.channel_users:
            user_list = self.irc_client.channel_users[current_channel]
        else:
            user_list = self.user_listbox.get(0, tk.END)

        # Remove @ and + symbols from nicknames
        user_list_cleaned = [nick.lstrip(modes_to_strip) for nick in user_list]

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
            self.entry_widget.delete(0, tk.END)
            self.entry_widget.insert(0, completed_text)
            # Cycle to the next completion
            self.tab_complete_index = (self.tab_complete_index + 1) % len(self.tab_complete_completions)

        # Set up a timer to append ": " after half a second if no more tab presses
        try:
            if self.entry_widget.get().startswith(completed_nick):
                self.tab_completion_timer = self.master.after(250, self.append_terminator_to_nick)
            else:
                self.tab_completion_timer = self.master.after(250, self.append_space_to_nick)
        except UnboundLocalError as e:
            pass

        # Prevent default behavior of the Tab key
        return 'break'

    def append_terminator_to_nick(self):
        current_text = self.entry_widget.get()
        self.entry_widget.delete(0, tk.END)
        self.entry_widget.insert(0, current_text + self.tab_complete_terminator + " ")

    def append_space_to_nick(self):
        current_text = self.entry_widget.get()
        self.entry_widget.delete(0, tk.END)
        self.entry_widget.insert(0, current_text + " ")
