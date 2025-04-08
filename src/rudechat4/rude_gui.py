from rudechat4.shared_imports import *
from rudechat4.global_variables import *
from rudechat4.rude_client import RudeChatClient
from rudechat4.server_config_window import ServerConfigWindow
from rudechat4.gui_config_window import GuiConfigWindow
from rudechat4.list_window import ChannelListWindow
from rudechat4.nick_cleaner import clean_nicknames
#from rudechat4.format_decoder import decoder
from rudechat4.rude_logger import configure_logging

class RudeTextEdit(QTextEdit):
    def get_anchor_at(self, pos):
        cursor = self.cursorForPosition(pos)
        char_format = cursor.charFormat()
        if char_format.isAnchor():
            return char_format.anchorHref()

    def is_anchor_at(self, pos):
        cursor = self.cursorForPosition(pos)
        return cursor.charFormat().isAnchor()

    def reset_cursor_position(self):
        """Reset the cursor to the bottom-right position."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        self.setTextCursor(cursor)

    def copy(self):
        super().copy()
        self.reset_cursor_position()

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        copy_action = menu.actions()[0]
        copy_action.triggered.connect(self.reset_cursor_position)
        menu.exec(event.globalPos())

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            super().mouseReleaseEvent(event)

    def mousePressEvent(self, e):
        if self.is_anchor_at(e.pos()):
            url = self.get_anchor_at(e.pos())
            webbrowser.open(url)
        elif e.button() == Qt.MouseButton.LeftButton:
            super().mousePressEvent(e)

class TabEventFilter(QObject):
    def __init__(self, gui):
        super().__init__()
        self.gui = gui

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Tab:
            self.handle_tab_complete()
            return True  # Block TAB behavior
        return super().eventFilter(obj, event)

    def handle_tab_complete(self):
        try:
            current_text = self.gui.text_field.text().strip()

            if not current_text:
                return

            # Get list of usernames from QListWidget
            user_list = [self.gui.user_selector_list.item(i).text() for i in range(self.gui.user_selector_list.count())]

            # Find the closest match
            matched_name = self.find_closest_match(current_text, user_list)

            # Replace text field with matched nickname
            if matched_name:
                self.gui.text_field.setText(matched_name + f"{self.gui.tab_complete_terminator} ")
        except Exception as e:
            logging.error(f"Error in TabEventFilter.handle_tab_complete: {e}")
            return

    def find_closest_match(self, input_text, user_list):
        """Returns the closest match to input_text from user_list (case insensitive), after stripping mode prefixes."""
        
        input_text = input_text.lower()
        
        # Strip any mode characters
        modes_to_strip = ''.join(self.gui.irc_client.mode_values)
        
        # Remove any leading modes from each username in the list
        def strip_modes(username):
            for mode in modes_to_strip:
                if username.startswith(mode):
                    username = username[1:]
            return username
        
        # Get matches after stripping modes
        matches = [
            user for user in user_list 
            if strip_modes(user).lower().startswith(input_text)
        ]
        
        # Strip modes from the match
        matched_nick = matches[0] if matches else None
        if matched_nick is None:
            return
        plain_nickname = matched_nick.lstrip(modes_to_strip)

        return plain_nickname

class ArrowKeyEventFilter(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def eventFilter(self, obj, event):
        if obj == self.parent.text_field and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Up:
                self.parent.show_previous_entry()
                return True
            elif event.key() == Qt.Key.Key_Down:
                self.parent.show_next_entry()
                return True
        return super().eventFilter(obj, event)

class RudeChannelListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.gui = parent

    def show_context_menu(self, pos: QPoint):
        """Displays channel list context menu"""
        menu = QMenu(self)
        selected_item = self.currentItem()
        
        if not selected_item:
            return

        for i in self.gui.irc_client.chantypes:
            if not selected_item.text().startswith(i):
                remove_action = QAction("Close DM", self)
                remove_action.triggered.connect(lambda _, item=selected_item.text(): self.exit_dm(item))
            else:
                remove_action = QAction("Leave Channel", self)
                remove_action.triggered.connect(lambda _, item=selected_item.text(): self.exit_channel(item))

        # Add actions to menu
        menu.addAction(remove_action)

        # Show menu at cursor position
        menu.exec(self.mapToGlobal(pos))

    def exit_channel(self, item):
        """Leaves a channel"""
        if not item:
            return
        channel_name = item
        reason = f"Bye!"
        self.gui.irc_client.loop.create_task(self.gui.irc_client.leave_channel(channel_name, reason))    

    def exit_dm(self, item):
        """Closes a DM from a user"""
        if not item:
            return
        self.gui.irc_client.close_dm(item)

class RudeUserListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.gui = parent

    def show_context_menu(self, pos: QPoint):
        """Displays user list context menu"""
        menu = QMenu(self)

        # Init the actions
        open_user_dm = QAction("Open DM", self)
        whois_user = QAction("whois", self)
        ignore_action = QAction("Ignore User", self)
        unignore_action = QAction("Unignore User", self)
        kick_action = QAction("Kick User", self)

        # Connect actions to methods
        open_user_dm.triggered.connect(self.open_dm_with_user)
        whois_user.triggered.connect(self.whois_the_user)
        ignore_action.triggered.connect(self.ignore_user)
        unignore_action.triggered.connect(self.unignore_user)
        kick_action.triggered.connect(self.kick_user_from_channel)

        # Add meu actions
        menu.addAction(open_user_dm)
        menu.addAction(whois_user)
        menu.addAction(ignore_action)
        menu.addAction(unignore_action)
        menu.addAction(kick_action)

        # Show menu at cursor position
        menu.exec(self.mapToGlobal(pos))

    def open_dm_with_user(self):
        """Removes the selected channel from the list."""
        selected_item = self.currentItem()
        if selected_item:
            self.gui.irc_client.loop.create_task(self.gui.irc_client.command_parser(f"/query {selected_item.text()}"))

    def whois_the_user(self):
        """Runs a whois command on the selected user."""
        selected_item = self.currentItem()
        if selected_item:
            modes_to_strip = ''.join(self.gui.irc_client.mode_values)
            user = selected_item.text().lstrip(modes_to_strip)
            self.gui.irc_client.whois_user_request = True
            self.gui.irc_client.loop.create_task(self.gui.irc_client.whois(user))

    def ignore_user(self):
        selected_item = self.currentItem()
        if selected_item:
            modes_to_strip = ''.join(self.gui.irc_client.mode_values)
            cleaned_nickname = selected_item.text().lstrip(modes_to_strip)
            self.gui.irc_client.loop.create_task(self.gui.irc_client.ignore_user_from_gui(cleaned_nickname))

    def unignore_user(self):
        selected_item = self.currentItem()
        if selected_item:
            modes_to_strip = ''.join(self.gui.irc_client.mode_values)
            cleaned_nickname = selected_item.text().lstrip(modes_to_strip)
            self.gui.irc_client.loop.create_task(self.gui.irc_client.unignore_user_from_gui(cleaned_nickname))

    def kick_user_from_channel(self):
        selected_item = self.currentItem()
        if selected_item:
            modes_to_strip = ''.join(self.gui.irc_client.mode_values)
            channel = self.gui.irc_client.current_channel
            selected_user = selected_item.text().lstrip(modes_to_strip)
            self.gui.irc_client.loop.create_task(self.gui.irc_client.handle_kick_command(["/kick", selected_user, channel, "Bye <3"]))

class RudeGui(QWidget):
    # Initialisation and Setup
    def __init__(self, master):
        super().__init__()
        self.master = master
        self.app_size = [800, 600]
        self.set_screen_size()
        self.master.resize(self.app_size[0], self.app_size[1])

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
            "☹": 0,
            "☹️": 0,
            "🥪": 1,
            "✨": 0,
            "✅": 0,
            "😈": 1,
            "❤️": 0,
            "🎶": 1,
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
        configure_logging()

    def set_icon(self): # Need to debug this, it wont show the icon on Linux. 
        match platform.system():
            case "Darwin":
                icon = QIcon()
                icon_file = os.path.join(G_SOURCE_DIR, 'rude.png')
                icon.addFile(icon_file)
                self.master.setWindowIcon(icon)
            case "Linux":
                icon = QIcon()
                icon_file = os.path.join(G_SOURCE_DIR, 'rude.png') # Icon file too big?
                icon.addFile(icon_file)
                self.master.setWindowIcon(icon)
            case "Windows":
                icon = QIcon()
                icon_file = os.path.join(G_SOURCE_DIR, 'rude.ico')
                icon.addFile(icon_file)
                self.master.setWindowIcon(icon)
            case _:
                logging.error(f"Unknown Operating System in set_icon: {platform.system()}")

    def set_screen_size(self):
        try:
            screen = QGuiApplication.primaryScreen()
            if not screen:
                raise ValueError("No available screen detected.")  # Handle None case

            width = screen.size().width()
            height = screen.size().height()
            width = width // 2
            height = height // 2
            self.app_size = [width, height]
        except Exception as e:
            logging.error(f"Unable to get screen size: {e}. Using default variables.")
            screen_size = "default"  # Prevent NameError in match-case

    def read_config(self):
        config_file = os.path.join(G_CONFIG_DIR, 'gui_config.ini')

        if os.path.exists(config_file):
            config = configparser.ConfigParser()
            config.read(config_file)

            self.window_bg = config.get('Chat', 'window_bg', fallback='#1b1e20')
            self.window_fg = config.get('Chat', 'window_fg', fallback='#C0FFEE')
            self.window_font_family = config.get('Chat', 'window_font_family', fallback='Courier')
            self.window_font_size = config.get('Chat', 'window_font_size', fallback=12)
            self.chat_bg = config.get('Chat', 'chat_bg', fallback='#1b1e20')
            self.chat_fg = config.get('Chat', 'chat_fg', fallback='#C0FFEE')
            self.chat_font_family = config.get('Chat', 'chat_font_family', fallback='Courier')
            self.chat_font_size = config.get('Chat', 'chat_font_size', fallback=12)
            self.entry_bg = config.get('Entry', 'entry_bg', fallback='#1b1e20')
            self.entry_fg = config.get('Entry', 'entry_fg', fallback='#C0FFEE')
            self.entry_selected_bg = config.get('Entry', 'entry_selected_bg', fallback='#C0FFEE')
            self.entry_font_family = config.get('Entry', 'entry_font_family', fallback='Courier')
            self.entry_font_size = config.get('Entry', 'entry_font_size', fallback=12)
            self.list_bg = config.get('Lists', 'list_bg', fallback='#1b1e20')
            self.list_server_fg = config.get('Lists', 'list_server_fg', fallback='#C0FFEE')
            self.list_channel_fg = config.get('Lists', 'list_channel_fg', fallback='#C0FFEE')
            self.list_font_family = config.get('Lists', 'list_font_family', fallback='Courier')
            self.list_font_size = config.get('Lists', 'list_font_size', fallback=12)
            self.list_channel_current_bg = config.get('Lists', 'list_channel_current_bg', fallback='blue')
            self.list_channel_select_bg = config.get('Lists', 'list_channel_select_bg', fallback='blue')
            self.list_channel_needwho_fg = config.get('Lists', 'list_channel_needwho_fg', fallback='#a4a4a4')
            self.list_user_fg = config.get('Lists', 'list_user_fg', fallback='#C0FFEE')
            self.list_user_away_fg = config.get('Lists', 'list_user_away_fg', fallback='#4c6c3b')
            self.main_nickname_color = config.get('Utility', 'main_nickname_color', fallback='#39ff14')
            self.generate_nickname_colors = config.getboolean('Utility', 'generate_nickname_colors', fallback=True)
            self.minimize_to_tray = config.getboolean('Utility', 'minimize_to_tray', fallback=True)
            self.log_on = config.getboolean('Utility', 'turn_logging_on', fallback=False)
            self.show_server_window = config.getboolean('Utility', 'show_server_window', fallback=True)
            self.tab_complete_terminator = config.get('Utility', 'tab_complete_terminator', fallback=':')
            self.scrollbar_bg = config.get('Utility', 'scrollbar_bg', fallback='#2a2e32')

        else:
            self.window_bg = '#1b1e20'
            self.window_fg = '#C0FFEE'
            self.window_font_family = 'Courier'
            self.window_font_size = 12
            self.chat_bg = '#1b1e20'
            self.chat_fg = '#C0FFEE'
            self.chat_font_family = 'Courier'
            self.chat_font_size = 12
            self.entry_bg = '#1b1e20'
            self.entry_fg = '#C0FFEE'
            self.entry_selected_bg = '#C0FFEE'
            self.entry_font_family = 'Courier'
            self.entry_font_size = 12
            self.list_bg = '#1b1e20'
            self.list_user_fg = '#C0FFEE'
            self.list_server_fg = '#C0FFEE'
            self.list_channel_fg = '#C0FFEE'
            self.list_font_family = 'Courier'
            self.list_font_size = 12
            self.list_channel_current_bg = 'blue'
            self.list_channel_select_bg = 'blue'
            self.list_channel_needwho_fg = '#a4a4a4'
            self.list_user_away_fg = '#4c6c3b'
            self.main_nickname_color = '#39ff14'
            self.generate_nickname_colors = True
            self.minimize_to_tray = True
            self.log_on = False
            self.show_server_window = True
            self.tab_complete_terminator = ':'

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

        self.text_field = QLineEdit(self)
        self.text_field.setFrame(False)
        self.arrow_key_filter = ArrowKeyEventFilter(self)
        self.text_field.installEventFilter(self.arrow_key_filter)
        self.tab_filter = TabEventFilter(self)
        self.text_field.installEventFilter(self.tab_filter)
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

        self.user_selector_list = RudeUserListWidget(self)
        self.user_selector_list.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.user_selector_list.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.user_selector_list.setItemAlignment(Qt.AlignmentFlag.AlignLeading)
        self.user_selector_list.setAutoFillBackground(True)
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
        self.server_selector_list.setAutoFillBackground(True)
        self.server_selector.addWidget(self.server_selector_list)

        self.sidebar.addLayout(self.server_selector)

        self.channel_selector = QVBoxLayout()

        self.channel_selector_label = QLabel(self, text="Channels (0)")
        self.channel_selector_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.channel_selector.addWidget(self.channel_selector_label)

        self.channel_selector_list = RudeChannelListWidget(self)
        self.channel_selector_list.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.channel_selector_list.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.channel_selector_list.itemClicked.connect(self.on_channel_click)
        self.channel_selector_list.setItemAlignment(Qt.AlignmentFlag.AlignLeading)
        self.channel_selector_list.setAutoFillBackground(True)
        self.channel_selector.addWidget(self.channel_selector_list)

        self.sidebar.addLayout(self.channel_selector)

        self.sidebar.setStretch(0, 2)
        self.sidebar.setStretch(1, 1)
        self.sidebar.setStretch(2, 2)

        self.layout().addLayout(self.sidebar)

    def select_first_server(self):
        server_count = self.server_selector_list.count()
        index_server = 0

        if server_count > 0:
            self.server_selector_list.clearSelection()
            self.server_selector_list.setCurrentRow(index_server)
            self.server_selector_list.scrollToItem(self.server_selector_list.item(index_server))

            self.on_server_change(None)
            return

    def set_gui_theme(self):  # Apply GUI theme settings
        # Set Chat Font
        chat_font = QFont(self.chat_font_family, int(self.chat_font_size))
        self.chat_box.setFont(chat_font)

        # Apply Topic Label Theme
        self.topic_label.setStyleSheet(f"""
            color: {self.window_fg};
            background-color: {self.window_bg};
            font-family: {self.window_font_family};
            font-size: {self.window_font_size}px;
        """)

        self.master.setStyleSheet(f"""
            color: {self.window_fg};
            background-color: {self.window_bg};
        """)

        # Apply Chat Box Theme
        self.chat_box.setStyleSheet(f"""
            color: {self.chat_fg};
            background-color: {self.chat_bg};
            font-family: {self.chat_font_family};
            font-size: {self.chat_font_size}px;
        """)

        # Apply Input Field Theme
        self.text_field.setStyleSheet(f"""
            color: {self.entry_fg};
            background-color: {self.entry_bg};
            selection-background-color: {self.entry_selected_bg};
            font-family: {self.entry_font_family};
            font-size: {self.entry_font_size}px;
        """)

        # Apply User List Theme
        self.user_selector_list.setStyleSheet(f"""
            color: {self.list_user_fg};
            background-color: {self.list_bg};
            font-family: {self.list_font_family};
            font-size: {self.list_font_size}px;
        """)

        # Apply Server List Theme
        self.server_selector_list.setStyleSheet(f"""
            color: {self.list_server_fg};
            background-color: {self.list_bg};
            font-family: {self.list_font_family};
            font-size: {self.list_font_size}px;
        """)

        # Apply Channel List Theme
        self.channel_selector_list.setStyleSheet(f"""
            color: {self.list_channel_fg};
            background-color: {self.list_bg};
            font-family: {self.list_font_family};
            font-size: {self.list_font_size}px;
        """)

        # Apply Scrollbar Theme
        self.setStyleSheet(f"""
            QScrollBar:vertical {{
                border: none;
                background: {self.scrollbar_bg };
                width: 12px;
                margin: 0px 0px 0px 0px;
            }}

            QScrollBar::handle:vertical {{
                background: {self.scrollbar_bg };
                min-height: 20px;
                border-radius: 5px;
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                background: none;
                border: none;
            }}

        """)

        # Apply Labels (User, Server, and Channel Sections)
        self.user_selector_label.setStyleSheet(f"color: {self.window_fg}; background-color: {self.window_bg};")
        self.server_selector_label.setStyleSheet(f"color: {self.window_fg}; background-color: {self.window_bg};")
        self.channel_selector_label.setStyleSheet(f"color: {self.window_fg}; background-color: {self.window_bg};")

        # Apply Message ID Label Theme
        self.id_label.setStyleSheet(f"color: {self.window_fg}; background-color: {self.window_bg};")

        # Apply Topic Label Theme
        self.topic_label.setStyleSheet(f"color: {self.window_fg}; background-color: {self.window_bg};")

        # Apply Selection Colors
        self.server_selector_list.setStyleSheet(self.server_selector_list.styleSheet() + f"selection-background-color: {self.list_channel_current_bg};")
        self.channel_selector_list.setStyleSheet(self.channel_selector_list.styleSheet() + f"selection-background-color: {self.list_channel_current_bg};")
        self.highlight_who_channels()

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
        self.download_channel_list = {} 
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
        self.apply_settings()
        self.show_startup_art()

    def init_input_menu(self): pass #TODO

    def apply_settings(self):
        self.highlight_nicknames()
        self.highlight_away_users()
        self.emoji_select()
        self.set_gui_theme()
        self.set_icon()

    def emoji_select(self):
        match platform.system():
            case "Darwin": self.emoji_type = "Apple Color Emoji" #macOS
            case "Linux": self.emoji_type = "Noto Color Emoji"
            case "Windows": self.emoji_type = "Segoe UI Emoji"
            case _: self.emoji_type = "Arial" # A generic font as a last resort

    def bind_return_key(self):
        loop = asyncio.get_event_loop()
        self.text_field.returnPressed.connect(lambda: loop.create_task(self.on_enter_key(), name="on_enter_key"))

    def get_channel_selector_items(self) -> list[str]:
        return [self.channel_selector_list.item(i).text() for i in range(self.channel_selector_list.count())]

    def show_previous_entry(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.text_field.setText(self.entry_history[self.history_index])

    def show_next_entry(self):
        if self.history_index < len(self.entry_history) - 1:
            self.history_index += 1
            self.text_field.setText(self.entry_history[self.history_index])
        elif self.history_index == len(self.entry_history) - 1:
            self.history_index += 1
            self.text_field.clear()

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
            logging.info("Finished Creating Client Tasks.")
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
        try:
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
        except AttributeError as e:
            logging.error(f"AttributeError in update_users_label: {e}")
            return
        except Exception as e:
            logging.error(f"Exception in update_users_label: {e}")
            return

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

    def reset_nick_colors(self):
        self.nickname_colors = self.load_nickname_colors()
        self.highlight_nicknames()

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

        self.main_window.layout.addWidget(config_window)

        save_button = QPushButton("Apply")
        save_button.clicked.connect(config_window.save_config)
        self.main_window.layout.addWidget(save_button)

        self.main_window.show()

    def open_gui_config_window(self):
        def after_config_window_close():
            self.read_config()
            self.apply_settings()

        def close_window():
            self.main_window.close()

        def on_config_window_close():
            QTimer.singleShot(100, after_config_window_close)
            QTimer.singleShot(200, close_window)
            return

        self.main_window = QWidget()
        self.main_window.setWindowTitle("Rude GUI configuration")
        self.main_window.resize(450, 500)

        config_file = os.path.join(G_CONFIG_DIR, 'gui_config.ini')

        self.main_window.layout = QVBoxLayout(self.main_window)
        self.main_window.setContentsMargins(0, 0, 0, 0)

        config_window = GuiConfigWindow(self.main_window, config_file, on_config_window_close)

        self.main_window.layout.addWidget(config_window)

        save_button = QPushButton("Apply")
        save_button.clicked.connect(config_window.save_config)
        self.main_window.layout.addWidget(save_button)

        self.main_window.show()

    def show_channel_list_window(self):
        self.channel_window = ChannelListWindow(self, self.master)
        self.channel_window.show()

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
                self.server_selector_list.item(self.previous_server_index).setBackground(QColor(self.list_bg))
                self.server_selector_list.item(self.previous_server_index).setForeground(QColor(self.list_server_fg))

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
                selected_server.setBackground(QColor(self.list_channel_current_bg))
                selected_server.setForeground(QColor(self.list_server_fg))

                # Store the foreground and background colors for the selected server
                self.server_colors[selected_server_index] = {'fg': self.list_server_fg, 'bg': self.list_channel_current_bg}
                
                if self.previous_server_index is not None:
                    if self.previous_server_index != selected_server_index:
                        # Check if the previous server color is not a mention or activity highlight before updating
                        prev_bg = self.server_colors[self.previous_server_index].get('bg', '')
                        if prev_bg not in [self.irc_client.activity_note_color, self.irc_client.mention_note_color]:
                            self.server_colors[self.previous_server_index] = {'bg': self.list_bg, 'fg': self.list_server_fg}

            for server_index, colors in self.server_colors.items():
                # Get the stored foreground and background colors
                fg_color = colors.get('fg', self.list_server_fg)
                bg_color = colors.get('bg', self.list_bg)

                # Apply the stored colors to each server in the listbox
                self.server_selector_list.item(server_index).setForeground(QColor(fg_color))
                self.server_selector_list.item(server_index).setBackground(QColor(bg_color))

            # Update the previous_server_index to the currently selected server index
            self.previous_server_index = selected_server_index
            return

    def on_channel_click(self):
        # Set background of currently selected channel back to default
        try:
            current_selected_channel = self.irc_client.current_channel
            if current_selected_channel:
                for i in range(self.channel_selector_list.count()):
                    if self.channel_selector_list.item(i).text() == current_selected_channel:
                        self.channel_selector_list.item(i).setBackground(QColor(self.list_bg))
                        break

            # Get index of clicked item
            clicked_index = self.channel_selector_list.currentRow()
            clicked_channel = self.channel_selector_list.item(clicked_index)
            self.switch_channel(clicked_channel.text())

            # Turn background blue
            self.channel_selector_list.item(clicked_index).setBackground(QColor(self.list_channel_current_bg))
            self.highlight_nicknames()
            self.highlight_away_users()
            self.update_users_label()

            # Remove the clicked channel from highlighted_channels dictionary
            if self.irc_client.server_name in self.irc_client.highlighted_channels:
                server_highlighted_channels = self.irc_client.highlighted_channels[self.irc_client.server_name]
                if clicked_channel.text() in server_highlighted_channels:
                    del server_highlighted_channels[clicked_channel.text()]
        except AttributeError as e:
            logging.error(f"AttributeError in on_channel_click: {e}")
            return
        except Exception as e:
            logging.error(f"Exception in on_channel_click: {e}")

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
            logging.error(f"Error in on_enter_key: {e}")

    # Text & Formatting
    def insert_text_widget(self, message):
        self.chat_box.reset_cursor_position()
        urls = self.find_urls(message)
        formatted_text = self.decoder(message)

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
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            for _ in range(excess_lines):
                cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()

    def find_urls(self, text):
        # Use the precompiled regex pattern to find URLs
        return self.url_pattern.findall(text)

    def decoder(self, input_text: str) -> List[Tuple[str, QTextCharFormat]]:
        output = []
        text_buffer = []

        # Mutable state
        current_attr = {
            "bold": False,
            "italic": False,
            "underline": False,
            "strikethrough": False,
            "inverse": False,
            "colour": 0,
            "background": 1
        }

        def flush():
            if text_buffer:
                try:
                    fmt = self.configure_tag_based_on_attributes(current_attr)
                    output.append(("".join(text_buffer), fmt))
                except Exception as e:
                    logging.error(f"Error creating format during flush: {e}")
                text_buffer.clear()

        c_index = 0
        while c_index < len(input_text):
            c = input_text[c_index]
            match c:
                case '\x02':  # Bold
                    flush()
                    current_attr["bold"] = not current_attr["bold"]
                case '\x1D':  # Italic
                    flush()
                    current_attr["italic"] = not current_attr["italic"]
                case '\x1F':  # Underline
                    flush()
                    current_attr["underline"] = not current_attr["underline"]
                case '\x1E':  # Strikethrough
                    flush()
                    current_attr["strikethrough"] = not current_attr["strikethrough"]
                case '\x16':  # Inverse
                    flush()
                    fg, bg = current_attr["colour"], current_attr["background"]
                    current_attr["colour"], current_attr["background"] = bg, fg
                case '\x03':  # Color code
                    flush()
                    current_attr = {
                        "bold": False,
                        "italic": False,
                        "underline": False,
                        "strikethrough": False,
                        "inverse": False,
                        "colour": 0,
                        "background": 1
                    }
                    color_match = re.match(r'\x03(\d{1,2})(?:,(\d{1,2}))?', input_text[c_index:])
                    if color_match:
                        fg = int(color_match.group(1))
                        bg = int(color_match.group(2)) if color_match.group(2) else 1
                        current_attr["colour"] = fg
                        current_attr["background"] = bg
                        c_index += color_match.end() - 1
                case '\x0F':  # Reset
                    flush()
                    current_attr = {
                        "bold": False,
                        "italic": False,
                        "underline": False,
                        "strikethrough": False,
                        "inverse": False,
                        "colour": 0,
                        "background": 1
                    }
                case _:
                    text_buffer.append(c)

            c_index += 1

        flush()
        return output

    def tag_text(self, formatted_text):
        cursor = self.chat_box.textCursor()
        for text, char_format in formatted_text:
            try:
                cursor.insertText(text, char_format)
            except Exception as e:
                logging.error(f"Error in tag_text: {e}")

    def configure_tag_based_on_attributes(self, attr: dict) -> QTextCharFormat:
        try:
            fmt = QTextCharFormat()
            fmt.setFontFamily(self.chat_font_family)
            fmt.setFontPointSize(int(self.chat_font_size))
            
            if attr["bold"]:
                fmt.setFontWeight(2)
            if attr["italic"]:
                fmt.setFontItalic(True)
            if attr["underline"]:
                fmt.setFontUnderline(True)
            if attr["strikethrough"]:
                fmt.setFontStrikeOut(True)
            
            if attr["colour"] != 0:
                irc_color_code = f"{attr['colour']:02d}"
                hex_color = self.irc_colors.get(irc_color_code, 'white')
                fmt.setForeground(QColor(hex_color))
            
            if attr["background"] != 1:
                irc_background_code = f"{attr['background']:02d}"
                hex_background = self.irc_colors.get(irc_background_code, 'black')
                fmt.setBackground(QColor(hex_background))
            
            return fmt

        except Exception as e:
            logging.error(f"Error in configure_tag_based_on_attributes: {e}")
            return QTextCharFormat()

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
        """Efficiently highlight nicknames in the chat box with emoji-aware offset correction."""
        try:
            text = self.chat_box.toPlainText()
            if not text:
                return

            # Precompute emoji offsets once for the entire text
            emoji_offset_start, emoji_offset_end = {}, {}
            font = self.chat_box.font()
            emoji_widths = self.estimate_emoji_offset(text, font)

            # Precompute cumulative emoji offsets for faster lookup
            emoji_offset_start, emoji_offset_end = self.build_emoji_offset_map(text, emoji_widths)
            nicknames_to_highlight = set()
            nicknames_to_highlight.add(self.irc_client.nickname)

            # Include matches from general nickname pattern
            if hasattr(self, 'nickname_pattern'):
                for match in self.nickname_pattern.finditer(text):
                    nick = match.group(0)
                    nicknames_to_highlight.add(nick.strip('<>').lstrip(''.join(self.irc_client.mode_values)))

            # Highlight nicknames
            for nickname in nicknames_to_highlight:
                pattern = self.users_nickname_pattern(nickname)
                for match in pattern.finditer(text):
                    matched_text = match.group(0)
                    start, end = match.span()
                    adjusted_start = start + emoji_offset_start.get(start, 0)
                    adjusted_end = end + emoji_offset_end.get(end, 0)
                    self.apply_nickname_format(matched_text, adjusted_start, adjusted_end, matched_text)

        except Exception as e:
            logging.error(f"Error in optimized highlight_nicknames: {e}")

    def build_emoji_offset_map(self, text, emoji_widths):
        """Precompute emoji offset adjustments at each index."""
        offset_start_map = {}
        offset_end_map = {}
        cum_offset = 0

        for i, char in enumerate(text):
            offset = emoji_widths.get(char, 0)
            if offset:
                cum_offset += offset
            offset_start_map[i + 1] = cum_offset
            offset_end_map[i + 1] = cum_offset

        return offset_start_map, offset_end_map

    def apply_nickname_format(self, text, start_position, end_position, nickname):
        """Apply color formatting to the nickname with emoji offset correction."""
        try:
            if not nickname:
                return

            # Determine the nickname color
            if nickname in self.nickname_colors:
                nickname_color = self.nickname_colors[nickname]
            else:
                if self.generate_nickname_colors:
                    if nickname == self.irc_client.nickname:
                        nickname_color = self.main_nickname_color
                    else:
                        nickname_color = self.generate_random_color()
                else:
                    nickname_color = self.main_fg_color

                self.nickname_colors[nickname] = nickname_color

            # Setup text format
            format_nick = QTextCharFormat()
            format_nick.setFontFamily(self.chat_font_family)
            format_nick.setFontPointSize(int(self.chat_font_size))
            format_nick.setForeground(QColor(nickname_color))

            # Apply formatting
            cursor = self.chat_box.textCursor()
            cursor.setPosition(start_position)
            cursor.setPosition(end_position, QTextCursor.MoveMode.KeepAnchor)
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
                    user_item.setForeground(QColor(self.list_user_away_fg))
                else:
                    # Reset the foreground color 
                    user_item.setForeground(QColor(self.list_user_fg))
            
            # Update the UI to reflect changes
            self.user_selector_list.update()
            
        except Exception as e:
            logging.error(f"Exception in highlight_away_users: {e}")

    def highlight_who_channels(self):
        try:
            if not hasattr(self, 'irc_client'):
                return
            if not hasattr(self.irc_client, 'activity_note_color') or not hasattr(self.irc_client, 'mention_note_color'):
                return
            # Loop through the items in the channel list
            for index in range(self.channel_selector_list.count()):
                # Get the channel item from the list
                channel_item = self.channel_selector_list.item(index)
                if not channel_item:
                    continue  # Skip if the item is not found

                # Get the channel name (assuming item text is the channel name)
                channel = channel_item.text()

                current_bg_color = channel_item.background().color().name()
                preserve_colors = [self.irc_client.activity_note_color, self.irc_client.mention_note_color]

                # Check if the channel is in the cap_who_for_chan list
                if channel in self.irc_client.cap_who_for_chan:
                    # Set foreground and background colors
                    channel_item.setForeground(QColor(self.list_channel_fg))
                    if current_bg_color not in preserve_colors:
                        channel_item.setBackground(QColor(self.list_bg))
                else:
                    # Highlight channels needing WHO request
                    channel_item.setForeground(QColor(self.list_channel_needwho_fg))
                    if current_bg_color not in preserve_colors:
                        channel_item.setBackground(QColor(self.list_bg))

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

    def the_force_click(self, index):
        # Set background of currently selected channel back to default
        current_selected_channel = self.irc_client.current_channel
        if self.log_on:
            logging.debug(f"the_force_click current_channel {current_selected_channel}")
        if current_selected_channel:
            for i in range(self.channel_selector_list.count()):
                item = self.channel_selector_list.item(i)  # Get the QListWidgetItem
                if item.text() == current_selected_channel:
                    # Reset background color to default
                    item.setBackground(QColor(self.list_bg))
                    break

        # Get index of clicked item
        clicked_index = index
        if self.log_on:
            logging.debug(f"Simulated Clicked Index: {clicked_index}")
        if clicked_index is not None and clicked_index >= 0:
            clicked_item = self.channel_selector_list.item(clicked_index)
            clicked_channel = clicked_item.text()
            if self.log_on:
                logging.debug(f"Clicked Channel: {clicked_channel}")
            
            self.switch_channel(clicked_channel)
            if self.log_on:
                logging.debug(f"Switching channels...")

            # Change background color of the clicked channel to blue
            if self.log_on:
                logging.debug(f"Recolor background hit")
            clicked_item.setBackground(QColor(self.list_channel_select_bg))
            self.highlight_away_users()
            self.update_users_label()
            if self.log_on:
                logging.debug(f"Finished with GUI update.")

            # Remove the clicked channel from highlighted_channels dictionary
            if self.irc_client.server_name in self.irc_client.highlighted_channels:
                server_highlighted_channels = self.irc_client.highlighted_channels[self.irc_client.server_name]
                if clicked_channel in server_highlighted_channels:
                    del server_highlighted_channels[clicked_channel]
