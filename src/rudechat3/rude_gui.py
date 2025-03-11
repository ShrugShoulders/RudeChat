from rudechat3.shared_imports import *
from rudechat3.global_variables import *
from rudechat3.rude_client import RudeChatClient
from rudechat3.nick_cleaner import clean_nicknames

class RudeGui:
    def __init__(self, master):
        self.master = master
        self.app_size = [800, 600]
        self.set_screen_size()
        self.master.resize(self.app_size[0], self.app_size[1])

        self.set_icon()

        self.read_config()
        self.start_tray_icon()

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
        self.initLayout()

        # Initialise other instance variables
        self.set_misc_variables()

        # Initialise client
        self.init_client()

        #TODO: set up keybinds

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
        pass #TODO

    def initLayout(self):
        self.centralWidget = QWidget(self.master)
        self.centralWidget.setWindowTitle("RudeChat")

        self.frame = QHBoxLayout(self.centralWidget)
        self.frame.setContentsMargins(5, 5, 5, 5)

        self.mainSection = QVBoxLayout()
        self.mainSection.setSpacing(5)

        self.chatArea = QVBoxLayout()
        self.chatArea.setSpacing(5)

        self.topicLabel = QLabel(self.centralWidget, text="Topic: ")
        self.chatArea.addWidget(self.topicLabel)

        self.displayText = QTextBrowser(self.centralWidget)
        self.chatArea.addWidget(self.displayText)

        self.mainSection.addLayout(self.chatArea)

        self.textInput = QHBoxLayout()
        self.textInput.setSpacing(5)

        self.current_nick_channel = "Nickname | #Channel" + " ▶"

        self.userChanDisplay = QLabel(self.centralWidget, text=self.current_nick_channel)
        self.textInput.addWidget(self.userChanDisplay)

        self.inputField = QLineEdit(self.centralWidget)
        self.textInput.addWidget(self.inputField)

        self.mainSection.addLayout(self.textInput)

        self.frame.addLayout(self.mainSection)

        self.sidebar = QVBoxLayout()
        self.sidebar.setSpacing(5)

        self.usersSelector = QVBoxLayout()

        self.usersLabel = QLabel(self.centralWidget, text="Users (0)")
        self.usersSelector.addWidget(self.usersLabel)

        self.userList = QListWidget(self.centralWidget)
        self.userList.setResizeMode(QListView.ResizeMode.Adjust)
        self.userList.setItemAlignment(Qt.AlignmentFlag.AlignLeading)
        self.usersSelector.addWidget(self.userList)

        self.sidebar.addLayout(self.usersSelector)

        self.serversSelector = QVBoxLayout()

        self.serversLabel = QLabel(self.centralWidget, text="Users (0)")
        self.serversSelector.addWidget(self.serversLabel)

        self.serverList = QListWidget(self.centralWidget)
        self.serverList.setResizeMode(QListView.ResizeMode.Adjust)
        self.serverList.setItemAlignment(Qt.AlignmentFlag.AlignLeading)
        self.serversSelector.addWidget(self.serverList)

        self.sidebar.addLayout(self.serversSelector)
        
        self.channelsSelector = QVBoxLayout()

        self.channelsLabel = QLabel(self.centralWidget, text="Users (0)")
        self.channelsSelector.addWidget(self.channelsLabel)

        self.channelList = QListWidget(self.centralWidget)
        self.channelList.setResizeMode(QListView.ResizeMode.Adjust)
        self.channelList.setItemAlignment(Qt.AlignmentFlag.AlignLeading)
        self.channelsSelector.addWidget(self.channelList)

        self.sidebar.addLayout(self.channelsSelector)

        self.sidebar.setStretch(0, 2)
        self.sidebar.setStretch(1, 1)
        self.sidebar.setStretch(2, 2)

        self.frame.addLayout(self.sidebar)

        self.frame.setStretch(0, 5)
        self.frame.setStretch(1, 1)

        # After all is said and done, make this the main widget
        self.master.setCentralWidget(self.centralWidget)

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
        # self.master.protocol("WM_DELETE_WINDOW", self.minimize_to_tray) TODO

    def init_input_menu(self):
        pass #TODO

    def init_message_menu(self):
        pass #TODO

    def init_server_menu(self):
        pass #TODO

    def apply_settings(self):
        self.hidden_windows()
        self.highlight_nickname()
        self.highlight_away_users()
        self.emoji_select()
        pass #TODO

    def hidden_windows(self):
        pass #TODO

    def highlight_nickname(self):
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
            self.bind_return_key()
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
                channel = self.channelList.itemFromIndex(index)

                # Check if the stripped channel is in the away_users list
                if channel in self.irc_client.cap_who_for_chan:
                    # Make sure the index exists in the channelList
                    if 0 <= index < self.channelList.count():
                        # Change the foreground color 
                        self.channelList.itemconfig(index, {'fg': self.channelList_fg})
                else:
                    # Make sure the index exists in the channelList
                    if 0 <= index < self.channelList.size():
                        # Reset the foreground color 
                        self.channelList.itemconfig(index, {'fg': self.need_who_chan_fg})
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
        self.current_nick_channel = f"{mode_symbol}{nickname} | {channel}" + " ▷"