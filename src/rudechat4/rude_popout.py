from rudechat4.shared_imports import *
from PyQt6 import QtCore, QtGui, QtWidgets


class EnterFilter(QObject):
    def __init__(self, gui):
        super().__init__()
        self.gui = gui

    def eventFilter(self, obj, event):
        if obj == self.gui.input and event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() in [QtCore.Qt.Key.Key_Enter, QtCore.Qt.Key.Key_Return]:
                logging.debug("Enter key pressed in input field")
                self.gui.insert_and_send_message()  # Handle Enter key press
                return True  
            else:
                logging.debug("Else block hit, key pressed is not Enter")
        return super().eventFilter(obj, event)  # Let other events pass normally

class RudePopout(QObject):
    def __init__(self):
        super().__init__()
        self.parentGui = None
        self.channel = None

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

        # Topic header
        self.topic_label.setText(_translate("Form", "Topic: "))
        if self.parentGui.log_on:
            logging.debug("Topic label set")

        # Sidebar label
        self.user_label.setText(_translate("Form", "Users (0)"))
        if self.parentGui.log_on:
            logging.debug("User label set")

        # Button text
        self.pushButton.setText(_translate("Form", "Pop In"))
        self.input.setFocus()
        self.load_user_list()

        if self.parentGui.log_on:
            logging.info(f"channel and parent is set to: {self.channel} & {self.parentGui}")

    def insert_text(self, message):
        cleaned_message = message.rstrip("\r\n")
        self.display_text.append(f"{cleaned_message}")

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
            if self.parentGui.log_on:
                logging.debug(f"Message to send: {text}")
            self.display_text.append(f"<{self.parentGui.irc_client.nickname}> {text}")  # Append keeps previous content and adds a new line
            self.input.clear()
            self.send_message(text)
        except Exception as e:
            logging.error(f"Exception in insert_and_send_message: {e}")

    def load_user_list(self):
        for user in self.parentGui.irc_client.channel_users.get(self.channel, []):
            self.user_list.addItem(user)
        self.highlight_away_users()

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

