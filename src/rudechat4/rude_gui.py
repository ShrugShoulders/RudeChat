from rudechat4.shared_imports import *
from rudechat4.global_variables import *
from rudechat4.rude_client import RudeChatClient
from rudechat4.server_config_window import ServerConfigWindow
from rudechat4.nick_cleaner import clean_nicknames
from rudechat4.format_decoder import decoder

class RudeTextEdit(QTextEdit):
    def get_anchor_at(self, pos):
        cursor = self.cursorForPosition(pos)
        char_format = cursor.charFormat()
        if char_format.isAnchor():
            return char_format.anchorHref()

    def is_anchor_at(self, pos):
        cursor = self.cursorForPosition(pos)
        return cursor.charFormat().isAnchor()

    def mousePressEvent(self, e):
        if self.is_anchor_at(e.pos()):
            url = self.get_anchor_at(e.pos())
            webbrowser.open(url)
        else:
            e.ignore()

class RudeGui(QWidget):
    # Initialisation and Setup
    def __init__(self, master):
        super().__init__()
        self.master = master
        self.app_size = [800, 600]
        self.set_screen_size()
        self.master.setWindowTitle("RudeChat")
        self.master.resize(self.app_size[0], self.app_size[1])

        self.set_icon()

        self.read_config()
        #self.start_tray_icon()

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

        self.emojis = [
            "😀", "😂", "😍", "😎", "😭", "😡", "🥺", "😳", "😘", "😧", "😇", "😖", "🤐", "👍", "👎", "🤔", "😈", "😺",
            "🎉", "🔥", "✨", "💥", "💯", "💀", "❤️", "💔", "💌", "🌸", "💐", "🍀", "🌈", "☀️", "🌙", "⭐", "🌍", "🌎",
            "🌏", "🏆", "🥇", "🎁", "🕶️", "🎸", "🎤", "🎧", "🎮", "🕹️", "🏁", "🚀", "🛸", "🌪️", "🦄", "🍎", "🍉", "🍓",
            "🍍", "🥑", "🍣", "🍕", "🍔", "🌮", "🌯", "🍿", "🍩", "🍪", "🥧", "🍰", "🍒", "🍇", "🍓", "🥥", "🥝", "🍑",
            "🍺", "🍻", "🍷", "🍸", "🍹", "🥂", "🍾", "🥃", "🍺", "🍷", "🍻", "🍾", "🥂", "🥃", "🧃", "🍽️", "🥄", "🍴",
            "👑", "💎", "👒", "👗", "👠", "👞", "🕴️", "🧥", "👚", "🧢", "👚", "👛", "👜", "💄", "💍", "🎩", "👢", "🦸",
            "💃", "🕺", "🤷‍", "🙆", "🙋", "🤰", "🤱", "🧑‍🍼", "👨‍🍼", "👩‍🍼", "🦷", "🐱", "🦪", "😱", "🍒", "🥢", "🐦", "🦞",
            "🐶", "🐰", "🐹", "🐷", "🐴", "🦄", "🐮", "🐨", "🦊", "🐯", "🐼", "🐵", "🦁", "🐒", "🦓", "🐸", "🦋", "🦋",
            "🐝", "🐞", "🐛", "🦗", "🦠", "🐍", "🐢", "🦎", "🐳", "🐋", "🐟", "🐠", "🦈", "🐬", "🐙", "🐚", "🦑", "🦐",
        ]

        self.SPECIAL_EMO_CASES = {
            "⛈": 0,
            "❌": 0,
            "😐": 1,
            "☁️": 0,
            "☁": 0,
            "✊": 0,
            "☘️": 0,
            "☘": 0,
            "🌶": 1,
            "⛴": 0,
            "⏰": 0,
            "⏱": 0,
            "⏲": 0,
            "🖥": 1,
            "🖱": 1,
            "🎙": 1,
            "🎵": 1,
            "⛅": 0,
        }

        # Initialise layout
        self.init_layout()

        # Initialise other instance variables
        self.set_misc_variables()

        # Set GUI Theme
        self.set_gui_theme()

        # Initialise client
        self.init_client()

        self.master.chat_upload_file_action.triggered.connect(lambda: self.irc_client.loop.create_task(self.irc_client.handle_upload(), name="handle_upload"))
        self.master.chat_clear_chat_action.triggered.connect(self.clear_chat_window)
        self.master.chat_reload_macros_action.triggered.connect(self.reload_macros)
        self.master.colors_color_selector_action.triggered.connect(self.open_color_selector)
        self.master.colors_save_colors_action.triggered.connect(self.save_nickname_colors)
        self.master.colors_reset_colors_action.triggered.connect(self.reset_nick_colors)
        self.master.config_edit_servers_action.triggered.connect(self.open_client_config_window)
        self.master.config_edit_gui_action.triggered.connect(self.open_gui_config_window)

    def set_screen_size(self):
        try:
            screen = QGuiApplication.primaryScreen()
            if not screen:
                raise ValueError("No available screen detected.")  # Handle None case

            width = screen.size().width()
            height = screen.size().height()
            self.app_size = [width, height]
        except Exception as e:
            logging.error(f"Unable to get screen size: {e}. Using default variables.")
            screen_size = "default"  # Prevent NameError in match-case

    def set_icon(self): pass #TODO

    def read_config(self):
        config_file = os.path.join(G_CONFIG_DIR, 'gui_config.ini')

        if os.path.exists(config_file):
            config = configparser.ConfigParser()
            config.read(config_file)

            # Read main GUI settings
            self.user_nickname_color = config.get('GUI', 'main_nickname_color', fallback='#39ff14')
            self.generate_nickname_colors = config.getboolean('GUI', 'generate_nickname_colors', fallback=True)
            self.master_bg = config.get('GUI', 'master_color', fallback='black')
            self.font_family = config.get('GUI', 'family', fallback='Courier')
            self.font_size = config.getint('GUI', 'size', fallback=10)
            self.main_fg_color = config.get('GUI', 'main_fg_color', fallback='#C0FFEE')
            self.main_bg_color = config.get('GUI', 'main_bg_color', fallback='black')
            self.server_fg_color = config.get('GUI', 'server_fg', fallback='#7882ff')
            self.server_bg_color = config.get('GUI', 'server_bg', fallback='black')
            self.selected_list_server = config.get('GUI', 'selected_list_server', fallback='blue')
            self.user_font_size = config.getint('GUI', 'user_font_size', fallback=10)
            self.channel_font_size = config.getint('GUI', 'channel_font_size', fallback=10)
            self.server_font_size = config.getint('GUI', 'server_font_size', fallback=10)
            self.list_boxs_font_family = config.get('GUI', 'list_boxs_font_family', fallback='Courier') 
            self.topic_label_font_size = config.getint('GUI', 'topic_label_font_size', fallback=10)
            self.topic_label_font_family = config.get('GUI', 'topic_label_font_family', fallback='Courier')
            self.to_tray = config.getboolean('GUI', 'minimize_to_tray', fallback=True)
            self.highlight_all_nicknames = config.getboolean('GUI', 'highlight_all_nicknames', fallback=False)
            self.log_on = config.getboolean('GUI', 'turn_logging_on', fallback=False)

            # Read Widget Settings
            self.user_listbox_fg = config.get('WIDGETS', 'users_fg', fallback='#39ff14')
            self.user_listbox_bg = config.get('WIDGETS', 'users_bg', fallback='black')
            self.user_label_bg = config.get('WIDGETS', 'user_label_bg', fallback='black')
            self.user_label_fg = config.get('WIDGETS', 'user_label_fg', fallback='white')
            self.away_user_fg = config.get('WIDGETS', 'away_user_fg', fallback='red')
            self.need_who_chan_fg = config.get('WIDGETS', 'need_who_chan_fg', fallback='red')
            self.channel_list_fg = config.get('WIDGETS', 'channels_fg', fallback='white')
            self.channel_list_bg = config.get('WIDGETS', 'channels_bg', fallback='black')
            self.input_fg = config.get('WIDGETS', 'entry_fg', fallback='#C0FFEE')
            self.input_bg = config.get('WIDGETS', 'entry_bg', fallback='black')
            self.input_insertbackground = config.get('WIDGETS', 'entry_insertbackground', fallback='#C0FFEE')
            self.input_label_bg = config.get('WIDGETS', 'entry_label_bg', fallback='black')
            self.input_label_fg = config.get('WIDGETS', 'entry_label_fg', fallback='#C0FFEE')
            self.server_list_bg = config.get('WIDGETS', 'server_list_bg', fallback='black')
            self.server_list_fg = config.get('WIDGETS', 'server_list_fg', fallback='white')
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
            self.font_family = 'Courier'
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
            self.channel_list_fg = 'white'
            self.channel_list_bg = 'black'
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
            if self.log_on:
                logging.error("GUI Fallbacks hit.")

    def init_layout(self):
        self.setLayout(QHBoxLayout(self))

        self.main_section = QVBoxLayout()
        self.main_section.setSpacing(5)

        self.topic_and_chat = QVBoxLayout()
        self.topic_and_chat.setSpacing(5)

        self.topic_label = QLabel(self, text="Topic: ")
        self.topic_label.setWordWrap(True)
        self.topic_and_chat.addWidget(self.topic_label)

        self.chat_box = RudeTextEdit(self)
        self.chat_box.setReadOnly(True)
        self.chat_box.setAcceptRichText(True)
        self.topic_and_chat.addWidget(self.chat_box)

        self.main_section.addLayout(self.topic_and_chat)

        self.message_bar = QHBoxLayout()
        self.message_bar.setSpacing(5)

        self.id_label = QLabel(self, text="Nickname | #Channel ▶")
        self.message_bar.addWidget(self.id_label)

        self.text_field = QLineEdit(self) # Bind TAB for tab complete.
        self.text_field.setFrame(False)
        QTimer.singleShot(0, self.bind_return_key)
        self.message_bar.addWidget(self.text_field)

        self.main_section.addLayout(self.message_bar)

        self.layout().addLayout(self.main_section)

        self.sidebar = QVBoxLayout()
        self.sidebar.setSpacing(5)

        self.user_selector = QVBoxLayout()

        self.user_selector_label = QLabel(self, text="Users (0)")
        self.user_selector_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.user_selector.addWidget(self.user_selector_label)

        self.user_selector_list = QListWidget(self)
        self.user_selector_list.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.user_selector_list.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.user_selector_list.setItemAlignment(Qt.AlignmentFlag.AlignLeading)
        self.user_selector.addWidget(self.user_selector_list)

        self.sidebar.addLayout(self.user_selector)

        self.server_selector = QVBoxLayout()

        self.server_selector_label = QLabel(self, text="Servers")
        self.server_selector_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.server_selector.addWidget(self.server_selector_label)

        self.server_selector_list = QListWidget(self)
        self.server_selector_list.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.server_selector_list.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.server_selector_list.itemClicked.connect(self.on_server_change)
        self.server_selector_list.setItemAlignment(Qt.AlignmentFlag.AlignLeading)
        self.server_selector.addWidget(self.server_selector_list)

        self.sidebar.addLayout(self.server_selector)

        self.channel_selector = QVBoxLayout()

        self.channel_selector_label = QLabel(self, text="Channels (0)")
        self.channel_selector_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.channel_selector.addWidget(self.channel_selector_label)

        self.channel_selector_list = QListWidget(self)
        self.channel_selector_list.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.channel_selector_list.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.channel_selector_list.itemClicked.connect(self.on_channel_click)
        self.channel_selector_list.setItemAlignment(Qt.AlignmentFlag.AlignLeading)
        self.channel_selector.addWidget(self.channel_selector_list)

        self.sidebar.addLayout(self.channel_selector)

        self.sidebar.setStretch(0, 2)
        self.sidebar.setStretch(1, 1)
        self.sidebar.setStretch(2, 2)

        self.layout().addLayout(self.sidebar)

    def set_gui_theme(self): # Add more gui configurations here. 
        chat_font = QFont(self.font_family, self.font_size)
        self.chat_box.setFont(chat_font)
        self.master.resize(self.app_size[0], self.app_size[1])

    def set_misc_variables(self):
        self.channel_lists = {}
        self.nickname_colors = self.load_nickname_colors()
        self.clients = {}
        self.channel_topics = {}
        self.url_cache = {}
        self.tag_cache = {}
        self.entry_history = []
        self.popped_out_channels = {}
        self.pop_out_windows = {}
        self.server_colors = {}
        self.emoji_width_cache = {}
        self.history_index = 0
        self.last_selected_index = None
        self.previous_server_index = None
        self.iconed = False
        self.target_user_info = None
        self.url_pattern = re.compile(r'(\w+://[^\s()<>]*\([^\s()<>]*\)[^\s()<>]*(?<![.,;!?])|www\.[^\s()<>]*\([^\s()<>]*\)[^\s()<>]*(?<![.,;!?])|\w+://[^\s()<>]+(?<![.,;!?])|www\.[^\s()<>]+(?<![.,;!?]))')
        self.nickname_pattern = re.compile(r'<([\S]+)>')
        self.users_nickname_pattern = lambda nickname: re.compile(r"\b" + re.escape(nickname) + r"\b")

    def init_client(self):
        self.irc_client = RudeChatClient(self.chat_box, self.text_field, self.master, self)
        self.init_input_menu()
        self.init_message_menu()
        self.init_server_menu()
        self.apply_settings()
        self.show_startup_art()

    def init_input_menu(self): pass #TODO

    def init_message_menu(self): pass #TODO

    def init_server_menu(self): pass #TODO

    def apply_settings(self):
        self.hidden_windows()
        self.highlight_nicknames()
        self.highlight_away_users()
        self.emoji_select()
        pass #TODO

    def hidden_windows(self): pass #TODO

    def emoji_select(self):
        match platform.system():
            case "Darwin": self.emoji_type = "Apple Color Emoji" #macOS
            case "Linux": self.emoji_type = "Noto Color Emoji"
            case "Windows": self.emoji_type = "Segoe UI Emoji"
            case _: self.emoji_type = "Arial" # A generic font as a last resort

    def bind_return_key(self):
        loop = asyncio.get_event_loop()
        self.text_field.returnPressed.connect(lambda: loop.create_task(self.on_enter_key(), name="on_enter_key"))

    # Tray Icon Management
    def create_tray_icon(self): pass #TODO

    def start_tray_icon(self):
        """Start the tray icon in a separate thread."""
        if platform.system() == "Darwin":
            self.to_tray = False
            return
        else:
            try:
                self.stop_tray_event = threading.Event()  # Event to stop the tray icon thread
                tray_thread = threading.Thread(target=self.create_tray_icon)
                tray_thread.daemon = True  # Make it a daemon thread so it will exit with the program
                tray_thread.start()
            except Exception as e:
                logging.error(f"Error starting tray icon: {e}")
                self.to_tray = False
                return

    def minimize_to_tray(self):
        """Minimize the window to the system tray."""
        if not self.to_tray:
            self.client_shutdown()
            return
        else:
            self.master.hide()  # Hide the window
            self.iconed = True

    # Client Management
    def add_client(self, server_name, irc_client):
        self.clients[server_name] = irc_client # Store clients here.

        # Get the current list of servers from the Listbox
        current_servers = [self.server_selector_list.item(i) for i in range (self.server_selector_list.count())]

        # Add the new server_name to the list if it's not already there
        if not any(server.text().startswith(server_name) for server in current_servers):
            current_servers.append(QListWidgetItem(str(server_name)))

        # Update the Listbox with the new list of servers
        for server in current_servers:
            self.server_selector_list.addItem(server)

        self.server_var = server_name  # Set the current server
        self.server_selector_list.setCurrentRow(0)
        self.channel_lists[server_name] = irc_client.joined_channels

    async def init_client_with_config(self, config_file, fallback_server_name):
        irc_client = None
        try:
            irc_client = RudeChatClient(self.chat_box, self.text_field, self.master, self)
            if self.log_on:
                logging.info(f"initializing client {irc_client} in progress")
            irc_client.client_event_loops[irc_client] = asyncio.get_event_loop()  # Store a reference to the event loop
            irc_client.tasks = {}  # Create a dictionary to store references to tasks
        except Exception as e:
            logging.error(f"Error initializing IRC client: {e}")
            return  # Stop further execution if client initialization fails

        try:
            irc_client.tasks["load_ascii_art_macros"] = asyncio.create_task(irc_client.load_ascii_art_macros(), name="load_ascii_art_macros_task")
            if self.log_on:
                logging.info(f"Created ASCII art task")
        except Exception as e:
            logging.error(f"Error loading ASCII art macros: {e}")

        try:
            await irc_client.read_config(config_file)
        except Exception as e:
            logging.error(f"Error reading configuration from {config_file}: {e}")

        try:
            await irc_client.connect(config_file)
        except Exception as e:
            logging.error(f"Error connecting with configuration {config_file}: {e}")

        try:
            # Use the server_name from config, otherwise fallback
            server_name = irc_client.server_name if irc_client.server_name else fallback_server_name
            self.add_client(server_name, irc_client)
        except Exception as e:
            logging.error(f"Error adding client {server_name}: {e}")

        try:
            # Create and store references to tasks
            irc_client.tasks["keep_alive"] = asyncio.create_task(irc_client.keep_alive(config_file), name="keep_alive_task")
        except Exception as e:
            logging.error(f"Error starting keep_alive task: {e}")

        try:
            irc_client.tasks["auto_save"] = asyncio.create_task(irc_client.auto_save(), name="auto_save_task")
        except Exception as e:
            logging.error(f"Error starting auto_save task: {e}")

        try:
            irc_client.tasks["auto_trim"] = asyncio.create_task(irc_client.auto_trim(), name="auto_trim_task")
        except Exception as e:
            logging.error(f"Error starting auto_trim task: {e}")

        try:
            irc_client.tasks["handle_incoming_message"] = asyncio.create_task(irc_client.handle_incoming_message(config_file), name="handle_incoming_message_task")
        except Exception as e:
            logging.error(f"Error starting handle_incoming_message task: {e}")

        try:
            irc_client.tasks["auto_who"] = asyncio.create_task(irc_client.request_who_for_all_channels(), name="auto_who_task")
        except Exception as e:
            logging.error(f"Error starting auto_who task: {e}")

        try:
            irc_client.tasks["auto_away"] = asyncio.create_task(irc_client.away_watcher(), name="auto_away_task")
        except Exception as e:
            logging.error(f"Error starting auto_away task: {e}")

        try:
            irc_client.tasks["auto_clean"] = asyncio.create_task(irc_client.the_cleaner(), name="auto_clean")
        except Exception as e:
            logging.error(f"Error starting auto_clean task: {e}")

        try:
            irc_client.tasks["away_update"] = asyncio.create_task(irc_client.away_updater(), name="away_update")
        except Exception as e:
            logging.error(f"Error starting away_updater task: {e}")

        try:
            irc_client.tasks["el_worker"] = asyncio.create_task(irc_client.the_worker(), name="la_worker")
        except Exception as e:
            logging.error(f"Error starting the_worker task: {e}") #thread_killer

        try:
            irc_client.tasks["who_missing_users"] = asyncio.create_task(irc_client.request_who_for_missing_users(), name="who_missing")
        except Exception as e:
            logging.error(f"Error starting request_who_for_missing_users task: {e}")

        try:
            irc_client.tasks["thread_killer"] = asyncio.create_task(irc_client.thread_killer(), name="thread_killer")
        except Exception as e:
            logging.error(f"Error starting thread_killer task: {e}")

        if self.log_on:
            logging.info("Finished Creating Client Tasks: auto_who, auto_away, handle_incoming_message, auto_trim, auto_save, & keep_alive")

        try:
            self.bind_return_key
        except Exception as e:
            logging.error(f"Error binding return key: {e}")
        if self.log_on:
            logging.info("Client initializing completed.")

    def update_server_ping(self, server_name, ping_time):
        """Update the entry for a server in the QListWidget with the new ping time."""
        for index in range(self.server_selector_list.count()):
            item = self.server_selector_list.item(index)
            if item.text().startswith(server_name):  # Find the matching server entry
                item.setText(f"{server_name} - {ping_time}")
                return

    def send_away_to_clients(self, away_message=None):
        if self.log_on:
            logging.info("Attempting AWAY with message")

        try:
            for server_name, irc_client in self.clients.items():
                # Assign the client reference
                client = irc_client

                if self.log_on:
                    logging.info(f"Client {client} AWAY attempt")

                loop = client.loop

                if self.log_on:
                    logging.info(f"Current Loop: {loop}")

                loop.create_task(client.send_away_notification(away_message), name="away_client_task")

                if self.log_on:
                    logging.info(f"Sending AWAY to client: {client}")
                    logging.info(f"AWAY Message: {away_message}")

        except Exception as e:
            logging.error(f"Error in send_away_to_clients: {e}")

    def quit_clients(self):
        if self.log_on:
            logging.info("Attempting to Quit Clients")

        try:
            for server_name, irc_client in self.clients.items():
                # Assign the client reference
                client = irc_client

                if self.log_on:
                    logging.info(f"Client {client} quit attempt")

                loop = client.loop

                if self.log_on:
                    logging.info(f"Current Loop: {loop}")

                loop.create_task(client.spec_quit(), name="quit_client_task")

                if self.log_on:
                    logging.info(f"Sending QUIT to client: {client}")

        except Exception as e:
            logging.error(f"Error in quit_clients: {e}")

    def quit_clients_with_message(self, quit_message):
        if self.log_on:
            logging.info("Attempting to Quit Clients With Message")

        try:
            for server_name, irc_client in self.clients.items():
                # Assign the client reference
                client = irc_client

                if self.log_on:
                    logging.info(f"Client {client} quit attempt")

                loop = client.loop

                if self.log_on:
                    logging.info(f"Current Loop: {loop}")

                loop.create_task(client.send_quit(quit_message), name="quit_client_task")

                if self.log_on:
                    logging.info(f"Sending QUIT to client: {client}")
                    logging.info(f"Quit Message: {quit_message}")

        except Exception as e:
            logging.error(f"Error in quit_clients: {e}")

    def client_shutdown(self):
        if self.log_on:
            logging.info(f"Attempting Client Shutdown.")

        try:
            # Shutdown the clients
            self.quit_clients()
        except Exception as e:
            logging.error(f"Error quitting Clients: {e}")

        try:
            # Destroy the GUI
            self.destroy_client()
        except Exception as e:
            logging.error(f"Error destroying clients: {e}")

    def destroy_client(self):
        try:
            self.master.close()
            sys.exit()
        except SystemExit:
            logging.info("SystemExit caught: Client Quit")
        except Exception as e:
            logging.error(f"Error When Destroying Client: {e}")

    # GUI
    def update_nick_channel_label(self):
        """Update the label with the current nickname and channel."""
        nickname = self.irc_client.nickname if self.irc_client.nickname else "Nickname"
        channel = self.irc_client.current_channel if self.irc_client.current_channel else "#Channel"
        user_mode = self.get_user_mode(nickname, channel)
        mode_symbol = self.get_mode_symbol(user_mode) if user_mode else ''
        self.id_label.setText( f"{mode_symbol}{nickname} | {channel}" + " ▷" )

    def update_users_label(self):
        if self.irc_client.server_name in self.irc_client.away_servers:
            away_text = f"You're Away"
            self.user_selector_label.setText(away_text)
            self.user_selector_label.setStyleSheet("color: red;")
        else:
            user_num = len(self.irc_client.channel_users.get(self.irc_client.current_channel, []))
            
            if user_num == 0:
                user_num = self.user_selector_list.count()

            back_text = f"Users ({user_num})"
            self.user_selector_label.setText(back_text)
            self.user_selector_label.setStyleSheet(f"color: white")
            
            if self.irc_client.server_name in self.irc_client.away_servers:
                self.irc_client.away_servers.remove(self.irc_client.server_name)

    def update_channel_label(self):
        channel_num = len(self.irc_client.joined_channels)
        label_text = f"Channels ({channel_num})"
        self.channel_selector_label.setText(label_text)

    def clear_topic_label(self):
        self.topic_label.setText("Topic: ")

    def clear_user_list(self):
        self.user_selector_list.clear()

    def clear_text_widget(self):
        self.chat_box.clear()

    def clear_chat_window(self):
        current_channel = self.irc_client.current_channel

        if current_channel:
            self.chat_box.clear()
            self.irc_client.channel_messages[self.irc_client.server][current_channel] = []

    def reload_macros(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.irc_client.update_available_macros())

    def open_color_selector(self): pass #TODO

    def reset_nick_colors(self): pass #TODO

    def open_client_config_window(self):
        def after_config_window_close():
            # Reload configuration after the configuration window is closed
            self.irc_client.reload_config(config_window.config_file)

        def close_window():
            self.main_window.close()

        def on_config_window_close():
            QTimer.singleShot(100, after_config_window_close)
            QTimer.singleShot(200, close_window)
            return

        self.main_window = QWidget()
        self.main_window.setWindowTitle("Rude Server configuration")
        self.main_window.resize(450, 500)

        files = os.listdir(G_CONFIG_DIR)
        config_files = [f for f in files if f.endswith(".rudeserver")]
        config_files.sort()

        if not config_files:
            QMessageBox.warning(self.main_window, "Warning", "No configuration files found.")
            self.main_window.close()
            return

        self.main_window.layout = QVBoxLayout(self.main_window)
        self.main_window.setContentsMargins(0, 0, 0, 0)

        config_window = ServerConfigWindow(self.main_window, os.path.join(G_CONFIG_DIR, config_files[0]), on_config_window_close)

        def on_config_change(event):
            selected_config_file = selected_config_file_var.currentText()
            config_window.config_file = os.path.join(G_CONFIG_DIR, selected_config_file)
            config_window.config.read(config_window.config_file)
            config_window.create_widgets()

        # Instruction label
        instruction_label = QLabel("To create a new config file, change the data in the fields, then edit the file name in the file selection above.\nConfiguration files must follow exampleserver.rudeserver format.")
        instruction_label.setWordWrap(True)
        self.main_window.layout.addWidget(instruction_label)

        # Menu to choose configuration file
        selected_config_file_var = QComboBox()
        selected_config_file_var.addItems(config_files)
        selected_config_file_var.currentIndexChanged.connect(on_config_change)
        self.main_window.layout.addWidget(selected_config_file_var)

        self.main_window.layout.addWidget(config_window.frame)

        save_button = QPushButton("Apply")
        save_button.clicked.connect(config_window.save_config)
        self.main_window.layout.addWidget(save_button)

        self.main_window.show()

    def open_gui_config_window(self): pass #TODO

    def show_startup_art(self):
        splash_directory = os.path.join(G_SOURCE_DIR, "Splash")

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
            logging.error(f"Error displaying startup art: {e}")

    def escape_color_codes(self, line):
        # Escape color codes in the string
        escaped_line = re.sub(r'\\x([0-9a-fA-F]{2})', lambda match: bytes.fromhex(match.group(1)).decode('utf-8'), line)
        
        return escaped_line

    # Event Handling
    def on_server_change(self, event):
        # Get the index of the currently selected server
        selected_server_index_tuple = [self.server_selector_list.currentIndex().row()]

        # If there's a selected server
        if selected_server_index_tuple:
            selected_server_index = selected_server_index_tuple[0]  # Extract the integer index

            # If there's a previous server, reset its background color to black
            if self.previous_server_index is not None:
                self.server_selector_list.item(self.previous_server_index).setBackground(QColor(self.server_list_bg))
                self.server_selector_list.item(self.previous_server_index).setForeground(QColor(self.server_list_fg))

            # Get the selected server from the listbox
            selected_server = self.server_selector_list.item(selected_server_index)
            clean_name = selected_server.text().split(" ")
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
                self.clear_user_list()
                self.clear_text_widget()

                # Display the MOTD if available
                self.show_startup_art()
                self.irc_client.display_server_motd(actual_server)
                self.update_users_label()
                self.highlight_nicknames()
                self.highlight_who_channels()
                self.update_channel_label()

                # Set the background color of the selected server to blue
                selected_server.setBackground(QColor(self.selected_list_server))
                selected_server.setForeground(QColor(self.server_list_fg))

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
                self.server_selector_list.item(server_index).setForeground(QColor(fg_color))
                self.server_selector_list.item(server_index).setBackground(QColor(bg_color))

            # Update the previous_server_index to the currently selected server index
            self.previous_server_index = selected_server_index

    def on_channel_click(self):
        # Set background of currently selected channel back to default
        current_selected_channel = self.irc_client.current_channel
        if current_selected_channel:
            for i in range(self.channel_selector_list.count()):
                if self.channel_selector_list.item(i).text() == current_selected_channel:
                    self.channel_selector_list.item(i).setBackground(QColor(self.channel_list_bg))
                    break

        # Get index of clicked item
        clicked_index = self.channel_selector_list.currentRow()
        clicked_channel = self.channel_selector_list.item(clicked_index)
        self.switch_channel(clicked_channel.text())

        # Turn background blue
        self.channel_selector_list.item(clicked_index).setBackground(QColor(self.channel_select_color))
        self.highlight_nicknames()
        self.highlight_away_users()
        self.update_users_label()

        # Remove the clicked channel from highlighted_channels dictionary
        if self.irc_client.server_name in self.irc_client.highlighted_channels:
            server_highlighted_channels = self.irc_client.highlighted_channels[self.irc_client.server_name]
            if clicked_channel.text() in server_highlighted_channels:
                del server_highlighted_channels[clicked_channel.text()]

    def switch_channel(self, channel_name):
        try:
            server = self.irc_client.server  # Assume the server is saved in the irc_client object
        except AttributeError as e:
            logging.error(f"AttributeError in switch_channel: server assignment {e}")
            return

        # Clear the text window
        self.chat_box.clear()

        # Print the current channel topics dictionary

        is_channel = any(channel_name.startswith(prefix) for prefix in self.irc_client.chantypes)

        if is_channel:
            # It's a channel
            if server in self.irc_client.channel_messages:

                self.irc_client.current_channel = channel_name
                self.update_nick_channel_label()

                # Update topic label
                current_topic = self.channel_topics.get(self.irc_client.server_name, {}).get(channel_name, "N/A")
                self.topic_label.setText(f"Topic: {current_topic}")

                # Display the last messages for the current channel
                self.irc_client.display_last_messages(channel_name, server_name=server)
                self.highlight_nicknames()

                self.irc_client.update_gui_user_list(channel_name)
                self.insert_and_scroll()

            else:
                self.insert_text_widget(f"Not a member of channel {channel_name}\n")

        else:
            self.clear_user_list()
            # Set current channel to the DM
            nickname = self.irc_client.nickname
            self.irc_client.current_channel = channel_name
            self.user_selector_list.addItem(nickname)
            self.user_selector_list.addItem(channel_name)
            self.update_nick_channel_label()

            # Display the last messages for the current DM
            self.irc_client.display_last_messages(channel_name, server_name=server)
            self.insert_and_scroll()
            self.highlight_nicknames()

            # No topic for DMs
            self.topic_label.setText(f"{channel_name}")

    async def on_enter_key(self):
        try:
            user_input = self.text_field.text()

            # Save the entered message to entry_history
            if user_input:
                self.entry_history.append(user_input)

                # Limit the entry_history to the last 10 messages
                if len(self.entry_history) > 10:
                    self.entry_history.pop(0)

                # Reset history_index to the end of entry_history
                self.history_index = len(self.entry_history)

            self.text_field.clear()
            await self.irc_client.command_parser(user_input)
        except Exception as e:
            print(e)

    # Text & Formatting
    def insert_text_widget(self, message):
        self.trim_text_widget()
        urls = self.find_urls(message)
        formatted_text = decoder(message)

        # Then apply other formatting
        self.tag_text(formatted_text)

        # Start tagging URLs using the non-blocking approach
        self.tag_urls(urls)
        self.insert_and_scroll()

    def trim_text_widget(self):
        """Trim the text widget to only hold a maximum of 1000 lines."""
        line_count = self.chat_box.document().blockCount()  # Get total line count
        if line_count > 1000:
            excess_lines = line_count - 1000
            cursor = self.chat_box.textCursor()
            cursor.movePosition(QTextCursor.Start)
            for _ in range(excess_lines):
                cursor.select(QTextCursor.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()

    def find_urls(self, text):
        # Use the precompiled regex pattern to find URLs
        return self.url_pattern.findall(text)

    def tag_text(self, formatted_text):
        cursor = self.chat_box.textCursor()
        for text, attributes in formatted_text:
            # Create a tag name based on the attributes
            tag_name = "_".join(str(attr) for attr in attributes)

            char_format = self.configure_tag_based_on_attributes(attributes)

            # Insert the formatted text with the current tag
            try:
                cursor.insertText(text, char_format)
            except Exception as e:
                logging.error(f"Error in tag_text: {e}")

    def configure_tag_based_on_attributes(self, attributes):
        try:
            # This method configures tag based on attributes efficiently
            tag_config = QTextCharFormat()
            tag_config.setFontFamily(self.font_family)
            tag_config.setFontPointSize(self.font_size)
            if any(attr.bold for attr in attributes):
                tag_config.setFontWeight(2)
            if any(attr.italic for attr in attributes):
                tag_config.setFontItalic(True)
            if any(attr.underline for attr in attributes):
                tag_config.setFontUnderline(True)
            if any(attr.strikethrough for attr in attributes):
                tag_config.setFontStrikeOut(True)
            if attributes and attributes[0].colour != 0:
                irc_color_code = f"{attributes[0].colour:02d}"
                hex_color = self.irc_colors.get(irc_color_code, 'white')
                tag_config.setForeground(QColor(hex_color))
            if attributes and attributes[0].background != 1:
                irc_background_code = f"{attributes[0].background:02d}"
                hex_background = self.irc_colors.get(irc_background_code, 'black')
                tag_config.setBackground(QColor(hex_background))
            return tag_config
        except Exception as e:
            logging.error(f"Error in configure_tag_based_on_attributes: {e}")

    def tag_urls(self, urls, index=0):
        if index < len(urls):
            url = urls[index]
            try:
                tag_name = f"url_{url}"
                char_format = QTextCharFormat()
                char_format.setAnchor(True)
                char_format.setAnchorHref(url)
            except Exception as e:
                logging.error(f"Error1 in tag_urls: {e}")
                
            try:
                char_format.setForeground(QColor("blue"))
                char_format.setFontUnderline(True)
                self.tag_cache[tag_name] = char_format

                cursor = self.chat_box.textCursor()
                cursor = self.chat_box.document().find(url, 0)
            except Exception as e:
                logging.error(f"Error2 in tag_urls: {e}")

            try:
                while not cursor.isNull():
                    cursor.mergeCharFormat(char_format)
                    cursor = self.chat_box.document().find(url, cursor)

                cursor = self.chat_box.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.Start) 
                while self.chat_box.find(url):
                    cursor.mergeCharFormat(self.tag_cache[tag_name])
                    cursor.setCharFormat(self.tag_cache[tag_name])
                    cursor.insertText(url, self.tag_cache[tag_name])
                    cursor.setPosition(cursor.position() + len(url))
            except Exception as e:
                logging.error(f"Error3 in tag_urls: {e}")

            # Schedule the next URL tagging
            QTimer.singleShot(1, lambda: self.tag_urls(urls, index + 1))
        else:
            self.insert_and_scroll()

    def insert_and_scroll(self):
        self.chat_box.moveCursor(QTextCursor.MoveOperation.End)

    def highlight_nicknames(self):
        """Highlight the user's nickname and other nicknames in text."""
        try:
            text = self.chat_box.toPlainText()

            # Highlight user's nickname first
            if not self.highlight_all_nicknames:
                user_nickname_matches = list(self.users_nickname_pattern(self.irc_client.nickname).finditer(text))
                for match in user_nickname_matches:
                    nickname = match.group(0)
                    start_position, end_position = match.span()
                    self.apply_nickname_format(text, start_position, end_position, nickname)

            elif self.highlight_all_nicknames:
                nicks_colors = list(self.nickname_colors.keys())
                for nicknames in nicks_colors:
                    modes_to_strip = ''.join(self.irc_client.mode_values)
                    strip_brakets = nicknames.strip('<>')
                    plain_nickname = strip_brakets.lstrip(modes_to_strip)
                    user_nickname_matches = list(self.users_nickname_pattern(plain_nickname).finditer(text))
                    for match in user_nickname_matches:
                        nickname = match.group(0)
                        start_position, end_position = match.span()
                        self.apply_nickname_format(text, start_position, end_position, nickname)

            # Highlight other nicknames
            if hasattr(self, 'nickname_pattern'):
                matches = list(self.nickname_pattern.finditer(text))
                for match in matches:
                    nickname_with_brackets = match.group(0)
                    start_position, end_position = match.span()
                    self.apply_nickname_format(text, start_position, end_position, nickname_with_brackets)

        except Exception as e:
            logging.error(f"Error in highlight_nicknames: {e}")

    def apply_nickname_format(self, text, start_position, end_position, nickname):
        """Apply color formatting to the nickname with emoji offset correction."""
        try:
            if not nickname:
                return
            modes = self.irc_client.mode_values + ['']
            modes_to_strip = ''.join(self.irc_client.mode_values)
            strip_brakets = nickname.strip('<>')
            plain_nickname = strip_brakets.lstrip(modes_to_strip)
            cursor = self.chat_box.textCursor()

            if f"<{plain_nickname}>" in self.nickname_colors:
                nickname_color = self.nickname_colors[f"<{plain_nickname}>"]
                # Cache the color for the nickname with modes
                self.nickname_colors[nickname] = nickname_color
            elif nickname == f"<{self.irc_client.nickname}>" and nickname not in self.nickname_colors:
                nickname_color = self.user_nickname_color
                self.nickname_colors[f"<{plain_nickname}>"] = nickname_color
            else:
                if self.generate_nickname_colors:
                    nickname_color = self.generate_random_color()
                else:
                    nickname_color = self.main_fg_color

                for mode in modes:
                    if nickname == f"<{mode}{self.irc_client.nickname}>":
                        nickname_color = self.user_nickname_color

                self.nickname_colors[nickname] = nickname_color
                self.nickname_colors[f"<{plain_nickname}>"] = nickname_color

            format_nick = QTextCharFormat()
            format_nick.setFontFamily(self.font_family)
            format_nick.setFontPointSize(self.font_size)
            format_nick.setForeground(QColor(nickname_color))

            # Calculate emoji offset
            emoji_offset_start, emoji_offset_end = self.calculate_emoji_offsets(text, start_position, end_position)
            adjusted_start = start_position + emoji_offset_start
            adjusted_end = end_position + emoji_offset_end

            # Apply the color formatting
            cursor.setPosition(adjusted_start)
            cursor.setPosition(adjusted_end, QTextCursor.MoveMode.KeepAnchor)
            cursor.setCharFormat(format_nick)
        except Exception as e:
            logging.error(f"Error in apply_nickname_format: {e}")

    def get_text_width(self, text, font):
        """Measure the width of text using QFontMetrics, with caching."""
        if text in self.emoji_width_cache:
            return self.emoji_width_cache[text]

        metrics = QFontMetrics(font)
        width = metrics.horizontalAdvance(text)  # Get the width of the text
        self.emoji_width_cache[text] = width  # Cache result
        return width

    def estimate_emoji_offset(self, text, font):
        """Estimate emoji offset based on their visual width, using caching."""
        normal_char_width = self.get_text_width("A", font)  # Reference width

        emoji_offsets = {}

        for char in set(text):  # Process only unique characters
            if self.is_emoji(char):  # Only measure emojis
                width = self.get_text_width(char, font)
                raw_offset = width / normal_char_width

                if char in self.SPECIAL_EMO_CASES:
                    offset = self.SPECIAL_EMO_CASES[char]
                else:
                    offset = max(0, round(raw_offset) - 1)

                emoji_offsets[char] = offset

        return emoji_offsets

    def calculate_emoji_offsets(self, text, start_position, end_position):
        """Calculate emoji offsets dynamically based on their rendered width."""
        emoji_offset_start = 0
        emoji_offset_end = 0
        font = self.chat_box.font()  # Get the current font
        emoji_widths = self.estimate_emoji_offset(text, font)  # Estimate emoji widths

        for i, char in enumerate(text):
            if char in emoji_widths:
                extra_offset = emoji_widths[char]  # Get cached width

                if i < start_position:
                    emoji_offset_start += extra_offset
                if i < end_position:
                    emoji_offset_end += extra_offset

        return emoji_offset_start, emoji_offset_end

    def is_emoji(self, char):
        """Check if a character is an emoji using the emoji library."""
        return char in emoji.EMOJI_DATA

    def generate_random_color(self):
        while True:
            # Generate random values for each channel
            r = random.randint(50, 255)
            g = random.randint(50, 255)
            b = random.randint(50, 255)
            
            if max(r, g, b) - min(r, g, b) > 50:
                return "#{:02x}{:02x}{:02x}".format(r, g, b)

    def highlight_away_users(self):
        try:
            # Loop through the items in the user_selector_list
            for index in range(self.user_selector_list.count()):
                # Get the user from the listbox
                user_item = self.user_selector_list.item(index)
                if not user_item:
                    continue  # If the item is not found, skip it

                # Get the user name
                user = user_item.text()
                modes_to_strip = ''.join(self.irc_client.mode_values)
                strip_user = user.lstrip(modes_to_strip)

                # Check if the user is in the away_users_dict
                if strip_user in self.irc_client.away_users_dict:
                    # Change the foreground color 
                    user_item.setForeground(QColor(self.away_user_fg))
                else:
                    # Reset the foreground color 
                    user_item.setForeground(QColor(self.user_listbox_fg))
            
            # Update the UI to reflect changes
            self.user_selector_list.update()
            
        except Exception as e:
            logging.error(f"Exception in highlight_away_users: {e}")

    def highlight_who_channels(self):
        try:
            # Loop through the items in the channel_list
            for index in range(self.channel_selector_list.count()):
                # Get the channel from the listbox (which should be a QListWidgetItem)
                channel_item = self.channel_selector_list.item(index)
                if not channel_item:
                    continue  # If the item is not found, skip it

                # Get the channel name (assuming item text is the channel name)
                channel = channel_item.text()

                # Check if the channel is in the cap_who_for_chan list
                if channel in self.irc_client.cap_who_for_chan:
                    # Change the foreground color 
                    channel_item.setForeground(QColor(self.channel_list_fg))
                else:
                    # Reset the foreground color 
                    channel_item.setForeground(QColor(self.need_who_chan_fg))
            
            # Update the UI to reflect changes
            self.channel_selector_list.update()
            
        except Exception as e:
            logging.error(f"Exception in highlight_who_channels: {e}")

    # Utility
    def get_mode_symbol(self, mode):
        """Return the symbol corresponding to the IRC mode."""
        return self.irc_client.mode_to_symbol.get(mode, '')

    def get_user_mode(self, user, channel):
        """Retrieve the user's mode for the given channel."""
        channel_modes = self.irc_client.user_modes.get(channel, {})
        user_modes = channel_modes.get(user, set())
        return next(iter(user_modes), None)  # Get the first mode if available, else None

    def load_nickname_colors(self):
        nickname_colors_path = os.path.join(G_CONFIG_DIR, 'nickname_colours.json')

        try:
            with open(nickname_colors_path, 'r') as file:
                nickname_colors = json.load(file)
            return nickname_colors
        except FileNotFoundError:
            logging.error(f"Nickname colors file not found at {nickname_colors_path}. Returning an empty dictionary.")
            return {}
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON in nickname colors file: {e}. Returning an empty dictionary.")
            return {}
        except Exception as e:
            logging.error(f"An unexpected error occurred while loading nickname colors: {e}. Returning an empty dictionary.")
            return {}
        
    def save_nickname_colors(self):
        clean_nicks = clean_nicknames(self.nickname_colors)
        nickname_colors_path = os.path.join(G_CONFIG_DIR, 'nickname_colours.json')

        try:
            with open(nickname_colors_path, 'w') as file:
                json.dump(clean_nicks, file, indent=2)
        except Exception as e:
            logging.error(f"An unexpected error occurred while saving nickname colors: {e}. Unable to save nickname colors.")

    def open_url(self, url):
        webbrowser.open(url)

    # Unused (but maybe used in the future)
    def find_nicks_in_brackets(self, text):
        # Match a space followed by '<', then the nickname inside <>, and then a space after '>'
        nick_matches = list(re.finditer(r"<([^<>]+)>", text))
        return nick_matches