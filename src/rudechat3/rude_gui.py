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

        self.start_irc_client()

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

        self.userChanDisplay = QLabel(self.centralWidget, text="User@channel: ")
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

    def start_irc_client(self):
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