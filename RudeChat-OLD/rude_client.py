#!/usr/bin/env python
from shared_imports import *
class IRCClient:
    MAX_MESSAGE_HISTORY_SIZE = 200

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG, filename='irc_client.log', filemode='w')
        # Initialization method and related properties
        self.irc_client_gui = None
        self.decoder = irctokens.StatefulDecoder()
        self.encoder = irctokens.StatefulEncoder()
        self.message_queue = Queue()
        self.send_message_queue = Queue()
        self.exit_event = threading.Event()

        # Data structures and storage properties
        self.channel_messages = {}
        self.joined_channels: list = []
        self.channel_list = []
        self.current_channel: str = ''
        self.user_list = {}
        self.temp_user_list = {}
        self.user_flags = {}
        self.whois_data = {}
        self.dm_users = []
        self.dm_messages = {}
        self.user_dual_privileges = {}
        self.special_char_to_mode = {}
        self.backup_nicknames = ["Rude", "stixie"]
        self.ignore_list = []
        self.friend_list = []
        self.server_capabilities = {}
        self.load_ignore_list()
        self.load_friend_list()

        # Threading and synchronization related properties
        self.user_list_lock = threading.Lock()
        self.receive_thread = None
        self.stay_alive_thread = None
        self.reconnection_thread = None
        self.channel_list_window = None
        self.reset_timer = None

        # Protocol specific properties
        self.current_nick_index = 0
        self.has_auto_joined = False
        self.sound_ctcp_count = 0
        self.sound_ctcp_limit = 5
        self.sound_ctcp_limit_flag = False
        self.show_channel_list_flag = False 

        # Other properties
        self.reset_timer = None

    def read_config(self, config_file):
        """
        Reads the config file
        """
        config = configparser.ConfigParser()
        config.read(config_file)

        self.server = config.get('IRC', 'server')
        self.port = config.getint('IRC', 'port')
        self.ssl_enabled = config.getboolean('IRC', 'ssl_enabled')
        self.nickname = config.get('IRC', 'nickname')
        self.nickserv_password = config.get('IRC', 'nickserv_password')
        self.auto_join_channels = config.get('IRC', 'auto_join_channels').split(',')

        # SASL configurations
        self.sasl_enabled = config.getboolean('IRC', 'sasl_enabled', fallback=False)
        self.sasl_username = config.get('IRC', 'sasl_username', fallback=self.nickname)
        self.sasl_password = config.get('IRC', 'sasl_password', fallback=self.nickserv_password)

    def connect(self):
        """
        Connect to the IRC server
        """
        try:
            # Determine if running as a script or as a frozen executable
            if getattr(sys, 'frozen', False):
                # Running as compiled
                script_directory = os.path.dirname(sys.executable)
            else:
                # Running as script
                script_directory = os.path.dirname(os.path.abspath(__file__))

            # Set absolute path for the Splash directory
            splash_dir = os.path.join(script_directory, 'Splash')
            splash_files = [f for f in os.listdir(splash_dir) if os.path.isfile(os.path.join(splash_dir, f))]
            selected_splash_file = random.choice(splash_files)

            # Read the selected ASCII art file
            with open(os.path.join(splash_dir, selected_splash_file), 'r', encoding='utf-8') as f:
                clover_art = f.read()

            print(f'Connecting to server: {self.server}:{self.port}')

            # Use socket.create_connection to automatically determine address family
            self.irc = socket.create_connection((self.server, self.port))

            # Wrap the socket with SSL if needed
            if self.ssl_enabled:
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                context.check_hostname = True
                context.verify_mode = ssl.CERT_REQUIRED
                self.irc = context.wrap_socket(self.irc, server_hostname=self.server)

            self.irc_client_gui.update_message_text(f'Connecting to server: {self.server}:{self.port}\n')

            if self.sasl_enabled:
                self.irc.send(bytes('CAP REQ :sasl\r\n', 'UTF-8'))

            self.irc.send(bytes(f'NICK {self.nickname}\r\n', 'UTF-8'))
            self.irc.send(bytes(f'USER {self.nickname} 0 * :{self.nickname}\r\n', 'UTF-8'))

            print(f'Connected to server: {self.server}:{self.port}')
            self.irc_client_gui.update_message_text(f'Connected to server: {self.server}:{self.port}\n')
            self.irc_client_gui.update_message_text(clover_art)

        except socket.timeout:
            print("Connection timed out.")
            self.irc_client_gui.update_message_text("Connection timed out.\n")

        except socket.error as e:
            print(f"Socket error: {e}")
            self.irc_client_gui.update_message_text(f"Socket error: {e}\n")

        except ssl.SSLError as e:
            print(f"SSL error: {e}")
            self.irc_client_gui.update_message_text(f"SSL error: {e}\n")

        except Exception as e:
            print(f"Unexpected error: {e}")
            self.irc_client_gui.update_message_text(f"Unexpected error: {e}\n")

    def disconnect(self):
        """
        Disconnect from the IRC server and stop any related threads.
        """
        channel = None
        self.exit_event.set()

        # Stop the threads if they're running
        for thread in [self.receive_thread, self.stay_alive_thread, self.reconnection_thread, self.reset_timer]:
            if thread and thread.is_alive():
                thread.join(timeout=1)

        # Close the socket connection
        if hasattr(self, 'irc'):
            try:
                self.irc.close()
            except Exception as e:
                print("Error while closing the socket:")
                traceback.print_exc()

        # Reset states or data structures
        self.channel_list = []
        self.temp_user_list = {}
        self.user_flags = {}
        self.whois_data = {}
        self.dm_users = []
        self.dm_messages = {}
        self.user_dual_privileges = {}
        self.special_char_to_mode = {}
        self.server_capabilities = {}
        self.joined_channels = []
        self.current_channel = ''
        self.channel_messages = {}
        self.temp_user_list = {}
        self.user_list = {}
        self.has_auto_joined = False
        print(f"Disconnected")
        self.irc_client_gui.update_message_text(f"Disconnected\r\n")
        self.irc_client_gui.update_user_list(channel)
        self.irc_client_gui.update_joined_channels_list(channel)
        self.irc_client_gui.clear_chat_window()

    def reconnect(self, server=None, port=None):
        """
        Reconnect to the IRC server.
        """
        if server:
            self.set_server(server, port)
        self.irc_client_gui.clear_chat_window()
        self.exit_event.clear()

        # Start a new connection
        self.reconnection_thread = threading.Thread(target=self.start)
        self.reconnection_thread.daemon = True
        self.reconnection_thread.start()

    def set_server(self, server, port=None):
        self.server = server
        if port:
            self.port = port
    
    def is_thread_alive(self):
        return self.reconnection_thread.is_alive()

    def send_message(self, message):
        """
        Sends messages
        """
        # Generate timestamp
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')

        # Split the message into lines
        lines = message.split("\n")

        for line in lines:
            # Send each line to the server
            self.irc.send(bytes(f'{line}\r\n', 'UTF-8'))

            # Extract the target channel and actual message content from the line
            target_match = re.match(r'PRIVMSG (\S+) :(.+)', line)
            if not target_match:
                continue

            target_channel, message_content = target_match.groups()

            # Check if it's a CTCP ACTION and format accordingly
            if message_content.startswith("\x01ACTION ") and message_content.endswith("\x01"):
                action_content = message_content[8:-1]
                formatted_message = f"* {self.nickname} {action_content}"
            else:
                formatted_message = message_content 

            # Generate the actual content of the message, not the entire command
            message_data = (timestamp, self.nickname, formatted_message)

            # Handle channel messages
            self.channel_messages.setdefault(target_channel, []).append(message_data)
            if len(self.channel_messages[target_channel]) > self.MAX_MESSAGE_HISTORY_SIZE:
                self.channel_messages[target_channel] = self.channel_messages[target_channel][-self.MAX_MESSAGE_HISTORY_SIZE:]

            # Handle DMs
            if target_channel not in self.joined_channels:
                if formatted_message.startswith("* "):
                    sent_dm = f"{timestamp} {formatted_message}\n"
                else:
                    sent_dm = f"{timestamp} <{self.nickname}> {formatted_message}\n"
                self.dm_messages.setdefault(target_channel, []).append(sent_dm)

            # Log the message with the timestamp for display
            self.log_message(target_channel, self.nickname, formatted_message, is_sent=True)

    def _send_message(self, message):
        """
        Enqueues messages to be sent by the sender_thread.
        """
        self.send_message_queue.put(message)

    def process_send_queue(self):
        while True:
            message = self.send_message_queue.get()
            try:
                self.send_message(message)
            except BrokenPipeError:
                # Handle socket being closed
                print("Socket closed.")
            self.send_message_queue.task_done()

    def send_ctcp_request(self, target, command, parameter=None):
        """
        Send a CTCP request to the specified target (user or channel).
        """
        message = f'\x01{command}'
        if parameter:
            message += f' {parameter}'
        message += '\x01'
        self._send_message(f'PRIVMSG {target} :{message}')

    def change_nickname(self, new_nickname):
        """
        Changes your nickname
        """
        self._send_message(f'NICK {new_nickname}')
        self.nickname = new_nickname
        self.irc_client_gui.update_message_text(f'Nickname changed to: {new_nickname}\n')

    def join_channel(self, channel):
        """
        Joins a channel
        """
        self._send_message(f'JOIN {channel}')
        self.joined_channels.append(channel)
        self.channel_messages[channel] = []
        self.user_list[channel] = []
        self.irc_client_gui.update_joined_channels_list(channel)
        time.sleep(1)

    def leave_channel(self, channel):
        """
        Leaves a channel
        """
        self._send_message(f'PART {channel}')
        if channel in self.joined_channels:
            self.joined_channels.remove(channel)
        if channel in self.channel_messages:
            del self.channel_messages[channel]
        if channel in self.user_list:
            del self.user_list[channel]
        if self.current_channel == channel:
            self.current_channel = ''
        self.irc_client_gui.update_joined_channels_list(channel)

    def keep_alive(self):
        """
        Periodically sends a PING request.
        """
        while not self.exit_event.is_set():
            time.sleep(195)
            param = self.server
            self._send_message(f'PING {param}')

    def ping_server(self, target=None):
        """
        Like the keep alive, this is used by the command parser to send a manual PING request
        """
        if target:
            param = target
        else:
            param = self.server
        self._send_message(f'PING {param}')

    def sync_user_list(self):
        """
        Syncs the user list via /users
        """
        self.user_list[self.current_channel] =[]
        self._send_message(f'NAMES {self.current_channel}')

    def strip_ansi_escape_sequences(self, text):
        # Strip ANSI escape sequences
        ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
        cleaned_text = ansi_escape.sub('', text)

        # Strip IRC color codes
        irc_color = re.compile(r'\x03\d{1,2}(,\d{1,2})?')
        return irc_color.sub('', cleaned_text)

    def handle_incoming_message(self):
        """
        The main method which handles incoming server and chat messages. 
        """
        remaining_data = ""

        while not self.exit_event.is_set():
            try:
                if not hasattr(self, 'irc'):
                    print("Socket not initialized.")
                data = self.irc.recv(4096).decode('UTF-8', errors='ignore')
                data = self.strip_ansi_escape_sequences(data)
                if not data:
                    break

                #prepend any remaining_data from the previous iteration to the new data
                data = remaining_data + data

                received_messages = ""
                self.server_feedback_buffer = ""
                messages = data.split('\r\n')

                #if the last message is incomplete, store it in remaining_data
                if not data.endswith('\r\n'):
                    remaining_data = messages[-1]
                    messages = messages[:-1]
                else:
                    remaining_data = ""

                #process each complete message
                for raw_message in messages:
                    # Generate timestamp
                    timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
                    # Skip empty lines or lines with only whitespace
                    raw_message = raw_message.strip()
                    if not raw_message:
                        continue

                    try:
                        tokens = irctokens.tokenise(raw_message)
                    except ValueError as e:
                        print(f"Error: {e}")
                        continue

                    if tokens.source is not None:
                        sender = tokens.hostmask.nickname
                    else:
                        sender = None
                    self.message_queue.put(raw_message)

                    match tokens.command:
                        case "PING":
                            self.handle_ping(tokens)
                        
                        case "ERROR":
                            self.server_feedback_buffer += raw_message + "\n"
                            self.irc_client_gui.update_server_feedback_text(raw_message)
                        
                        case "CAP":
                            self.handle_cap(tokens)

                        case "AUTHENTICATE":
                            self.handle_sasl_auth(tokens)

                        case "903":
                            self.handle_sasl_successful()

                        case "904":
                            self.handle_sasl_failed()

                        case "376" | "001":
                            self.handle_welcome_or_end_of_motd(raw_message)

                        case "NOTICE":
                            received_message = self.handle_notice(tokens, timestamp, sender)
                            if received_message:
                                received_messages += received_message

                        case "005":
                            self.handle_isupport(tokens)

                        case "353":
                            self.handle_353(tokens)

                        case "352" | "315":
                            self.handle_who_reply(tokens)

                        case "366":
                            self.handle_366(tokens)

                        case "367":  
                            self.handle_banlist(tokens)
                            
                        case "368":  
                            self.handle_endofbanlist(tokens)

                        case "311" | "312" | "313" | "317" | "319" | "301" | "671" | "338" | "318":
                            self.handle_whois_replies(tokens.command, tokens)
                        case "391":
                            self.handle_time_request(tokens)
                        case "433":
                            self.handle_nickname_conflict(tokens)

                        case "322":
                            self.handle_list_response(tokens)
                        case "323":
                            self.save_channel_list_to_file()

                        case "PART":
                            self.handle_part_command(tokens, raw_message)

                        case "JOIN":
                            self.handle_join_command(tokens, raw_message)

                        case "QUIT":
                            self.handle_quit_command(tokens, raw_message)

                        case "NICK":
                            old_nickname = tokens.hostmask.nickname
                            new_nickname = tokens.params[0]
                            self.handle_nick_change(old_nickname, new_nickname, channel, raw_message)

                        case "MODE":
                            channel = tokens.params[0]
                            mode = tokens.params[1]
                            if len(tokens.params) > 2:  # Ensure there's a target user for the mode change
                                target_user = tokens.params[2]
                                self.handle_mode_changes(channel, mode, target_user)
                            self.irc_client_gui.update_server_feedback_text(raw_message)
                        case "KICK":
                            self.handle_kick_event(tokens, raw_message)

                        case "PRIVMSG":
                            received_messages = self.handle_privmsg(tokens, timestamp)

                        case _:
                            self.handle_default_case(raw_message)

                    # limit the chat history size for each channel
                    for channel in self.channel_messages:
                        if len(self.channel_messages[channel]) > self.MAX_MESSAGE_HISTORY_SIZE:
                            self.channel_messages[channel] = self.channel_messages[channel][-self.MAX_MESSAGE_HISTORY_SIZE:]

            except OSError as e:
                if e.errno == 9:
                    print("Socket closed.")
                    break
                else:
                    print(f"Unexpected Error during data reception: {e}")

            if received_messages:
                self.message_queue.put(received_messages)
                self.irc_client_gui.update_message_text(received_messages)

    def handle_banlist(self, tokens):
        """
        Handle the RPL_BANLIST reply, which provides info about each ban mask.
        """
        channel = tokens.params[1]
        banmask = tokens.params[2]
        setter = tokens.params[3]
        timestamp = tokens.params[4]
        
        # Construct the ban information message
        ban_info = f"Channel: {channel}, Banmask: {banmask}, Set by: {setter}, Timestamp: {timestamp}\r\n"
        
        # Update the GUI's message text with this ban information
        self.irc_client_gui.update_ban_list(channel, ban_info=ban_info)

    def handle_endofbanlist(self, tokens):
        """
        Handle the RPL_ENDOFBANLIST reply, signaling the end of the ban list.
        """
        channel = tokens.params[1]
        
        # Notify the user that the ban list has ended
        end_message = f"End of ban list for channel: {channel}\r\n"
        self.irc_client_gui.update_ban_list(channel, end_message=end_message)

    def handle_list_response(self, tokens):
        """
        Handle the individual channel data from the LIST command.
        """
        channel_name = tokens.params[1]
        visible_users = tokens.params[2]
        topic = tokens.params[3]

        channel_info = {
            "name": channel_name,
            "users": visible_users,
            "topic": topic
        }

        self.channel_list.append(channel_info)

    def handle_time_request(self, tokens):
        """
        Handle the server's response for the TIME command.
        """
        server_name = tokens.params[0]  # The server's name
        local_time = tokens.params[1]   # The local time on the server

        # Display the information in your client's GUI
        message = f"Server Time from {server_name}: {local_time}"
        self.irc_client_gui.update_message_text(message)

    def handle_ping(self, tokens):
        ping_param = tokens.params[0]
        pong_response = f'PONG {ping_param}'
        self._send_message(pong_response)

    def handle_cap(self, tokens):
        if "ACK" in tokens.params and "sasl" in tokens.params:
            self._send_message("AUTHENTICATE PLAIN")
        elif "NAK" in tokens.params:
            print("Server does not support SASL.")
            self.irc_client_gui.update_server_feedback_text("Error: Server does not support SASL.")
            self._send_message("CAP END")

    def handle_sasl_auth(self, tokens):
        if tokens.params[0] == "+":
            # Server is ready to receive authentication data.
            import base64
            auth_string = f"{self.sasl_username}\0{self.sasl_username}\0{self.sasl_password}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            self._send_message(f"AUTHENTICATE {encoded_auth}")

    def handle_sasl_successful(self):
        print("SASL authentication successful.")
        self.irc_client_gui.update_server_feedback_text("SASL authentication successful.")
        # End the capability negotiation after successful SASL authentication
        self._send_message("CAP END")

    def handle_sasl_failed(self):
        print("SASL authentication failed!")
        self.irc_client_gui.update_server_feedback_text("Error: SASL authentication failed!")
        # End the capability negotiation even if SASL authentication failed
        self._send_message("CAP END")

    def handle_welcome_or_end_of_motd(self, raw_message):
        self.irc_client_gui.update_server_feedback_text(raw_message)
        self._send_message(f'PRIVMSG NickServ :IDENTIFY {self.nickserv_password}')
        if not self.has_auto_joined:
            for channel in self.auto_join_channels:
                self.join_channel(channel)
            self.has_auto_joined = True

    def handle_notice(self, tokens, timestamp, sender):
        target = tokens.params[0]
        notice_content = tokens.params[1]

        # Check if the target is a channel or the user
        if target.startswith(("#", "&", "+", "!")):
            
            # This is a channel-specific NOTICE
            if target not in self.channel_messages:
                self.channel_messages[target] = []
            self.channel_messages[target].append((timestamp, sender, notice_content))
            if target == self.current_channel:
                return f'{timestamp} [NOTICE] <{sender}> {notice_content}'
            else:
                self.notify_channel_activity(target)
                return None
        else:            
            # This is a user-specific NOTICE, display in a general "server" or "status" tab
            server_tab_content = f'[SERVER NOTICE] <{sender}> {notice_content}'
            self.irc_client_gui.update_server_feedback_text(server_tab_content)
            return None

    def handle_isupport(self, tokens):
        """
        Handle the RPL_ISUPPORT (005) server message.
        This method processes the server capabilities and updates the client's knowledge about them.
        """
        isupport_params = tokens.params[:-1]

        # Store these in a dictionary 
        new_capabilities = {} 
        for param in isupport_params:
            if '=' in param:
                key, value = param.split('=', 1)
                if key not in self.server_capabilities:  
                    new_capabilities[key] = value
                    self.server_capabilities[key] = value

                    # If the capability is PREFIX, update the special_char_to_mode
                    if key == 'PREFIX':
                        modes, symbols = value[1:].split(')', 1)
                        self.special_char_to_mode = dict(zip(symbols, modes))

            else:
                # Some capabilities might just be flags without a value
                if param not in self.server_capabilities:
                    new_capabilities[param] = True
                    self.server_capabilities[param] = True

        # Display capabilities:
        for key, value in new_capabilities.items():
            display_text = f"{key}: {value}"
            self.irc_client_gui.update_server_feedback_text(display_text)

    def handle_353(self, tokens):
        if len(tokens.params) == 4:
            channel = tokens.params[2]
            users = tokens.params[3].split()
        elif len(tokens.params) == 3:
            channel = tokens.params[1]
            users = tokens.params[2].split()
        else:
            print("Error: Unexpected format for the 353 command.")
            return

        # Initialize channel if not already present in temp_user_list
        if channel not in self.temp_user_list:
            self.temp_user_list[channel] = []

        self.temp_user_list[channel].extend(users)  # Accumulate users in the temp list

    def handle_366(self, tokens):
        channel = tokens.params[1]

        with self.user_list_lock:
            if channel in self.temp_user_list:
                self.user_list[channel] = self.temp_user_list[channel]

                # Initialize user_flags for the channel based on the complete user list
                self.initialize_user_flags_from_list(channel, self.temp_user_list[channel])

                del self.temp_user_list[channel]

    def handle_who_reply(self, tokens):
        """
        Handle the WHO reply from the server.
        """
        if not hasattr(self, 'who_details'):
            self.who_details = []

        if tokens.command == "352":  # Standard WHO reply
            # Parse the WHO reply
            channel = tokens.params[1]
            username = tokens.params[2]
            host = tokens.params[3]
            server = tokens.params[4]
            nickname = tokens.params[5]
            user_details = {
                "nickname": nickname,
                "username": username,
                "host": host,
                "server": server,
                "channel": channel
            }
            self.who_details.append(user_details)

        elif tokens.command == "315":  # End of WHO list
            messages = []
            for details in self.who_details:
                message = f"User {details['nickname']} ({details['username']}@{details['host']}) on {details['server']} in {details['channel']}\r\n"
                messages.append(message)
            final_message = "\n".join(messages)
            self.irc_client_gui.update_message_text(final_message)
            # Reset the who_details for future use
            self.who_details = []

    def handle_whois_replies(self, command, tokens):
        nickname = tokens.params[1]

        if command == "311":
            username = tokens.params[2]
            hostname = tokens.params[3]
            realname = tokens.params[5]
            self.whois_data[nickname] = {"Username": username, "Hostname": hostname, "Realname": realname}

        elif command == "312":
            server_info = tokens.params[2]
            if self.whois_data.get(nickname):
                self.whois_data[nickname]["Server"] = server_info

        elif command == "313":
            operator_info = tokens.params[2]
            if self.whois_data.get(nickname):
                self.whois_data[nickname]["Operator"] = operator_info

        elif command == "317":
            idle_time_seconds = int(tokens.params[2])
            idle_time = str(datetime.timedelta(seconds=idle_time_seconds))
            if self.whois_data.get(nickname):
                self.whois_data[nickname]["Idle Time"] = idle_time

        elif command == "319":
            channels = tokens.params[2]
            self.whois_data[nickname]["Channels"] = channels

        elif command == "301":
            away_message = tokens.params[2]
            if nickname not in self.whois_data:
                self.whois_data[nickname] = {}  
            self.whois_data[nickname]["Away"] = away_message

        elif command == "671":
            secure_message = tokens.params[2]
            self.whois_data[nickname]["Secure Connection"] = secure_message

        elif command == "338":
            ip_address = tokens.params[2]
            self.whois_data[nickname]["Actual IP"] = ip_address

        elif command == "318":
            if self.whois_data.get(nickname):
                whois_response = f"WHOIS for {nickname}:\n"
                for key, value in self.whois_data[nickname].items():
                    whois_response += f"{key}: {value}\n"

                # Generate and append the /ignore suggestion
                ignore_suggestion = f"*!{self.whois_data[nickname]['Username']}@{self.whois_data[nickname]['Hostname']}"
                whois_response += f"\nSuggested /ignore mask: {ignore_suggestion}\n"

                self.irc_client_gui.update_message_text(whois_response)

    def handle_nickname_conflict(self, tokens):
        if tokens.params and len(tokens.params) > 1:
            taken_nickname = tokens.params[1]
            error_message = tokens.params[2]
            msg = f"Error: The nickname {taken_nickname} is already in use. Reason: {error_message}"
            self.irc_client_gui.update_server_feedback_text(msg)

            # Try the next nickname in the backup list
            if self.current_nick_index < len(self.backup_nicknames):
                new_nickname = self.backup_nicknames[self.current_nick_index]
                self.current_nick_index += 1
                self.change_nickname(new_nickname)
                feedback = f"Attempting to use nickname: {new_nickname}"
                self.irc_client_gui.update_server_feedback_text(feedback)
            else:
                feedback = "All backup nicknames are exhausted. Please set a new nickname."
                self.irc_client_gui.update_server_feedback_text(feedback)

    def handle_part_command(self, tokens, raw_message):
        if tokens.source is not None:
            quit_user = tokens.hostmask.nickname
            quit_user = self.strip_nick_prefix(quit_user)
            channel = tokens.params[0]

            with self.user_list_lock:
                if channel in self.user_list:
                    similar_users = [user for user in self.user_list[channel] 
                                     if user == quit_user or 
                                     user.startswith('@' + quit_user) or 
                                     user.startswith('+' + quit_user)]
                    for user in similar_users:
                        self.user_list[channel].remove(user)
                    # Only update the GUI if the affected channel is the current channel
                    if channel == self.irc_client_gui.current_channel:
                        self.irc_client_gui.update_user_list(channel)

        self.server_feedback_buffer += raw_message + "\n"
        self.irc_client_gui.update_server_feedback_text(raw_message)

    def handle_join_command(self, tokens, raw_message):
        if tokens.source is not None:
            join_user = tokens.hostmask.nickname
            channel = tokens.params[0]

            if join_user in self.friend_list:
                self.friend_online(channel, join_user)

            with self.user_list_lock:
                if channel in self.user_list:
                    if join_user not in self.user_list[channel]:
                        self.user_list[channel].append(join_user)
                    else:
                        self.user_list[channel].remove(join_user)
                        self.user_list[channel].append(join_user) 
                    # Only update the GUI if the affected channel is the current channel
                    if channel == self.irc_client_gui.current_channel:
                        self.irc_client_gui.update_user_list(channel)
                else:
                    self.user_list[channel] = [join_user]
                    # Only update the GUI if the affected channel is the current channel
                    if channel == self.irc_client_gui.current_channel:
                        self.irc_client_gui.update_user_list(channel)

        self.server_feedback_buffer += raw_message + "\n"
        self.irc_client_gui.update_server_feedback_text(raw_message)

    def handle_quit_command(self, tokens, raw_message):
        if tokens.source is not None:
            quit_user = tokens.hostmask.nickname

            with self.user_list_lock:
                for channel in self.user_list:
                    similar_users = [user for user in self.user_list[channel] 
                                     if user == quit_user or 
                                     user.startswith('@' + quit_user) or 
                                     user.startswith('+' + quit_user)]
                    for user in similar_users:
                        self.user_list[channel].remove(user)
                    # Only update the GUI if the affected channel is the current channel
                    if channel == self.irc_client_gui.current_channel:
                        self.irc_client_gui.update_user_list(channel)

        self.server_feedback_buffer += raw_message + "\n"
        self.irc_client_gui.update_server_feedback_text(raw_message)

    def handle_nick_change(self, old_nickname, new_nickname, channel, raw_message):
        # Display the nick change message in the chat window
        nick_change_message_content = f"{old_nickname} has changed their nickname to {new_nickname}"
        self.irc_client_gui.display_message_in_chat(nick_change_message_content)
        
        # Update internal user lists to reflect the nickname change
        with self.user_list_lock:
            for chan, users in self.user_list.items():
                if old_nickname in users:
                    users.remove(old_nickname)
                    users.append(new_nickname)
                elif "@" + old_nickname in users:
                    users.remove("@" + old_nickname)
                    users.append("@" + new_nickname)
                elif "+" + old_nickname in users:
                    users.remove("+" + old_nickname)
                    users.append("+" + new_nickname)
        
        if channel == self.irc_client_gui.current_channel:
            self.irc_client_gui.update_user_list(channel)
            
        self.irc_client_gui.update_server_feedback_text(raw_message)

    def handle_kick_event(self, tokens, raw_message):
        """
        Handle the KICK event from the server.
        """
        channel = tokens.params[0]
        kicked_nickname = tokens.params[1]
        reason = tokens.params[2] if len(tokens.params) > 2 else 'No reason provided'
        
        # Display the kick message in the chat window
        kick_message_content = f"{kicked_nickname} has been kicked from {channel} by {tokens.hostmask.nickname} ({reason})"
        self.irc_client_gui.display_message_in_chat(kick_message_content)

        # Update internal user lists to reflect the kick
        with self.user_list_lock:
            if channel in self.user_list:
                if kicked_nickname in self.user_list[channel]:
                    self.user_list[channel].remove(kicked_nickname)
                elif "@" + kicked_nickname in self.user_list[channel]:
                    self.user_list[channel].remove("@" + kicked_nickname)
                elif "+" + kicked_nickname in self.user_list[channel]:
                    self.user_list[channel].remove("+" + kicked_nickname)

        # Update the GUI user list if the kick happened in the current channel
        if channel == self.irc_client_gui.current_channel:
            self.irc_client_gui.update_user_list(channel)

        # Update server feedback
        self.irc_client_gui.update_server_feedback_text(raw_message)

    def should_ignore_message(self, hostmask, sender):
        """Determine if a message should be ignored."""
        return self.should_ignore(hostmask) or sender in self.ignore_list

    def format_received_message(self, message_content, sender):
        """Format the received message."""
        if message_content.startswith("\x01ACTION ") and message_content.endswith("\x01"):
            action_content = message_content[8:-1]
            return f"* {sender} {action_content}"
        return message_content

    def handle_dm(self, sender, formatted_message, timestamp):
        """Handle Direct Messages (DMs)."""
        if sender not in self.dm_users:
            self.dm_users.append(sender)
        if formatted_message.startswith('* '):
            received_dm = f"{timestamp} {formatted_message}\n"
        else:
            received_dm = f"{timestamp} <{sender}> {formatted_message}\n"
        self.log_message(f"{sender}", sender, formatted_message)
        if sender not in self.dm_messages:
            self.dm_messages[sender] = []
        self.dm_messages[sender].append(received_dm)

        # Check if this DM is already in the channels_with_activity list
        dm_name = f"DM: {sender}"
        if dm_name not in self.irc_client_gui.channels_with_activity:
            self.irc_client_gui.channels_with_activity.append(dm_name)
        self.irc_client_gui.update_joined_channels_list(dm_name)

        # Only display the DM in the GUI if the currently selected channel is the DM from this sender
        if self.current_channel == sender:
            self.irc_client_gui.update_message_text(received_dm, sender=sender, is_dm=True)

        # Handling CTCP requests here, inside the DM section
        if formatted_message.startswith("\x01") and formatted_message.endswith("\x01"):
            received_message = self.handle_ctcp_request(sender, formatted_message)
            if received_message:
                if sender not in self.dm_messages:
                    self.dm_messages[sender] = []
                self.dm_messages[sender].append((timestamp, received_message))

    def handle_channel_message(self, target, sender, formatted_message, timestamp):
        """Handle channel messages."""
        self.log_message(target, sender, formatted_message, is_sent=False)
        
        # Prepare the formatted message for display
        if formatted_message.startswith("* "):
            # For ACTION messages
            display_message = f'{timestamp} {formatted_message}\n'
        else:
            # For regular messages
            display_message = f'{timestamp} <{sender}> {formatted_message}\n'
        
        # Update the GUI if the message's channel is the current channel
        if self.irc_client_gui.current_channel == target:
            self.irc_client_gui.update_message_text(display_message)

        if sender == self.nickname:
            return

        if self.nickname.lower() in formatted_message.lower():
            self.trigger_beep_notification(channel_name=target, message_content=formatted_message)
            if target not in self.irc_client_gui.channels_with_mentions:
                self.irc_client_gui.channels_with_mentions.append(target)
                self.irc_client_gui.update_joined_channels_list(target)

        if target not in self.irc_client_gui.channels_with_activity:
            self.irc_client_gui.channels_with_activity.append(target)
            self.irc_client_gui.update_joined_channels_list(target)

        if target not in self.channel_messages:
            self.channel_messages[target] = []

        self.channel_messages[target].append((timestamp, sender, formatted_message))

    def handle_privmsg(self, tokens, timestamp):
        """Main function to handle private messages."""
        target = tokens.params[0]
        message_content = tokens.params[1]

        # Constructing the hostmask from the given token attributes
        hostmask = f"{tokens.hostmask.nickname}!{tokens.hostmask.username}@{tokens.hostmask.hostname}"
        sender = tokens.hostmask.nickname  # Define the sender here

        # Check if the message should be ignored
        if self.should_ignore_message(hostmask, sender):
            return

        # Format the message content
        formatted_message = self.format_received_message(message_content, sender)

        if target == self.nickname:
            # This is a DM
            self.handle_dm(sender, formatted_message, timestamp)
        else:
            # This is a channel message
            self.handle_channel_message(target, sender, formatted_message, timestamp)

    def handle_default_case(self, raw_message):
        if raw_message.startswith(':'):
            # move message starting with ":" to server feedback
            self.server_feedback_buffer += raw_message + "\n"
            self.irc_client_gui.update_server_feedback_text(raw_message)
        else:
            # print other messages in the main chat window
            self.irc_client_gui.update_message_text(raw_message)

    def handle_ctcp_request(self, sender, message_content):
        # List of available CTCP commands
        available_ctcp_commands = ["VERSION", "CTCP", "TIME", "PING", "FINGER", "CLIENTINFO", "SOUND", "MOO"]

        # Split the CTCP message content at the first space to separate the command from any data
        ctcp_parts = message_content[1:-1].split(" ", 1)
        ctcp_command = ctcp_parts[0]

        # Check if the CTCP request has more than one command
        if ' ' in ctcp_parts[-1]:  # Checking if there's another space in the last part
            print(f"Ignoring CTCP request with multiple commands from {sender}.")
            return None

        # Check if the CTCP command is available
        if ctcp_command not in available_ctcp_commands:
            print(f"Ignoring unavailable CTCP command '{ctcp_command}' from {sender}.")
            return None

        if ctcp_command == "VERSION":
            # Respond to VERSION request
            version_reply = "\x01VERSION IRishC v2.7\x01"
            self._send_message(f'NOTICE {sender} :{version_reply}')

        elif ctcp_command == "CTCP":
            # Respond to CTCP request
            ctcp_response = "\x01CTCP response\x01"
            self._send_message(f'NOTICE {sender} :{ctcp_response}')

        elif ctcp_command == "TIME":
            import pytz
            dublin_tz = pytz.timezone('Europe/Dublin')
            dublin_time = datetime.datetime.now(dublin_tz).strftime("%Y-%m-%d %H:%M:%S")
            time_reply = "\x01TIME " + dublin_time + "\x01"
            self._send_message(f'NOTICE {sender} :{time_reply}')

        elif ctcp_command == "PING":
            if len(ctcp_parts) > 1:
                ping_data = ctcp_parts[1]
                ping_reply = "\x01PING " + ping_data + "\x01"
                self._send_message(f'NOTICE {sender} :{ping_reply}')
            else:
                print("Received PING CTCP request without timestamp/data.")

        elif ctcp_command == "FINGER":
            # Respond to FINGER request (customize as per requirement)
            version_data = "IRishC v2.7"
            finger_reply = f"\x01FINGER User: {self.nickname}, {self.server}, {version_data}\x01"
            self._send_message(f'NOTICE {sender} :{finger_reply}')

        elif ctcp_command == "CLIENTINFO":
            # Respond with supported CTCP commands
            client_info_reply = "\x01CLIENTINFO VERSION CTCP TIME PING FINGER SOUND\x01"
            self._send_message(f'NOTICE {sender} :{client_info_reply}')

        elif ctcp_command == "SOUND":
            if self.sound_ctcp_count < self.sound_ctcp_limit:
                # Increment the counter
                self.sound_ctcp_count += 1
                # SOUND CTCP can include a file or description of the sound. This is just for logging.
                sound_data = ctcp_parts[1] if len(ctcp_parts) > 1 else "Unknown sound"
                self.trigger_beep_notification()
            else:
                print("SOUND CTCP limit reached. Ignoring...")
                if not self.sound_ctcp_limit_flag:  # If the flag isn't set yet
                    self.sound_ctcp_limit_flag = True
                    self.start_reset_timer()

        elif ctcp_command == "MOO":
            moo_reply = "MOO!"
            version_data = "IRishC v2.7"
            cow_hello = "Hi Cow!"
            self._send_message(f'NOTICE {sender} :{moo_reply}, {version_data}, {cow_hello}')

        else:
            if message_content.startswith("\x01ACTION") and message_content.endswith("\x01"):
                action_content = message_content[8:-1]
                action_message = f"* {sender} {action_content}"
                self.log_message(self.current_channel, sender, action_message, is_sent=False)
                return action_message
            else:
                self.log_message(self.current_channel, sender, message_content, is_sent=False)
                return f'<{sender}> {message_content}'
        return None  # No standard message to display

    def start_reset_timer(self):
        # If the flag isn't set, don't start the timer
        if not self.sound_ctcp_limit_flag:
            return

        # If a timer already exists, cancel it to avoid overlapping timers
        if self.reset_timer:
            self.reset_timer.cancel()

        # Set up the timer to call reset_counter after 15 minutes (900 seconds)
        self.reset_timer = threading.Timer(900, self.reset_counter)
        self.reset_timer.daemon = True
        self.reset_timer.start()

    def reset_counter(self):
        print("Resetting SOUND CTCP counter...")
        self.sound_ctcp_count = 0
        self.sound_ctcp_limit_flag = False

    def initialize_user_flags_from_list(self, channel, user_list):
        # Initialize the user_flags for the channel
        self.user_flags[channel] = {}

        # Populate the user_flags based on the user_list
        for user in user_list:
            stripped_user = user.lstrip(''.join(self.special_char_to_mode.keys()))  # Use dynamic symbols
            flags = set()
            for char in user:
                if char in self.special_char_to_mode:  # Use dynamic mapping
                    flags.add(self.special_char_to_mode[char])  # Use dynamic mapping
            self.user_flags[channel][stripped_user] = flags

    def handle_mode_changes(self, channel, mode_string, user):
        if channel not in self.user_flags:
            self.user_flags[channel] = {}

        add_mode = False
        skip_next_mode = False

        for mode in mode_string:
            if skip_next_mode:
                skip_next_mode = False
                continue

            if mode == '+':
                add_mode = True
            elif mode == '-':
                add_mode = False
            else:
                # Skip +q, -q, +b, -b modes
                if mode in 'qb':
                    skip_next_mode = True
                    continue

                if user not in self.user_flags[channel]:
                    self.user_flags[channel][user] = set()

                if add_mode:
                    self.user_flags[channel][user].add(mode)
                else:
                    self.user_flags[channel][user].discard(mode)

        if user in self.user_flags[channel]:  # Check if the user exists in the dictionary
            updated_user_nick = self.format_nick(user, self.user_flags[channel][user])

            self.user_list[channel] = [existing_user for existing_user in self.user_list[channel]
                                       if existing_user.lstrip('@+%') != user]
            self.user_list[channel].append(updated_user_nick)

            if channel == self.irc_client_gui.current_channel:
                self.irc_client_gui.update_user_list(channel)

    def format_nick(self, user, flags):
        """Format the nick based on the flags."""
        # Check for flags in order of precedence
        if 'q' in flags:  # Adding support for channel owner
            return '~' + user
        elif 'o' in flags:
            return '@' + user
        elif 'h' in flags:
            return '%' + user
        elif 'v' in flags:
            return '+' + user
        else:
            return user

    def trigger_beep_notification(self, channel_name=None, message_content=None):
        """
        You've been pinged! Plays a beep or noise on mention.
        """
        
        # Determine if running as a script or as a frozen executable
        if getattr(sys, 'frozen', False):
            # Running as compiled
            script_directory = os.path.dirname(sys.executable)
        else:
            # Running as script
            script_directory = os.path.dirname(os.path.abspath(__file__))
        
        if sys.platform.startswith("linux"):
            # Linux-specific notification sound using paplay
            sound_path = os.path.join(script_directory, "Sounds", "Notification4.wav")
            os.system(f"paplay {sound_path}")
        elif sys.platform == "darwin":
            # macOS-specific notification sound using afplay
            os.system("afplay /System/Library/Sounds/Ping.aiff")
        elif sys.platform == "win32":
            # Windows-specific notification using winsound
            import winsound
            duration = 75  # milliseconds
            frequency = 1200  # Hz
            winsound.Beep(frequency, duration)
        else:
            # For other platforms, print a message
            print("Beep notification not supported on this platform.")

        try:
            self.irc_client_gui.trigger_desktop_notification(channel_name, message_content=message_content)
        except Exception as e:
            print(f"Error triggering desktop notification: {e}")

    def sanitize_channel_name(self, channel):
        #gotta remove any characters that are not alphanumeric or allowed special characters
        return re.sub(r'[^\w\-\[\]{}^`|]', '_', channel)

    def log_message(self, channel, sender, message, is_sent=False):
        """
        Logs your chats for later use.
        """
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Split the message into lines
        lines = message.split("\n")
        
        # Detect if the message is an action message
        is_action = lines[0].startswith('* ')
        
        # Construct the log line
        if is_sent:
            if is_action:
                log_line = f'[{timestamp}] {lines[0]}\n'
            else:
                log_line = f'[{timestamp}] <{self.nickname}> {lines[0]}\n'
        else:
            if is_action:
                log_line = f'[{timestamp}] {lines[0]}\n'
            else:
                log_line = f'[{timestamp}] <{sender}> {lines[0]}\n'
        
        # Add the subsequent lines without timestamp
        for line in lines[1:]:
            if is_action:
                log_line += f'           {line}\n'
            else:
                log_line += f'           <{sender if is_sent else self.nickname}> {line}\n'
        
        # Determine if running as a script or as a frozen executable
        if getattr(sys, 'frozen', False):
            # Running as compiled
            script_directory = os.path.dirname(sys.executable)
        else:
            # Running as script
            script_directory = os.path.dirname(os.path.abspath(__file__))
        
        # Construct the full path for the Logs directory
        logs_directory = os.path.join(script_directory, 'Logs')
        
        # Create the Logs directory if it doesn't exist
        os.makedirs(logs_directory, exist_ok=True)

        # Construct the full path for the log file inside the Logs directory
        filename = os.path.join(logs_directory, f'irc_log_{self.sanitize_channel_name(channel)}.txt')

        with open(filename, 'a', encoding='utf-8') as file:
            file.write(log_line)

    def save_friend_list(self):
        """
        Save Friend list!
        """
        
        # Determine if running as a script or as a frozen executable
        if getattr(sys, 'frozen', False):
            # Running as compiled
            script_directory = os.path.dirname(sys.executable)
        else:
            # Running as script
            script_directory = os.path.dirname(os.path.abspath(__file__))
        
        # Construct the full path for the friend_list.txt
        file_path = os.path.join(script_directory, 'friend_list.txt')

        with open(file_path, "w", encoding='utf-8') as f:
            for user in self.friend_list:
                f.write(f"{user}\n")

    def load_friend_list(self):
        """
        Load Friend list!
        """
        
        # Determine if running as a script or as a frozen executable
        if getattr(sys, 'frozen', False):
            # Running as compiled
            script_directory = os.path.dirname(sys.executable)
        else:
            # Running as script
            script_directory = os.path.dirname(os.path.abspath(__file__))
        
        # Construct the full path for the friend_list.txt
        file_path = os.path.join(script_directory, 'friend_list.txt')

        if os.path.exists(file_path):
            with open(file_path, "r", encoding='utf-8') as f:
                self.friend_list = [line.strip() for line in f.readlines()]

    def save_ignore_list(self):
        """
        Saves ignore list!
        """
        
        # Determine if running as a script or as a frozen executable
        if getattr(sys, 'frozen', False):
            # Running as compiled
            script_directory = os.path.dirname(sys.executable)
        else:
            # Running as script
            script_directory = os.path.dirname(os.path.abspath(__file__))
        
        # Construct the full path for the ignore_list.txt
        file_path = os.path.join(script_directory, 'ignore_list.txt')

        with open(file_path, "w", encoding='utf-8') as f:
            for item in self.ignore_list:
                f.write(f"{item}\n")

    def load_ignore_list(self):
        """
        Loads ignore list!
        """
        
        # Determine if running as a script or as a frozen executable
        if getattr(sys, 'frozen', False):
            # Running as compiled
            script_directory = os.path.dirname(sys.executable)
        else:
            # Running as script
            script_directory = os.path.dirname(os.path.abspath(__file__))
        
        # Construct the full path for the ignore_list.txt
        file_path = os.path.join(script_directory, 'ignore_list.txt')

        if os.path.exists(file_path):
            with open(file_path, "r", encoding='utf-8') as f:
                self.ignore_list = [line.strip() for line in f.readlines()]

    def reload_ignore_list(self):
        self.ignore_list = []
        self.load_ignore_list()
        self.irc_client_gui.update_message_text(f"Ignore List reloaded C:<\r\n")
        for person in self.ignore_list:
            self.irc_client_gui.update_message_text(f"{person}\r\n")

    def save_channel_list_to_file(self):
        """
        Save the channel list data to a file.
        """
        
        # Determine if running as a script or as a frozen executable
        if getattr(sys, 'frozen', False):
            # Running as compiled
            script_directory = os.path.dirname(sys.executable)
        else:
            # Running as script
            script_directory = os.path.dirname(os.path.abspath(__file__))
        
        # Construct the full path for the channel_list.txt
        file_path = os.path.join(script_directory, 'channel_list.txt')

        with open(file_path, 'w', encoding='utf-8') as f:
            for channel in self.channel_list:
                f.write(f"Channel: {channel['name']}, Users: {channel['users']}, Topic: {channel['topic']}\n")
        
        # Clear the channel list after saving
        self.channel_list.clear()
        self.show_channel_list_flag = True

        if self.show_channel_list_flag:
            self.display_channel_list_window()

    def should_ignore(self, hostmask):
        """
        This should ignore by hostmask but it doesn't work yet.
        """
        for pattern in self.ignore_list:
            if fnmatch.fnmatch(hostmask.lower(), pattern.lower()):
                return True
        return False

    def strip_nick_prefix(self, nickname):
        # Strip '@' or '+' prefix from the nickname if present
        if nickname.startswith('@') or nickname.startswith('+'):
            return nickname[1:]
        return nickname

    def notify_channel_activity(self, channel):
        """
        Channel Activity notification - old
        """
        self.irc_client_gui.update_server_feedback_text(f'Activity in channel {channel}!\r')

    def friend_online(self, channel, username):
        """
        Friend list!
        """
        self.irc_client_gui.update_message_text(f"{channel}: {username} is Online!\r\n")

    def whois(self, target):
        """
        Who is this? Sends a whois request
        """
        self._send_message(f'WHOIS {target}')

    def display_channel_list_window(self):
        """
        Display the channel list window.
        """
        from list_window import ChannelListWindow
        
        # Determine if running as a script or as a frozen executable
        if getattr(sys, 'frozen', False):
            # Running as compiled
            script_directory = os.path.dirname(sys.executable)
        else:
            # Running as script
            script_directory = os.path.dirname(os.path.abspath(__file__))
        
        # Construct the full path for the channel_list.txt
        file_path = os.path.join(script_directory, 'channel_list.txt')

        # Check if the window is already open
        if self.channel_list_window and not self.channel_list_window.is_destroyed:
            # Bring the existing window to the front
            self.channel_list_window.lift()
        else:
            # Create a new window
            self.channel_list_window = ChannelListWindow(file_path)

    def start(self):
        while not self.exit_event.is_set():
            self.connect()
            self.receive_thread = threading.Thread(target=self.handle_incoming_message)
            self.receive_thread.daemon = True
            self.receive_thread.start()

            self.sender_thread = threading.Thread(target=self.process_send_queue)
            self.sender_thread.daemon = True
            self.sender_thread.start()

            self.stay_alive_thread = threading.Thread(target=self.keep_alive)
            self.stay_alive_thread.daemon = True
            self.stay_alive_thread.start()

            self.gui_handler()
            self.exit_event.set()

    def gui_handler(self):
        """
        Passes messages from the logic to the GUI.
        """
        while True:
            raw_message = self.message_queue.get()
