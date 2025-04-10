from rudechat4.shared_imports import *
from PyQt6 import QtCore, QtGui, QtWidgets


class EnterFilter(QObject):
    def __init__(self, gui):
        super().__init__()
        self.gui = gui

    def eventFilter(self, obj, event):
        if hasattr(self.gui, 'input'):
            if obj == self.gui.input and event.type() == QtCore.QEvent.Type.KeyPress:
                if event.key() in [QtCore.Qt.Key.Key_Enter, QtCore.Qt.Key.Key_Return]:
                    self.gui.insert_and_send_message()  # Handle Enter key press
                    return True  
        return super().eventFilter(obj, event)  # Let other events pass normally

class RudePopout(QObject):
    def __init__(self):
        super().__init__()
        self.parentGui = None
        self.channel = None
        self.form = None
        self.emoji_width_cache = {}

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
            "⚠": 0,
        }

    def setupUi(self, Form):
        # === Main Window Setup ===
        if self.parentGui.log_on:
            logging.info("Setting up UI components")

        # === Main Horizontal Layout (Chat + Sidebar) ===
        self.horizontalLayout = QtWidgets.QHBoxLayout(Form)
        self.horizontalLayout.setObjectName("horizontalLayout")

        # ===============================
        #       LEFT: CHAT AREA
        # ===============================
        self.content = QtWidgets.QVBoxLayout()
        self.content.setSpacing(5)
        self.content.setObjectName("content")

        # --- Chat Area (Topic Label + Text Display) ---
        self.chat_area = QtWidgets.QVBoxLayout()
        self.chat_area.setSpacing(5)
        self.chat_area.setObjectName("chat_area")

        # * Topic label (appears above the chat log) *
        self.topic_label = QtWidgets.QLabel(parent=Form)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Preferred
        )
        sizePolicy.setHeightForWidth(self.topic_label.sizePolicy().hasHeightForWidth())
        self.topic_label.setSizePolicy(sizePolicy)
        self.topic_label.setObjectName("topic_label")
        self.chat_area.addWidget(self.topic_label)

        # * Chat display area (read-only text browser) *
        self.display_text = QtWidgets.QTextBrowser(parent=Form)
        self.display_text.setObjectName("display_text")
        self.chat_area.addWidget(self.display_text)

        # Add chat area to the content layout
        self.content.addLayout(self.chat_area)

        # --- Input field for typing messages ---
        self.text_input = QtWidgets.QHBoxLayout()
        self.text_input.setSpacing(5)
        self.text_input.setObjectName("text_input")

        # * Line edit for typing messages *
        self.input = QtWidgets.QLineEdit(parent=Form)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Preferred
        )
        sizePolicy.setHeightForWidth(self.input.sizePolicy().hasHeightForWidth())
        self.input.setSizePolicy(sizePolicy)
        self.input.setObjectName("input_field")
        self.text_input.addWidget(self.input)

        # Add text input field to the content layout
        self.content.addLayout(self.text_input)

        # Add all content (chat + input) to the main horizontal layout
        self.horizontalLayout.addLayout(self.content)

        # ===============================
        #       RIGHT: SIDEBAR
        # ===============================
        self.sidebar = QtWidgets.QVBoxLayout()
        self.sidebar.setSpacing(5)
        self.sidebar.setObjectName("sidebar")

        # --- Sidebar layout for user list + button ---
        self.users_selector = QtWidgets.QVBoxLayout()
        self.users_selector.setSpacing(5)
        self.users_selector.setObjectName("users_selector")

        # * Label above user list *
        self.user_label = QtWidgets.QLabel(parent=Form)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Preferred
        )
        sizePolicy.setHeightForWidth(self.user_label.sizePolicy().hasHeightForWidth())
        self.user_label.setSizePolicy(sizePolicy)
        self.user_label.setObjectName("user_label")
        self.users_selector.addWidget(self.user_label)

        # * List of users (clickable items) *
        self.user_list = QtWidgets.QListWidget(parent=Form)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        sizePolicy.setHeightForWidth(self.user_list.sizePolicy().hasHeightForWidth())
        self.user_list.setSizePolicy(sizePolicy)
        self.user_list.setMouseTracking(True)
        self.user_list.setAutoFillBackground(True)
        self.user_list.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.user_list.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.user_list.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        self.user_list.setItemAlignment(QtCore.Qt.AlignmentFlag.AlignLeading)
        self.user_list.setObjectName("user_list")

        self.users_selector.addWidget(self.user_list)

        # * Button under user list (e.g. to "Pop In" the window) *
        self.pushButton = QtWidgets.QPushButton(parent=Form)
        self.pushButton.setObjectName("pushButton")
        self.users_selector.addWidget(self.pushButton)

        # Add user-related widgets to the sidebar
        self.sidebar.addLayout(self.users_selector)
        self.sidebar.setStretch(0, 2)

        # Add sidebar to main horizontal layout
        self.horizontalLayout.addLayout(self.sidebar)

        # ===============================
        #       SET WINDOW TEXTS
        # ===============================
        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

        self.enter_filter = EnterFilter(self)
        self.input.installEventFilter(self.enter_filter)
        if self.parentGui.log_on:
            logging.info("UI setup complete")

    def retranslateUi(self, Form): 
        _translate = QtCore.QCoreApplication.translate
        self.form = Form
        self.form.closeEvent = self.handle_close_event

        # Topic header
        self.topic_label.setWordWrap(True)
        self.topic_label.setText(_translate("Form", "Topic: "))
        if self.parentGui.log_on:
            logging.debug("Topic label set")

        # Sidebar label
        self.user_label.setText(_translate("Form", "Users (0)"))
        if self.parentGui.log_on:
            logging.debug("User label set")

        # Button text
        self.pushButton.setText(_translate("Form", "Pop In"))
        self.pushButton.clicked.connect(self.pop_in_window)
        self.input.setFocus()
        self.load_channel_messages()
        self.load_user_list()
        self.set_topic()

        if self.parentGui.log_on:
            logging.info(f"channel and parent is set to: {self.channel} & {self.parentGui}")

    def handle_close_event(self, event):
        self.pop_in_window()
        event.accept()

    def pop_in_window(self):
        self.form.close()
        self.parentGui.remove_from_pop_out_dict(self.channel)
        self.parentGui.irc_client.update_gui_channel_list()

    def insert_text(self, message):
        cleaned_message = message.rstrip("\r\n")
        self.display_text.append(f"{cleaned_message}")
        self.highlight_nicknames()

    def load_channel_messages(self):
        try:
            messages = self.parentGui.irc_client.channel_messages[self.parentGui.irc_client.server][self.channel]
            for message in messages:
                cleaned_message = message.rstrip("\r\n")
                self.display_text.append(f"{cleaned_message}")
            self.highlight_nicknames()
        except Exception as e:
            logging.error(f"Unable to load pop out messages: {e}")

    def set_topic(self):
        try:
            topic = self.parentGui.channel_topics[self.parentGui.irc_client.server_name][self.channel]
            self.topic_label.setText(str(topic))
        except Exception as e:
            logging.error(f"Error setting topic: {e}")

    def send_message(self, text):
        try:
            msg = f'PRIVMSG {self.channel} :{text}'
            if self.parentGui.log_on:
                logging.info(f"Sending message: {msg}")
            self.parentGui.irc_client.loop.create_task(self.parentGui.irc_client.send_message(msg))
        except Exception as e:
            logging.error(f"Exception in send_message: {e}")

    def insert_and_send_message(self):
        try:
            nickname = self.parentGui.irc_client.nickname
            user_mode = self.parentGui.irc_client.get_user_mode(nickname, self.channel)
            mode_symbol = self.parentGui.irc_client.get_mode_symbol(user_mode) if user_mode else ''
            if self.parentGui.irc_client.use_time_stamp:
                timestamp = datetime.now().strftime('[%H:%M:%S] ')
            else:
                timestamp = ""
            text = self.input.text().strip()
            if self.parentGui.log_on:
                logging.debug(f"Message to send: {text}")
            self.display_text.append(f"{timestamp}<{mode_symbol}{self.parentGui.irc_client.nickname}> {text}")  # Append keeps previous content and adds a new line
            self.input.clear()
            self.send_message(text)
            self.highlight_nicknames()
            self.parentGui.irc_client.save_message(self.parentGui.irc_client.server, self.channel, nickname, text, mode_symbol, is_sent=False)
            self.parentGui.irc_client.log_message(self.parentGui.irc_client.server_name, self.channel, nickname, text, is_sent=False)
        except Exception as e:
            logging.error(f"Exception in insert_and_send_message: {e}")

    def load_user_list(self):
        for user in self.parentGui.irc_client.channel_users.get(self.channel, []):
            self.user_list.addItem(user)

        num_users = self.user_list.count()
        self.user_label.setText(f"Users ({num_users})")
        self.highlight_away_users()

    def update_user_label(self):
        num_users = self.user_list.count()
        self.user_label.setText(f"Users ({num_users})")

    def update_gui_user_list(self, channel):
        self.user_list.clear()

        for user in self.parentGui.irc_client.channel_users.get(self.channel, []):
            self.user_list.addItem(user)

        self.highlight_away_users()

    def highlight_away_users(self):
        try:
            # Loop through the items in the user_selector_list
            for index in range(self.user_list.count()):
                # Get the user from the listbox
                user_item = self.user_list.item(index)
                if not user_item:
                    continue  # If the item is not found, skip it

                # Get the user name
                user = user_item.text()
                modes_to_strip = ''.join(self.parentGui.irc_client.mode_values)
                strip_user = user.lstrip(modes_to_strip)

                # Check if the user is in the away_users_dict
                if strip_user in self.parentGui.irc_client.away_users_dict:
                    # Change the foreground color 
                    user_item.setForeground(QColor(self.parentGui.list_user_away_fg))
                else:
                    # Reset the foreground color 
                    user_item.setForeground(QColor(self.parentGui.list_user_fg))
            
            # Update the UI to reflect changes
            self.user_list.update()
            
        except Exception as e:
            logging.error(f"Exception in highlight_away_users: {e}")

    def highlight_nicknames(self):
        """Efficiently highlight nicknames in the chat box with emoji-aware offset correction."""
        try:
            text = self.display_text.toPlainText() # self.display_text
            if not text:
                return

            # Precompute emoji offsets once for the entire text
            emoji_offset_start, emoji_offset_end = {}, {}
            font = self.display_text.font()
            emoji_widths = self.estimate_emoji_offset(text, font)

            # Precompute cumulative emoji offsets for faster lookup
            emoji_offset_start, emoji_offset_end = self.build_emoji_offset_map(text, emoji_widths)
            nicknames_to_highlight = set()
            nicknames_to_highlight.add(self.parentGui.irc_client.nickname)

            # Include matches from general nickname pattern
            if hasattr(self.parentGui, 'nickname_pattern'):
                for match in self.parentGui.nickname_pattern.finditer(text):
                    nick = match.group(0)
                    nicknames_to_highlight.add(nick.strip('<>').lstrip(''.join(self.parentGui.irc_client.mode_values)))

            # Highlight nicknames
            for nickname in nicknames_to_highlight:
                pattern = self.parentGui.users_nickname_pattern(nickname)
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
            if nickname in self.parentGui.nickname_colors:
                nickname_color = self.parentGui.nickname_colors[nickname]
            else:
                if self.parentGui.generate_nickname_colors:
                    if nickname == self.parentGui.irc_client.nickname:
                        nickname_color = self.parentGui.main_nickname_color
                    else:
                        nickname_color = self.generate_random_color()
                else:
                    nickname_color = self.parentGui.main_fg_color

                self.parentGui.nickname_colors[nickname] = nickname_color

            # Setup text format
            format_nick = QTextCharFormat()
            format_nick.setFontFamily(self.parentGui.chat_font_family)
            format_nick.setFontPointSize(int(self.parentGui.chat_font_size))
            format_nick.setForeground(QColor(nickname_color))

            # Apply formatting
            cursor = self.display_text.textCursor()
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