from rudechat4.shared_imports import *
from rudechat4.rude_text_browser import RudeTextBrowser


class RudeUserListWidget(QListWidget):
    def __init__(self, parent=None, maingui=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.parentGui = maingui
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
        selected_item = self.currentItem()
        if selected_item:
            self.parentGui.irc_client.loop.create_task(self.parentGui.irc_client.command_parser(f"/query {selected_item.text()}"))

    def whois_the_user(self):
        """Runs a whois command on the selected user."""
        selected_item = self.currentItem()
        if selected_item:
            modes_to_strip = ''.join(self.parentGui.irc_client.mode_values)
            user = selected_item.text().lstrip(modes_to_strip)
            self.parentGui.irc_client.whois_user_request = True
            self.parentGui.irc_client.loop.create_task(self.parentGui.irc_client.whois(user))

    def ignore_user(self):
        selected_item = self.currentItem()
        if selected_item:
            modes_to_strip = ''.join(self.parentGui.irc_client.mode_values)
            cleaned_nickname = selected_item.text().lstrip(modes_to_strip)
            self.parentGui.irc_client.loop.create_task(self.parentGui.irc_client.ignore_user_from_gui(cleaned_nickname))

    def unignore_user(self):
        selected_item = self.currentItem()
        if selected_item:
            modes_to_strip = ''.join(self.parentGui.irc_client.mode_values)
            cleaned_nickname = selected_item.text().lstrip(modes_to_strip)
            self.parentGui.irc_client.loop.create_task(self.parentGui.irc_client.unignore_user_from_gui(cleaned_nickname))

    def kick_user_from_channel(self):
        selected_item = self.currentItem()
        if selected_item:
            modes_to_strip = ''.join(self.parentGui.irc_client.mode_values)
            channel = self.parentGui.irc_client.current_channel
            selected_user = selected_item.text().lstrip(modes_to_strip)
            self.parentGui.irc_client.loop.create_task(self.parentGui.irc_client.handle_kick_command(["/kick", selected_user, channel, "Bye <3"]))

class TabEventFilter(QObject):
    def __init__(self, parent, gui):
        super().__init__()
        self.gui = gui
        self.parent = parent

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Tab:
            self.handle_tab_complete()
            return True  # Block TAB behavior
        return super().eventFilter(obj, event)

    def handle_tab_complete(self):
        try:
            current_text = self.parent.input.text().strip()

            if not current_text:
                return

            # Get list of usernames from QListWidget
            user_list = [self.parent.user_list.item(i).text() for i in range(self.parent.user_list.count())]

            # Find the closest match
            matched_name = self.find_closest_match(current_text, user_list)

            # Replace text field with matched nickname
            if matched_name:
                self.parent.input.setText(matched_name + f"{self.gui.tab_complete_terminator} ")
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
        if hasattr(self.parent, 'input'):
            if obj == self.parent.input and event.type() == QEvent.Type.KeyPress:
                if event.key() == Qt.Key.Key_Up:
                    self.parent.show_previous_entry()
                    return True
                elif event.key() == Qt.Key.Key_Down:
                    self.parent.show_next_entry()
                    return True
        return super().eventFilter(obj, event)

class EnterFilter(QObject):
    def __init__(self, gui):
        super().__init__()
        self.gui = gui

    def eventFilter(self, obj, event):
        if hasattr(self.gui, 'input'):
            if obj == self.gui.input and event.type() == QEvent.Type.KeyPress:
                if event.key() in [Qt.Key.Key_Enter, Qt.Key.Key_Return]:
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
        self.tag_cache = {}
        self.history_index = 0
        self.entry_history = []

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
            "🤖": 1,
            "⚙": 0,
            "🔒": 1,
            "⚰": 0,
        }

        self.url_pattern = re.compile(r'(\w+://[^\s()<>]*\([^\s()<>]*\)[^\s()<>]*(?<![.,;!?])|www\.[^\s()<>]*\([^\s()<>]*\)[^\s()<>]*(?<![.,;!?])|\w+://[^\s()<>]+(?<![.,;!?])|www\.[^\s()<>]+(?<![.,;!?]))')

    def setupUi(self, Form):
        # === Main Window Setup ===
        if self.parentGui.log_on:
            logging.info("Setting up UI components")

        # === Main Horizontal Layout (Chat + Sidebar) ===
        self.horizontalLayout = QHBoxLayout(Form)
        self.horizontalLayout.setObjectName("horizontalLayout")

        # ===============================
        #       LEFT: CHAT AREA
        # ===============================
        self.content = QVBoxLayout()
        self.content.setSpacing(5)
        self.content.setObjectName("content")

        # --- Chat Area (Topic Label + Text Display) ---
        self.chat_area = QVBoxLayout()
        self.chat_area.setSpacing(5)
        self.chat_area.setObjectName("chat_area")

        # * Topic label (appears above the chat log) *
        self.topic_label = QLabel(parent=Form)
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        sizePolicy.setHeightForWidth(self.topic_label.sizePolicy().hasHeightForWidth())
        self.topic_label.setSizePolicy(sizePolicy)
        self.topic_label.setObjectName("topic_label")
        self.chat_area.addWidget(self.topic_label)

        # * Chat display area (read-only text browser) *
        self.display_text = RudeTextBrowser(parent=Form)
        self.display_text.setObjectName("display_text")
        self.chat_area.addWidget(self.display_text)

        # Add chat area to the content layout
        self.content.addLayout(self.chat_area)

        # --- Input field for typing messages ---
        self.text_input = QHBoxLayout()
        self.text_input.setSpacing(5)
        self.text_input.setObjectName("text_input")

        # * Line edit for typing messages *
        self.input = QLineEdit(parent=Form)
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
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
        self.sidebar = QVBoxLayout()
        self.sidebar.setSpacing(5)
        self.sidebar.setObjectName("sidebar")

        # --- Sidebar layout for user list + button ---
        self.users_selector = QVBoxLayout()
        self.users_selector.setSpacing(5)
        self.users_selector.setObjectName("users_selector")

        # * Label above user list *
        self.user_label = QLabel(parent=Form)
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Preferred
        )
        sizePolicy.setHeightForWidth(self.user_label.sizePolicy().hasHeightForWidth())
        self.user_label.setSizePolicy(sizePolicy)
        self.user_label.setObjectName("user_label")
        self.users_selector.addWidget(self.user_label)

        # * List of users (clickable items) *
        self.user_list = RudeUserListWidget(parent=Form, maingui=self.parentGui)
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding
        )
        sizePolicy.setHeightForWidth(self.user_list.sizePolicy().hasHeightForWidth())
        self.user_list.setSizePolicy(sizePolicy)
        self.user_list.setMouseTracking(True)
        self.user_list.setAutoFillBackground(True)
        self.user_list.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.user_list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.user_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.user_list.setItemAlignment(Qt.AlignmentFlag.AlignLeading)
        self.user_list.setObjectName("user_list")

        self.users_selector.addWidget(self.user_list)

        # * Button under user list (e.g. to "Pop In" the window) *
        self.pushButton = QPushButton(parent=Form)
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
        QMetaObject.connectSlotsByName(Form)

        self.enter_filter = EnterFilter(self)
        self.input.installEventFilter(self.enter_filter)
        self.tab_filter = TabEventFilter(self, self.parentGui)
        self.input.installEventFilter(self.tab_filter)
        self.arrow_key_filter = ArrowKeyEventFilter(self)
        self.input.installEventFilter(self.arrow_key_filter)
        if self.parentGui.log_on:
            logging.info("UI setup complete")

    def set_theme(self, Form):
        self.display_text.setStyleSheet(f"""
            color: {self.parentGui.chat_fg};
            background-color: {self.parentGui.chat_bg};
            font-family: {self.parentGui.chat_font_family};
            font-size: {self.parentGui.chat_font_size}px;
        """)

        # Apply User List Theme
        self.user_list.setStyleSheet(f"""
            color: {self.parentGui.list_user_fg};
            background-color: {self.parentGui.list_bg};
            font-family: {self.parentGui.list_font_family};
            font-size: {self.parentGui.list_font_size}px;
        """)

        Form.setStyleSheet(f"""
            QScrollBar:vertical {{
                border: none;
                background: {self.parentGui.scrollbar_bg };
                width: 12px;
                margin: 0px 0px 0px 0px;
            }}

            QScrollBar::handle:vertical {{
                background: {self.parentGui.scrollbar_bg };
                min-height: 20px;
                border-radius: 5px;
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                background: none;
                border: none;
            }}

        """)

    def retranslateUi(self, Form): 
        _translate = QCoreApplication.translate
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
        self.set_theme(Form)
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
        self.parentGui.pop_out_return(self.channel)

    def insert_and_scroll(self):
        self.display_text.moveCursor(QTextCursor.MoveOperation.End)

    def insert_text(self, message):
        urls = self.find_urls(message)
        formatted_text = self.decoder(message + "\n")
        self.tag_text(formatted_text)
        self.tag_urls(urls)

        self.highlight_nicknames()
        self.insert_and_scroll()

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
        cursor = self.display_text.textCursor()
        for text, char_format in formatted_text:
            try:
                cursor.insertText(text, char_format)
            except Exception as e:
                logging.error(f"Error in tag_text: {e}")

    def configure_tag_based_on_attributes(self, attr: dict) -> QTextCharFormat:
        try:
            fmt = QTextCharFormat()
            fmt.setFontFamily(self.parentGui.chat_font_family)
            fmt.setFontPointSize(int(self.parentGui.chat_font_size))
            
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

    def find_urls(self, text):
        # Use the precompiled regex pattern to find URLs
        return self.url_pattern.findall(text)

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

                cursor = self.display_text.textCursor()
                cursor = self.display_text.document().find(url, 0)
            except Exception as e:
                logging.error(f"Error2 in tag_urls: {e}")

            try:
                while not cursor.isNull():
                    cursor.mergeCharFormat(char_format)
                    cursor = self.display_text.document().find(url, cursor)

                cursor = self.display_text.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.Start) 
                while self.display_text.find(url):
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

    def load_channel_messages(self):
        try:
            messages = self.parentGui.irc_client.channel_messages[self.parentGui.irc_client.server][self.channel]
            for message in messages[-150:]:
                cleaned_message = message.rstrip("\r\n")
                self.insert_text(f"{cleaned_message}")
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
            text = self.input.text().strip()
            nickname = self.parentGui.irc_client.nickname
            user_mode = self.parentGui.irc_client.get_user_mode(nickname, self.channel)
            mode_symbol = self.parentGui.irc_client.get_mode_symbol(user_mode) if user_mode else ''
            if self.parentGui.irc_client.use_time_stamp:
                timestamp = datetime.now().strftime('[%H:%M:%S] ')
            else:
                timestamp = ""

            if text.startswith("/"):
                self.parentGui.irc_client.loop.create_task(self.parentGui.irc_client.command_parser(text))
                self.input.clear()
                return

            if self.parentGui.log_on:
                logging.debug(f"Message to send: {text}")

            self.insert_text(f"{timestamp}<{mode_symbol}{self.parentGui.irc_client.nickname}> {text}")
            self.input.clear()
            self.send_message(text)
            self.save_entry_history(text)
            self.highlight_nicknames()
            self.parentGui.irc_client.save_message(self.parentGui.irc_client.server, self.channel, nickname, text, mode_symbol, is_sent=False)
            self.parentGui.irc_client.log_message(self.parentGui.irc_client.server_name, self.channel, nickname, text, is_sent=False)
        except Exception as e:
            logging.error(f"Exception in insert_and_send_message: {e}")

    def show_previous_entry(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.input.setText(self.entry_history[self.history_index])

    def show_next_entry(self):
        if self.history_index < len(self.entry_history) - 1:
            self.history_index += 1
            self.input.setText(self.entry_history[self.history_index])
        elif self.history_index == len(self.entry_history) - 1:
            self.history_index += 1
            self.input.clear()

    def save_entry_history(self, text):
        try:
            # Save the entered message to entry_history
            if text:
                self.entry_history.append(text)

                # Limit the entry_history to the last 10 messages
                if len(self.entry_history) > 10:
                    self.entry_history.pop(0)

                # Reset history_index to the end of entry_history
                self.history_index = len(self.entry_history)
        except Exception as e:
            logging.error(f"Error in save_entry_history: {e}")

    def load_user_list(self):
        for user in self.parentGui.irc_client.channel_users.get(self.channel, []):
            self.user_list.addItem(user)

        self.update_user_label()
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
