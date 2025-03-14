from rudechat4.shared_imports import *
from rudechat4.global_variables import *
from rudechat4.rude_client import RudeChatClient
from rudechat4.nick_cleaner import clean_nicknames
from rudechat4.format_decoder import decoder

class RudeTextEdit(QTextEdit):
    def mousePressEvent(self, e):
        if self.is_anchor_at(e.pos()):
            url = self.get_anchor_at(e.pos())
            webbrowser.open(url)
        else:
            e.ignore()

    def is_anchor_at(self, pos):
        cursor = self.cursorForPosition(pos)
        return cursor.charFormat().isAnchor()
    
    def get_anchor_at(self, pos):
        cursor = self.cursorForPosition(pos)
        char_format = cursor.charFormat()
        if char_format.isAnchor():
            return char_format.anchorHref()


class RudeGui(QWidget):
    def __init__(self, master):
        super().__init__()
        self.master = master
        self.app_size = [800, 600]
        self.set_screen_size()
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

        # Initialise layout
        self.init_layout()

        # Initialise other instance variables
        self.set_misc_variables()

        # Initialise client
        self.init_client()

        self.master.clear_chat_window = self.clear_chat_window
        self.master.reload_macros = self.reload_macros

        self.master.open_color_selector = self.open_color_selector
        self.master.save_nickname_colors = self.save_nickname_colors
        self.master.reset_nick_colors = self.reset_nick_colors

        self.master.open_client_config_window = self.open_client_config_window
        self.master.open_gui_config_window = self.open_gui_config_window

        self.master.chat_clear_chat_action.triggered.disconnect()
        self.master.chat_reload_macros_action.triggered.disconnect()
        self.master.colors_color_selector_action.triggered.disconnect()
        self.master.colors_save_colors_action.triggered.disconnect()
        self.master.colors_reset_colors_action.triggered.disconnect()
        self.master.config_edit_servers_action.triggered.disconnect()
        self.master.config_edit_gui_action.triggered.disconnect()

        self.master.chat_clear_chat_action.triggered.connect(self.clear_chat_window)
        self.master.chat_reload_macros_action.triggered.connect(self.reload_macros)
        self.master.colors_color_selector_action.triggered.connect(self.open_color_selector)
        self.master.colors_save_colors_action.triggered.connect(self.save_nickname_colors)
        self.master.colors_reset_colors_action.triggered.connect(self.reset_nick_colors)
        self.master.config_edit_servers_action.triggered.connect(self.open_client_config_window)
        self.master.config_edit_gui_action.triggered.connect(self.open_gui_config_window)

        #TODO: set up keybinds

    def clear_chat_window(self):
        print("clear_chat_window")
        pass #TODO

    def reload_macros(self):
        print("reload_macros")
        pass #TODO

    def open_color_selector(self):
        print("open_color_selector")
        pass #TODO

    def reset_nick_colors(self):
        print("reset_nick_colors")
        pass #TODO

    def open_client_config_window(self):
        print("open_client_config_window")
        pass #TODO

    def open_gui_config_window(self):
        print("open_gui_config_window")
        pass #TODO

    def set_screen_size(self):
        pass #TODO

    def set_icon(self):
        pass #TODO

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
            self.log_on = config.getboolean('GUI', 'turn_logging_on', fallback=False)

            # Read Widget Settings
            self.user_listbox_fg = config.get('WIDGETS', 'users_fg', fallback='#39ff14')
            self.user_listbox_bg = config.get('WIDGETS', 'users_bg', fallback='black')
            self.user_label_bg = config.get('WIDGETS', 'user_label_bg', fallback='black')
            self.user_label_fg = config.get('WIDGETS', 'user_label_fg', fallback='white')
            self.away_user_fg = config.get('WIDGETS', 'away_user_fg', fallback='red')
            self.need_who_chan_fg = config.get('WIDGETS', 'need_who_chan_fg', fallback='red')
            self.channelList_fg = config.get('WIDGETS', 'channels_fg', fallback='white')
            self.channelList_bg = config.get('WIDGETS', 'channels_bg', fallback='black')
            self.input_fg = config.get('WIDGETS', 'entry_fg', fallback='#C0FFEE')
            self.input_bg = config.get('WIDGETS', 'entry_bg', fallback='black')
            self.input_insertbackground = config.get('WIDGETS', 'entry_insertbackground', fallback='#C0FFEE')
            self.input_label_bg = config.get('WIDGETS', 'entry_label_bg', fallback='black')
            self.input_label_fg = config.get('WIDGETS', 'entry_label_fg', fallback='#C0FFEE')
            self.server_list_bg = config.get('WIDGETS', 'serverList_bg', fallback='black')
            self.server_list_fg = config.get('WIDGETS', 'serverList_fg', fallback='white')
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
            self.channelList_fg = 'white'
            self.channelList_bg = 'black'
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

    def init_layout(self):
        self.setLayout(QHBoxLayout(self))

        self.mainSection = QVBoxLayout()
        self.mainSection.setSpacing(5)

        self.chatArea = QVBoxLayout()
        self.chatArea.setSpacing(5)

        self.current_topic = "Topic: "

        self.topicLabel = QLabel(self, text=self.current_topic)
        self.topicLabel.setWordWrap(True)
        self.chatArea.addWidget(self.topicLabel)

        self.displayText = RudeTextEdit(self)
        self.displayText.setReadOnly(True)
        self.displayText.setAcceptRichText(True)
        self.chatArea.addWidget(self.displayText)

        self.mainSection.addLayout(self.chatArea)

        self.textInput = QHBoxLayout()
        self.textInput.setSpacing(5)

        self.current_nick_channel = "Nickname | #Channel" + " ▶"

        self.userChanDisplay = QLabel(self, text=self.current_nick_channel)
        self.textInput.addWidget(self.userChanDisplay)

        self.inputField = QLineEdit(self)
        
        QTimer.singleShot(0, self.bind_return_key)

        self.textInput.addWidget(self.inputField)

        self.mainSection.addLayout(self.textInput)

        self.layout().addLayout(self.mainSection)

        self.sidebar = QVBoxLayout()
        self.sidebar.setSpacing(5)

        self.usersSelector = QVBoxLayout()

        self.usersLabel = QLabel(self, text="Users (0)")
        self.usersSelector.addWidget(self.usersLabel)

        self.userList = QListWidget(self)
        self.userList.setResizeMode(QListView.ResizeMode.Adjust)
        self.userList.setItemAlignment(Qt.AlignmentFlag.AlignLeading)
        self.usersSelector.addWidget(self.userList)

        self.sidebar.addLayout(self.usersSelector)

        self.serversSelector = QVBoxLayout()

        self.server_var = ""

        self.serversLabel = QLabel(self, text="Servers")
        self.serversSelector.addWidget(self.serversLabel)

        self.serverList = QListWidget(self)
        self.serverList.setResizeMode(QListView.ResizeMode.Adjust)
        self.serverList.itemClicked.connect(self.on_server_change)
        self.serverList.setItemAlignment(Qt.AlignmentFlag.AlignLeading)
        self.serversSelector.addWidget(self.serverList)

        self.sidebar.addLayout(self.serversSelector)
        
        self.channelsSelector = QVBoxLayout()

        self.channelsLabel = QLabel(self, text="Channels (0)")
        self.channelsSelector.addWidget(self.channelsLabel)

        self.channelList = QListWidget(self)
        self.channelList.setResizeMode(QListView.ResizeMode.Adjust) 
        self.channelList.itemClicked.connect(self.on_channel_click)
        self.channelList.setItemAlignment(Qt.AlignmentFlag.AlignLeading)
        self.channelsSelector.addWidget(self.channelList)

        self.sidebar.addLayout(self.channelsSelector)

        self.sidebar.setStretch(0, 2)
        self.sidebar.setStretch(1, 1)
        self.sidebar.setStretch(2, 2)

        self.layout().addLayout(self.sidebar)

        self.layout().setStretch(0, 5)
        self.layout().setStretch(1, 1)

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
        self.history_index = 0
        self.last_selected_index = None
        self.previous_server_index = None
        self.iconed = False
        self.target_user_info = None
        self.url_pattern = re.compile(r'(\w+://[^\s()<>]*\([^\s()<>]*\)[^\s()<>]*(?<![.,;!?])|www\.[^\s()<>]*\([^\s()<>]*\)[^\s()<>]*(?<![.,;!?])|\w+://[^\s()<>]+(?<![.,;!?])|www\.[^\s()<>]+(?<![.,;!?]))')

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

    def init_client(self):
        self.irc_client = RudeChatClient(self.displayText, self.inputField, self.master, self)
        self.init_input_menu()
        self.init_message_menu()
        self.init_server_menu()
        self.apply_settings()
        self.show_startup_art()
        # self.master.protocol("WM_DELETE_WINDOW", self.minimize_to_tray) TODO

    def init_input_menu(self):
        pass #TODO

    def init_message_menu(self):
        pass #TODO

    def init_server_menu(self):
        pass #TODO

    def apply_settings(self):
        self.hidden_windows()
        self.highlight_nicknames()
        self.highlight_away_users()
        self.emoji_select()
        pass #TODO

    def hidden_windows(self):
        pass #TODO

    def highlight_away_users(self):
        pass #TODO

    def emoji_select(self):
        if platform.system() == "Darwin":  # macOS
            self.emoji_type = "Apple Color Emoji"
        elif platform.system() == "Linux":
            # Check for the Noto Color Emoji font, a common default on Linux
            self.emoji_type = "Noto Color Emoji"
        elif platform.system() == "Windows":
            # Use Segoe UI Emoji for Windows
            self.emoji_type = "Segoe UI Emoji"
        else:
            # Fallback for unknown systems
            self.emoji_type = "Arial"  # A generic font as a last resort

    async def init_client_with_config(self, config_file, fallback_server_name):
        irc_client = None
        try:
            irc_client = RudeChatClient(self.displayText, self.inputField, self.master, self)
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

    def bind_return_key(self):
        loop = asyncio.get_event_loop()
        # self.entry_widget.bind('<Return>', lambda event: loop.create_task(self.on_enter_key(event), name="on_enter_key")) TODO

    def highlight_who_channels(self):
        try:
            # Loop through the items in the channelList
            for index in range(self.channelList.count()):
                # Get the channel from the listbox
                channel = self.channelList.item(index)

                # Check if the stripped channel is in the away_users list
                if channel in self.irc_client.cap_who_for_chan:
                    # Make sure the index exists in the channelList
                    if 0 <= index < self.channelList.count():
                        # Change the foreground color 
                        channel.setForeground(QColor(self.channelList_fg))
                else:
                    # Make sure the index exists in the channelList
                    if 0 <= index < self.channelList.count():
                        # Reset the foreground color 
                        channel.setForeground(QColor(self.need_who_chan_fg))
        except Exception as e:
            logging.error(f"Exception in highlight_who_channels: {e}")
    
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
        self.userChanDisplay.setText( f"{mode_symbol}{nickname} | {channel}" + " ▷" )

    def trim_text_widget(self):
        """Trim the text widget to only hold a maximum of 1000 lines."""
        line_count = self.displayText.document().blockCount()  # Get total line count
        if line_count > 1000:
            excess_lines = line_count - 1000
            cursor = self.displayText.textCursor()
            cursor.movePosition(QTextCursor.Start)
            for _ in range(excess_lines):
                cursor.select(QTextCursor.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()

    def find_nicks_in_brackets(self, text):
        # Match a space followed by '<', then the nickname inside <>, and then a space after '>'
        nick_matches = list(re.finditer(r"<([^<>]+)>", text))
        return nick_matches

    def find_urls(self, text):
        # Use the precompiled regex pattern to find URLs
        return self.url_pattern.findall(text)

    def find_emojis(self, text):
        # Detect emojis in the text
        return [char for char in text if char in emoji.EMOJI_DATA]
    
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

    def tag_text(self, formatted_text):
        cursor = self.displayText.textCursor()
        for text, attributes in formatted_text:
            # Create a tag name based on the attributes
            tag_name = "_".join(str(attr) for attr in attributes)

            char_format = self.configure_tag_based_on_attributes(attributes)

            # Insert the formatted text with the current tag
            try:
                cursor.insertText(text, char_format)
            except Exception as e:
                logging.error(f"Error in tag_text: {e}")

    def insert_and_scroll(self):
        self.displayText.moveCursor(QTextCursor.MoveOperation.End)

    def tag_urls(self, urls, index=0):
        if index < len(urls):
            url = urls[index]
            if url in self.url_cache:
                tag_name = self.url_cache[url]
            else:
                try:
                    tag_name = f"url_{url}"
                    self.url_cache[url] = tag_name
                    char_format = QTextCharFormat()
                    char_format.setAnchor(True)
                    char_format.setAnchorHref(url)
                except Exception as e:
                    logging.error(f"Error1 in tag_urls: {e}")
                
                try:
                    char_format.setForeground(QColor("blue"))
                    char_format.setFontUnderline(True)
                    self.tag_cache[tag_name] = char_format

                    cursor = self.displayText.textCursor()
                    cursor = self.displayText.document().find(url, 0)
                except Exception as e:
                    logging.error(f"Error2 in tag_urls: {e}")

                try:
                    while not cursor.isNull():
                        cursor.mergeCharFormat(char_format)
                        cursor = self.displayText.document().find(url, cursor)

                    cursor = self.displayText.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.Start) 
                    while self.displayText.find(url):
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

    def tag_emojis(self, emojis, message):
        try:
            cursor = self.displayText.textCursor()
            for emoji_char in emojis:
                # Create a unique tag for each emoji
                tag_name = f"emoji_{emoji_char}"
                if tag_name not in self.tag_cache:
                    # Configure format for emoji with larger font and color
                    char_format = QTextCharFormat()
                    char_format.setFontPointSize(self.font_size + 5)
                    char_format.setForeground(QColor(self.main_fg_color))
                    char_format.setFontFamily(self.emoji_type)
                    self.tag_cache[tag_name] = char_format

                # Find and tag all occurrences of the emoji
                start_idx = 0
                while True:
                    start_idx = message.find(emoji_char, start_idx)
                    if start_idx == -1:
                        break
                    cursor.setPosition(start_idx)
                    cursor.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor, len(emoji_char))
                    cursor.setCharFormat(self.tag_cache[tag_name])
                    start_idx += len(emoji_char)
        except Exception as e:
            logging.error(f"Error in tag_emojis: {e}")

    def clear_text_widget(self):
        self.displayText.clear()

    def generate_random_color(self):
        while True:
            # Generate random values for each channel
            r = random.randint(50, 255)
            g = random.randint(50, 255)
            b = random.randint(50, 255)
            
            # Ensure the difference between the maximum and minimum channel values is above a threshold
            if max(r, g, b) - min(r, g, b) > 50:  # 50 is the threshold, you can adjust this value as needed
                return "#{:02x}{:02x}{:02x}".format(r, g, b)

    def is_emoji(self, char):
        return char in emoji.EMOJI_DATA

    def highlight_nicknames(self):
        """Highlight the user's nickname and other nicknames in text."""
        try:
            user_nickname = self.irc_client.nickname

            cursor = self.displayText.textCursor()
            text = self.displayText.toPlainText()

            start_position = text.find('<')
            while start_position != -1:
                end_position = text.find('>', start_position)
                if end_position == -1:
                    break

                nickname_with_brackets = text[start_position:end_position + 1]
                nickname = nickname_with_brackets.strip('<>')

                self.apply_nickname_format(text, start_position, end_position + 1, nickname)

                start_position = text.find('<', end_position + 1)
        except Exception as e:
            logging.error(f"Error in highlight_nicknames: {e}")

    def apply_nickname_format(self, text, start_position, end_position, nickname):
        """Apply color formatting to the nickname with emoji offset correction."""
        try:
            cursor = self.displayText.textCursor()

            if f"<{nickname}>" in self.nickname_colors:
                nickname_color = self.nickname_colors[f"<{nickname}>"]
            else:
                if self.generate_nickname_colors:
                    nickname_color = self.generate_random_color()
                else:
                    nickname_color = self.main_fg_color

                self.nickname_colors[f"<{nickname}>"] = nickname_color

            format_nick = QTextCharFormat()
            format_nick.setFontFamily(self.font_family)
            format_nick.setFontPointSize(self.font_size)
            format_nick.setForeground(QColor(nickname_color))

            # Calculate emoji offset
            emoji_offset_start = 0
            for i in range(start_position):
                if self.is_emoji(text[i]):
                    emoji_offset_start += 1

            emoji_offset_end = 0
            for i in range(end_position):
                if self.is_emoji(text[i]):
                    emoji_offset_end += 1

            # Adjust start and end positions with the calculated offset
            if platform.system() == "Darwin":
                adjusted_start = start_position + emoji_offset_start
                adjusted_end = end_position + emoji_offset_end
            elif platform.system() == "Linux":
                adjusted_start = start_position + emoji_offset_start - 1
                adjusted_end = end_position + emoji_offset_end - 1
            elif platform.system() == "Windows":
                adjusted_start = start_position + emoji_offset_start
                adjusted_end = end_position + emoji_offset_end

            # Apply the color formatting
            cursor.setPosition(adjusted_start)
            cursor.setPosition(adjusted_end, QTextCursor.MoveMode.KeepAnchor)
            cursor.setCharFormat(format_nick)
        except Exception as e:
            logging.error(f"Error in apply_nickname_format: {e}")

    def insert_text_widget(self, message):
        self.trim_text_widget()
        urls = self.find_urls(message)
        emojis = self.find_emojis(message)

        formatted_text = decoder(message)

        # Then apply other formatting
        self.tag_text(formatted_text)

        # Start tagging URLs using the non-blocking approach
        self.tag_urls(urls)
        self.tag_emojis(emojis, message)
        self.insert_and_scroll()

    def open_url(self, url):
        webbrowser.open(url)

    def escape_color_codes(self, line):
        # Escape color codes in the string
        escaped_line = re.sub(r'\\x([0-9a-fA-F]{2})', lambda match: bytes.fromhex(match.group(1)).decode('utf-8'), line)
        
        return escaped_line

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

    def add_client(self, server_name, irc_client):
        self.clients[server_name] = irc_client # Store clients here.

        # Get the current list of servers from the Listbox
        current_servers = [self.serverList.item(i) for i in range (self.serverList.count())]

        # Add the new server_name to the list if it's not already there
        if not any(server.text().startswith(server_name) for server in current_servers):
            current_servers.append(QListWidgetItem(str(server_name)))

        # Update the Listbox with the new list of servers
        for server in current_servers:
            self.serverList.addItem(server)

        self.server_var = server_name  # Set the current server
        self.serverList.setCurrentRow(0)
        self.channel_lists[server_name] = irc_client.joined_channels

    def clear_topic_label(self):
        self.topicLabel.setText("Topic: ")

    def clear_user_list(self):
        self.userList.clear()

    def update_users_label(self):
        if self.irc_client.server_name in self.irc_client.away_servers:
            away_text = f"You're Away"
            self.usersLabel.setText(away_text)
            self.usersLabel.setStyleSheet("color: red;")
        else:
            user_num = len(self.irc_client.channel_users.get(self.irc_client.current_channel, []))
            
            if user_num == 0:
                user_num = self.userList.count()

            back_text = f"Users ({user_num})"
            self.usersLabel.setText(back_text)
            self.usersLabel.setStyleSheet(f"color: initial")
            
            if self.irc_client.server_name in self.irc_client.away_servers:
                self.irc_client.away_servers.remove(self.irc_client.server_name)

    def update_channel_label(self):
        channel_num = len(self.irc_client.joined_channels)
        label_text = f"Channels ({channel_num})"
        self.channelsLabel.setText(label_text)

    def on_server_change(self, event):
        # Get the index of the currently selected server
        selected_server_index_tuple = [self.serverList.currentIndex().row()]

        # If there's a selected server
        if selected_server_index_tuple:
            selected_server_index = selected_server_index_tuple[0]  # Extract the integer index

            # If there's a previous server, reset its background color to black
            if self.previous_server_index is not None:
                self.serverList.item(self.previous_server_index).setBackground(QColor(self.server_list_bg))
                self.serverList.item(self.previous_server_index).setForeground(QColor(self.server_list_fg))

            # Get the selected server from the listbox
            selected_server = self.serverList.item(selected_server_index)
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
                self.serverList.item(server_index).setForeground(QColor(fg_color))
                self.serverList.item(server_index).setBackground(QColor(bg_color))

            # Update the previous_server_index to the currently selected server index
            self.previous_server_index = selected_server_index

    def on_channel_click(self):
        # Set background of currently selected channel back to default
        current_selected_channel = self.irc_client.current_channel
        if current_selected_channel:
            for i in range(self.channelList.count()):
                if self.channelList.item(i).text() == current_selected_channel:
                    self.channelList.item(i).setBackground(QColor(self.channelList_bg))
                    break

        # Get index of clicked item
        clicked_index = self.channelList.currentRow()
        clicked_channel = self.channelList.item(clicked_index)
        self.switch_channel(clicked_channel.text())

        # Turn background blue
        self.channelList.item(clicked_index).setBackground(QColor(self.channel_select_color))
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
        self.displayText.clear()

        # Print the current channel topics dictionary

        is_channel = any(channel_name.startswith(prefix) for prefix in self.irc_client.chantypes)

        if is_channel:
            # It's a channel
            if server in self.irc_client.channel_messages:

                self.irc_client.current_channel = channel_name
                self.update_nick_channel_label()

                # Update topic label
                current_topic = self.channel_topics.get(self.irc_client.server_name, {}).get(channel_name, "N/A")
                self.topicLabel.setText(f"Topic: {current_topic}")

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
            self.userList.addItem(nickname)
            self.userList.addItem(channel_name)
            self.update_nick_channel_label()

            # Display the last messages for the current DM
            self.irc_client.display_last_messages(channel_name, server_name=server)
            self.insert_and_scroll()
            self.highlight_nicknames()

            # No topic for DMs
            self.topicLabel.setText(f"{channel_name}")

    async def on_enter_key(self):
        try:
            user_input = self.inputField.text()

            # Save the entered message to entry_history
            if user_input:
                self.entry_history.append(user_input)

                # Limit the entry_history to the last 10 messages
                if len(self.entry_history) > 10:
                    self.entry_history.pop(0)

                # Reset history_index to the end of entry_history
                self.history_index = len(self.entry_history)

            self.inputField.clear()
            await self.irc_client.command_parser(user_input)
        except Exception as e:
            print(e)
        
    def bind_return_key(self):
        loop = asyncio.get_event_loop()
        self.inputField.returnPressed.connect(lambda: loop.create_task(self.on_enter_key(), name="on_enter_key"))

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

    def minimize_to_tray(self):
        """Minimize the window to the system tray."""
        if not self.to_tray:
            self.client_shutdown()
            return
        else:
            self.master.hide()  # Hide the window
            self.iconed = True
    
    def client_shutdown(self):
        if self.log_on:
            logging.info(f"Attempting Client Shutdown.")

        try:
            # Shutdown the clients
            self.quit_clients()
        except Exception as e:
            logging.error(f"Error quitting Clients: {e}")

        try:
            # Stop and remove the tray icon
            self.remove_tray_icon()
        except Exception as e:
            logging.error(f"Error Removing Tray Icon: {e}")

        try:
            # Destroy the GUI
            self.destroy_client()
        except Exception as e:
            logging.error(f"Error destroying clients: {e}")

    def destroy_client(self):
        try:
            self.master.destroy(True)
            sys.exit()
        except Exception as e:
            logging.error(f"Error When Destroying Client: {e}")

    def remove_tray_icon(self):
        if hasattr(self, 'tray_icon'):
            self.stop_tray_event.set()
            # self.tray_icon.stop()
