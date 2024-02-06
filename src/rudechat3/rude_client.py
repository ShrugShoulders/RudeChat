#!/usr/bin/env python
"""
GPL-3.0 License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from .list_window import ChannelListWindow
from .shared_imports import *

class RudeChatClient:
    def __init__(self, text_widget, server_text_widget, entry_widget, master, gui):
        self.master = master
        self.text_widget = text_widget
        self.entry_widget = entry_widget
        self.server_text_widget = server_text_widget
        self.joined_channels = []
        self.motd_lines = []
        self.chantypes = ''
        self.ignore_list = []
        self.current_channel = ''
        self.nickname = ''
        self.channel_messages = {}
        self.channel_users = {}
        self.user_modes = {}
        self.mode_to_symbol = {}
        self.whois_data = {}
        self.download_channel_list = {}
        self.highlighted_channels = {}
        self.highlighted_servers = {}
        self.whois_executed = set()
        self.decoder = irctokens.StatefulDecoder()
        self.encoder = irctokens.StatefulEncoder()
        self.gui = gui
        self.reader = None
        self.writer = None
        self.ping_start_time = None
        self.sasl_authenticated = False
        self.rate_limit_semaphore = asyncio.Semaphore(10)
        self.privmsg_rate_limit_semaphore = asyncio.Semaphore(2)
        self.ASCII_ART_MACROS = {}
        self.load_channel_messages()
        self.load_ignore_list()

    async def read_config(self, config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        self.server = config.get('IRC', 'server')
        self.port = config.getint('IRC', 'port')
        self.ssl_enabled = config.getboolean('IRC', 'ssl_enabled')
        self.nickname = config.get('IRC', 'nickname')

        # Add a new option for NickServ authentication
        self.use_nickserv_auth = config.getboolean('IRC', 'use_nickserv_auth', fallback=False)
        self.nickserv_password = config.get('IRC', 'nickserv_password') if self.use_nickserv_auth else None

        self.auto_join_channels = config.get('IRC', 'auto_join_channels').split(',')
        
        # Read new SASL-related fields
        self.sasl_enabled = config.getboolean('IRC', 'sasl_enabled', fallback=False)
        self.sasl_username = config.get('IRC', 'sasl_username', fallback=None)
        self.sasl_password = config.get('IRC', 'sasl_password', fallback=None)
        
        # Read server name from the config file
        self.server_name = config.get('IRC', 'server_name', fallback=None)
        self.gui.update_nick_channel_label()

    def load_channel_messages(self):
        script_directory = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_directory, 'channel_messages.json')
        try:
            with open(file_path, 'r') as file:
                self.channel_messages = json.load(file)
        except FileNotFoundError:
            # If the file doesn't exist, initialize an empty dictionary
            self.channel_messages = {}

    def save_channel_messages(self):
        script_directory = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_directory, 'channel_messages.json')
        with open(file_path, 'w') as file:
            json.dump(self.channel_messages, file, indent=2)

    async def connect(self, config_file):
        await self.connect_to_server(config_file)
        await self.send_initial_commands()
        await self.wait_for_welcome(config_file)

    async def connect_to_server(self, config_file):
        TIMEOUT = 256  # seconds
        self.gui.insert_text_widget(f'Connecting to server: {self.server}:{self.port}\n')
        self.gui.highlight_nickname()

        try:
            if self.ssl_enabled:
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                context.check_hostname = True
                context.verify_mode = ssl.CERT_REQUIRED
                self.reader, self.writer = await asyncio.wait_for(
                    asyncio.open_connection(self.server, self.port, ssl=context),
                    timeout=TIMEOUT
                )
            else:
                self.reader, self.writer = await asyncio.wait_for(
                    asyncio.open_connection(self.server, self.port),
                    timeout=TIMEOUT
                )
        except asyncio.TimeoutError:
            self.gui.insert_text_widget(f"Connection timeout. Please try again later.\n")
        except OSError as e:
            if e.winerror == 121:  # The semaphore error that I hate.
                self.gui.insert_text_widget("The semaphore timeout period has expired. Reconnecting...\n")
                success = await self.reconnect(config_file)
                if success:
                    self.gui.add_server_to_combo_box(self.server_name)
            else:
                self.gui.insert_text_widget(f"An unexpected error occurred: {str(e)}\n")

    async def send_initial_commands(self):
        self.gui.insert_text_widget(f'Sent client registration commands.\n')
        await self.send_message(f'NICK {self.nickname}')
        await self.send_message(f'USER {self.nickname} 0 * :{self.nickname}')
        
        # Start capability negotiation
        if self.sasl_enabled:
            self.gui.insert_text_widget("Beginning SASL Authentication\n")
            await self.send_message('CAP LS 302')
        else:
            self.gui.insert_text_widget("SASL is not enabled.\n")

    def handle_motd_line(self, tokens):
        motd_line = tokens.params[-1]  # Assumes the MOTD line is the last parameter
        self.motd_lines.append(motd_line)

    def handle_motd_start(self, tokens):
        self.motd_lines.clear()
        motd_start_line = tokens.params[-1]  # Assumes the introductory line is the last parameter
        self.motd_lines.append(motd_start_line)

    def handle_motd_end(self, tokens):
        # Combine the individual MOTD lines into a single string
        full_motd = "\n".join(self.motd_lines)
        # Display the full MOTD, cleaned up
        self.gui.insert_text_widget(f"Message of the Day:\n{full_motd}\n")
        # Clear the MOTD buffer for future use
        self.motd_lines.clear()
            
    async def wait_for_welcome(self, config_file):
        MAX_RETRIES = 5
        RETRY_DELAY = 5  # seconds
        retries = 0

        while retries < MAX_RETRIES:
            try:
                await self._await_welcome_message()
                return  # Successfully connected and received 001
            except (OSError, ConnectionError) as e:
                self.gui.insert_text_widget(f"Error occurred: {e}. Retrying in {RETRY_DELAY} seconds.\n")
                success = await self.reconnect(config_file)
                if success:
                    return  # Successfully reconnected
                retries += 1
                await asyncio.sleep(RETRY_DELAY)
        self.gui.insert_text_widget("Failed to reconnect after multiple attempts. Please check your connection.\n")

    def handle_connection_info(self, tokens):
        connection_info = tokens.params[-1]  # Assumes the connection info is the last parameter
        self.gui.insert_text_widget(f"Server Info: {connection_info}\n")

    def handle_global_users_info(self, tokens):
        global_users_info = tokens.params[-1]  # Assumes the global users info is the last parameter
        self.gui.insert_text_widget(f"Server Users Info: {global_users_info}\n")

    async def handle_nickname_conflict(self, tokens):
        new_nickname = self.nickname + str(random.randint(1, 99))
        await self.send_message(f'NICK {new_nickname}')
        self.nickname = new_nickname
        self.gui.insert_text_widget(f"Nickname already in use. Changed nickname to: {self.nickname}\n")

    async def initial_ping(self, tokens):
        ping_param = tokens.params[0]
        await self.send_message(f'PONG {ping_param}')

    async def automatic_join(self):
        for channel in self.auto_join_channels:
            await self.join_channel(channel)
            await asyncio.sleep(0.1)

    async def _await_welcome_message(self):
        self.gui.insert_text_widget(f'Waiting for welcome message from the server.\n')
        buffer = ""
        received_001 = False
        motd_received = False
        sasl_authenticated = False

        while True:
            data = await self.reader.read(4096)
            if not data:
                raise ConnectionError("Connection lost while waiting for the welcome message.")

            decoded_data = data.decode('UTF-8', errors='ignore')
            buffer += decoded_data
            while '\r\n' in buffer:
                line, buffer = buffer.split('\r\n', 1)
                tokens = irctokens.tokenise(line)

                match tokens.command:
                    case "CAP":
                        self.gui.insert_text_widget("Handling CAP message\n")
                        await self.handle_cap(tokens)

                    case "AUTHENTICATE":
                        self.gui.insert_text_widget("Handling AUTHENTICATE message\n")
                        await self.handle_sasl_auth(tokens)

                    case "903":
                        self.gui.insert_text_widget("Handling SASL successful message\n")
                        await self.handle_sasl_successful()
                        sasl_authenticated = True
                        await self.automatic_join()
                        return

                    case "904":
                        self.gui.insert_text_widget("Handling SASL failed message\n")
                        self.handle_sasl_failed()

                    case "001":
                        self.gui.insert_text_widget(f'Connected to the server: {self.server}:{self.port}\n')
                        received_001 = True
                        self.gui.insert_and_scroll()

                        if self.use_nickserv_auth and not self.sasl_enabled:
                            await self.send_message(f'PRIVMSG NickServ :IDENTIFY {self.nickname} {self.nickserv_password}\r\n')
                            self.gui.insert_text_widget(f"Sent NickServ authentication.\n")
                            motd_received = True
                        else:
                            motd_received = True

                    case "005":
                        self.handle_isupport(tokens)
                        self.gui.insert_and_scroll()

                    case "250":
                        self.handle_connection_info(tokens)

                    case "266":
                        self.handle_global_users_info(tokens)

                    case "433":
                        await self.handle_nickname_conflict(tokens)

                    case "372":
                        self.handle_motd_line(tokens)

                    case "375":
                        self.handle_motd_start(tokens)

                    case "376":
                        self.handle_motd_end(tokens)
                        if not self.use_nickserv_auth and not self.sasl_enabled:
                            motd_received = True
                            await self.automatic_join()
                            return

                    case "PING":
                        await self.initial_ping(tokens)

                    case "396":
                        if received_001 and motd_received and not self.sasl_enabled:
                            await self.automatic_join()
                            print("Joined channels after authentication.")
                            return

                    case _:
                        self.gui.insert_and_scroll()

    async def handle_cap(self, tokens):
        if not self.sasl_enabled:
            self.gui.insert_text_widget(f"SASL is not enabled.\n")
            return  # Skip SASL if it's not enabled
        if "LS" in tokens.params:
            await self.send_message("CAP REQ :sasl")
        elif "ACK" in tokens.params:
            await self.send_message("AUTHENTICATE PLAIN")

    async def handle_sasl_auth(self, tokens):
        if not self.sasl_enabled:
            self.gui.insert_text_widget(f"SASL is not enabled.\n")
            return  # Skip SASL if it's not enabled
        if tokens.params[0] == '+':
            auth_string = f"{self.sasl_username}\0{self.sasl_username}\0{self.sasl_password}"
            encoded_auth_string = base64.b64encode(auth_string.encode()).decode()
            await self.send_message(f"AUTHENTICATE {encoded_auth_string}")

    async def handle_sasl_successful(self):
        if not self.sasl_enabled:
            self.gui.insert_text_widget(f"SASL is not enabled.\n")
            return  # Skip SASL if it's not enabled
        self.gui.insert_text_widget(f"SASL authentication successful.\n")
        await self.send_message("CAP END")

    def handle_sasl_failed(self):
        if not self.sasl_enabled:
            self.gui.insert_text_widget(f"SASL is not enabled.\n")
            return
        self.gui.insert_text_widget(f"SASL authentication failed. Disconnecting.\n")

    async def send_message(self, message):
        try:
            self.writer.write(f'{message}\r\n'.encode('UTF-8'))
            await asyncio.wait_for(self.writer.drain(), timeout=10)
        except TimeoutError:
            print("Timeout while sending message.")

    def is_valid_channel(self, channel):
        return any(channel.startswith(prefix) for prefix in self.chantypes)

    async def join_channel(self, channel):
        if not self.is_valid_channel(channel):
            self.gui.insert_text_widget(f"Invalid channel name {channel}.\n")
            return

        if channel in self.joined_channels:
            self.gui.insert_text_widget(f"You are already in channel {channel}.\n")
            return

        await self.send_message(f'JOIN {channel}')
        self.joined_channels.append(channel)
        self.gui.channel_lists[self.server] = self.joined_channels  # Update the GUI channel list
        self.update_gui_channel_list()  # Update the channel list in GUI

    async def leave_channel(self, channel):
        await self.send_message(f'PART {channel}')
        if channel in self.joined_channels:
            self.joined_channels.remove(channel)
            
            # Remove the channel entry from the highlighted_channels dictionary
            if self.server_name in self.highlighted_channels:
                self.highlighted_channels[self.server_name].pop(channel, None)

            self.gui.channel_lists[self.server] = self.joined_channels
            self.update_gui_channel_list()

    def update_gui_channel_list(self):
        # Clear existing items
        self.gui.channel_listbox.delete(0, tk.END)

        for chan in self.joined_channels:
            self.gui.channel_listbox.insert(tk.END, chan)

        # Update and restore the highlighted background color for all previously highlighted channels
        updated_highlighted_channels = {}
        for channel, highlighted_info in self.highlighted_channels.get(self.server_name, {}).items():
            if highlighted_info is not None:
                old_index = highlighted_info.get('index')
                if old_index is not None:
                    # Find the new index in the current listbox
                    new_index = None
                    for idx in range(self.gui.channel_listbox.size()):
                        if self.gui.channel_listbox.get(idx) == channel:
                            new_index = idx
                            break

                    if new_index is not None:
                        # Update the index in the highlighted info
                        highlighted_info['index'] = new_index

                        # Set the background color directly based on the dictionary entry
                        bg_color = highlighted_info.get('bg', 'red')
                        self.gui.channel_listbox.itemconfig(new_index, {'bg': bg_color})

                        # Update the dictionary with the new index
                        updated_highlighted_channels[channel] = highlighted_info

        # Update the highlighted_channels dictionary with the new indexes
        self.highlighted_channels[self.server_name] = updated_highlighted_channels

    def update_gui_user_list(self, channel):
        self.gui.user_listbox.delete(0, tk.END)
        for user in self.channel_users.get(channel, []):
            self.gui.user_listbox.insert(tk.END, user)

    async def reset_state(self):
        await self.gui.remove_server_from_dropdown(self.server_name)
        self.joined_channels.clear()
        self.motd_lines.clear()
        self.channel_messages.clear()
        self.channel_users.clear()
        self.user_modes.clear()
        self.mode_to_symbol.clear()
        self.whois_data.clear()
        self.download_channel_list.clear()
        self.whois_executed.clear()

    async def reconnect(self, config_file):
        MAX_RETRIES = 5
        RETRY_DELAY = 5
        retries = 0
        while retries < MAX_RETRIES:
            try:
                # Reset client state before attempting to reconnect
                await self.disconnect()
                
                # Initialize the client with the specified config file
                await self.gui.init_client_with_config(config_file, self.server_name)
                
                # Add server to combo box if reconnection is successful
                if self.gui:
                    self.gui.irc_client = self
                    self.gui.add_server_to_combo_box(self.server_name)
                
                if hasattr(self.gui, 'insert_text_widget'):  
                    self.gui.insert_text_widget(f'Successfully reconnected.\n')
                else:
                    print(f"GUI object not set")
                return True  # Successfully reconnected
            except Exception as e:
                retries += 1
                print(f'Failed to reconnect ({retries}/{MAX_RETRIES}): {e}. Retrying in {RETRY_DELAY} seconds.\n')
                await asyncio.sleep(RETRY_DELAY)
        return False

    async def keep_alive(self):
        while True:
            try:
                # Measure ping time before sending PING
                self.ping_start_time = time.time()

                await asyncio.sleep(194)
                await self.send_message(f'PING {self.server}')

            except (ConnectionResetError, OSError) as e:
                print(f"Exception caught in keep_alive: {e}")

    async def handle_server_message(self, line):
        self.gui.insert_server_widget(line + "\n")

    async def handle_notice_message(self, tokens):
        sender = tokens.hostmask if tokens.hostmask else "Server"
        target = tokens.params[0]
        message = tokens.params[1]
        self.gui.insert_server_widget(f"NOTICE {sender} {target}: {message}\n")

    async def handle_ctcp(self, tokens):
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
        sender = tokens.hostmask.nickname
        target = tokens.params[0]
        message = tokens.params[1]

        # Detect if this is a CTCP message
        if message.startswith('\x01') and message.endswith('\x01'):
            ctcp_command = message[1:-1].split(' ', 1)[0]  # Extract the CTCP command
            ctcp_content = message[1:-1].split(' ', 1)[1] if ' ' in message else None  # Extract the content if present

            match ctcp_command:
                case "VERSION":
                    if tokens.command == "PRIVMSG":
                        await self.send_message(f'NOTICE {sender} :\x01VERSION RudeChat3.0.4\x01')
                        self.gui.insert_server_widget(f"CTCP: {sender} {target}: {ctcp_command}\n")
                case "MOO":
                    if tokens.command == "PRIVMSG":
                        await self.send_message(f'NOTICE {sender} :\x01MoooOOO! Hi Cow!! RudeChat3.0.4\x01')
                        self.gui.insert_server_widget(f"CTCP: {sender} {target}: {ctcp_command}\n")
                case "PING":
                    if tokens.command == "PRIVMSG":
                        timestamp = str(int(time.time()))  # Get the current Unix timestamp
                        await self.send_message(f'NOTICE {sender} :\x01PING {ctcp_content} {timestamp}\x01')
                        self.gui.insert_server_widget(f"CTCP: {sender} {target}: {ctcp_command}\n")
                case "FINGER":
                    if tokens.command == "PRIVMSG":
                        await self.send_message(f'NOTICE {sender} :\x01FINGER: {self.nickname} {self.server_name} RudeChat3.0.4\x01')
                        self.gui.insert_server_widget(f"CTCP: {sender} {target}: {ctcp_command}\n")
                case "CLIENTINFO":
                    if tokens.command == "PRIVMSG":
                        await self.send_message(f'NOTICE {sender} :\x01CLIENTINFO VERSION TIME PING FINGER\x01')
                        self.gui.insert_server_widget(f"CTCP: {sender} {target}: {ctcp_command}\n")
                case "TIME":
                    if tokens.command == "PRIVMSG":
                        import pytz
                        dublin_tz = pytz.timezone('Europe/Dublin')
                        dublin_time = datetime.datetime.now(dublin_tz).strftime("%Y-%m-%d %H:%M:%S")
                        time_reply = "\x01TIME " + dublin_time + "\x01"
                        await self.send_message(f'NOTICE {sender} :{time_reply}')
                        self.gui.insert_server_widget(f"CTCP: {sender} {target}: {ctcp_command}\n")
                case "ACTION":
                    await self.handle_action_ctcp(timestamp, sender, target, ctcp_content)
                case _:
                    print(f"Unhandled CTCP command: {ctcp_command}")

    async def handle_action_ctcp(self, timestamp, sender, target, ctcp_content):
        action_message = f"{timestamp}* {sender} {ctcp_content}\n"

        # Update the message history
        if target not in self.channel_messages:
            self.channel_messages[target] = []

        self.channel_messages[target].append(action_message)

        # Trim the messages list
        self.trim_messages(target, server_name=None)

        # Display the message in the text_widget if the target matches the current channel or DM
        if target == self.current_channel and self.gui.irc_client == self:
            self.gui.insert_text_widget(action_message)
            self.gui.highlight_nickname()
        else:
            # If it's not the currently viewed channel, highlight the channel in green in the Listbox
            for idx in range(self.gui.channel_listbox.size()):
                if self.gui.channel_listbox.get(idx) == target:
                    current_bg = self.gui.channel_listbox.itemcget(idx, 'bg')
                    if current_bg != 'red':
                        self.gui.channel_listbox.itemconfig(idx, {'bg':'green'})
                    break

    def trim_messages(self, target, server_name=None):
        # Trim all entries in channel_messages to 100 lines
        for channel in self.channel_messages:
            entry = self.channel_messages[channel]
            if isinstance(entry, list):
                self.channel_messages[channel] = entry[-100:]
            elif server_name is not None and server_name in entry:
                for server_channel in entry[server_name]:
                    entry[server_name][server_channel] = entry[server_name][server_channel][-100:]

    async def notify_user_of_mention(self, server, channel):
        notification_msg = f"Mention on {server} in {channel}"

        # Check if the mentioned channel is currently selected
        selected_channel = self.current_channel
        is_channel_selected = selected_channel == channel

        # Highlight the mentioned channel in the channel_listbox if it's not selected
        if not is_channel_selected:
            self.highlight_channel(channel)

        # Highlight the server in the server_listbox if it's not selected
        self.highlight_server()

        # Play the beep sound/notification
        await self.trigger_beep_notification(channel_name=channel, message_content=notification_msg)

    def highlight_channel(self, channel):
        if self.server_name not in self.highlighted_channels:
            self.highlighted_channels[self.server_name] = {}

        for idx in range(self.gui.channel_listbox.size()):
            if self.gui.channel_listbox.get(idx) == channel:
                self.gui.channel_listbox.itemconfig(idx, {'bg': 'red'})
                # Store the highlighted channel information for the server
                self.highlighted_channels[self.server_name][channel] = {'index': idx, 'bg': 'red'}
                break

    def highlight_server(self):
        for idx in range(self.gui.server_listbox.size()):
            if self.gui.server_listbox.get(idx) == self.server_name:
                self.gui.server_listbox.itemconfig(idx, {'bg': 'red'})
                # Store the highlighted server information with red background
                self.highlighted_servers[self.server_name] = {'index': idx, 'bg': 'red'}
                break

    async def trigger_beep_notification(self, channel_name=None, message_content=None):
        """
        You've been pinged! Plays a beep or noise on mention.
        """
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
            self.gui.trigger_desktop_notification(channel_name, message_content=message_content)
        except Exception as e:
            print(f"Error triggering desktop notification: {e}")

    async def handle_privmsg(self, tokens):
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
        sender = tokens.hostmask.nickname
        target = tokens.params[0]
        message = tokens.params[1]

        sender_hostmask = str(tokens.hostmask)
        if self.should_ignore_sender(sender_hostmask):
            return

        await self.notify_user_if_mentioned(message, target)
        if self.is_ctcp_command(message):
            await self.handle_ctcp(tokens)
            return

        if self.is_direct_message(target):
            target = await self.get_direct_message_target(sender, target)
            await self.prepare_direct_message(sender, target, message, timestamp)
        else:
            await self.handle_channel_message(sender, target, message, timestamp)

    def should_ignore_sender(self, sender_hostmask):
        return any(fnmatch.fnmatch(sender_hostmask, ignored) for ignored in self.ignore_list)

    async def notify_user_if_mentioned(self, message, target):
        if self.nickname in message:
            await self.notify_user_of_mention(self.server, target)

    def is_ctcp_command(self, message):
        return message.startswith('\x01') and message.endswith('\x01')

    def is_direct_message(self, target):
        return target == self.nickname

    async def get_direct_message_target(self, sender, target):
        if sender not in self.whois_executed:
            await self.send_message(f'WHOIS {sender}')
            self.whois_executed.add(sender)
        return target

    async def prepare_direct_message(self, sender, target, message, timestamp):
        if self.server not in self.channel_messages:
            self.channel_messages[self.server] = {}
        if sender not in self.channel_messages[self.server]:
            self.channel_messages[self.server][sender] = []

        if self.is_direct_message(target) and sender not in self.joined_channels:
            self.joined_channels.append(sender)
            self.gui.channel_lists[self.server] = self.joined_channels
            self.update_gui_channel_list()

        self.save_message(self.server_name, target, sender, message, is_sent=False)
        self.log_message(self.server_name, target, sender, message, is_sent=False)
        self.display_message(timestamp, sender, message, target)

    async def handle_channel_message(self, sender, target, message, timestamp):
        if target not in self.channel_messages:
            self.channel_messages[target] = []
        self.save_message(self.server_name, target, sender, message, is_sent=False)
        self.log_message(self.server_name, target, sender, message, is_sent=False)
        self.display_message(timestamp, sender, message, target)

    def save_message(self, server, target, sender, message, is_sent):
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
        if is_sent:
            self.sent_messages.append((timestamp, sender, target, message))
        else:
            if self.is_direct_message(target):
                message_list = self.channel_messages[self.server][sender]
            else:
                message_list = self.channel_messages[target]
            message_list.append(f"{timestamp}<{sender}> {message}\n")
            if len(message_list) > 100:
                message_list = message_list[-100:]

    def display_message(self, timestamp, sender, message, target):
        if target == self.current_channel and self.gui.irc_client == self:
            self.gui.insert_text_widget(f"{timestamp}<{sender}> {message}\n")
            self.gui.highlight_nickname()
        else:
            self.highlight_channel_if_not_current(target, sender)

    def highlight_channel_if_not_current(self, target, sender):
        highlighted_channel = target
        if self.is_direct_message(target):
            highlighted_channel = sender

        for idx in range(self.gui.channel_listbox.size()):
            if self.gui.channel_listbox.get(idx) == highlighted_channel:
                current_bg = self.gui.channel_listbox.itemcget(idx, 'bg')
                if current_bg != 'red':
                    self.gui.channel_listbox.itemconfig(idx, {'bg': 'green'})
                    self.save_highlight(highlighted_channel, idx, bg='green')
                break

    def save_highlight(self, channel, index, bg='green'):
        if self.server_name not in self.highlighted_channels:
            self.highlighted_channels[self.server_name] = {}

        # Store the highlighted channel information for the server
        self.highlighted_channels[self.server_name][channel] = {'index': index, 'bg': bg}

    async def handle_join(self, tokens):
        user_info = tokens.hostmask.nickname
        channel = tokens.params[0]
        join_message = f"<&> {user_info} has joined channel {channel}\n"

        # Update the message history for the channel
        if channel not in self.channel_messages:
            self.channel_messages[channel] = []

        self.channel_messages[channel].append(join_message)

        self.trim_messages(channel, server_name=None)

        # Display the message in the text_widget only if the channel matches the current channel
        if channel == self.current_channel and self.gui.irc_client == self:
            self.gui.insert_text_widget(join_message)
            self.gui.highlight_nickname()

        # If the user joining is the client's user, just return
        if user_info == self.nickname:
            return

        # Check if the user is not already in the channel_users list for the channel
        if user_info not in self.channel_users.get(channel, []):
            # Add the user to the channel_users list
            self.channel_users.setdefault(channel, []).append(user_info)
        else:
            already_in_message = f"{user_info} is already in the user list for channel {channel}\n"
            if channel == self.current_channel and self.gui.irc_client == self:
                self.gui.insert_text_widget(already_in_message)

        # Sort the user list for the channel
        sorted_users = self.sort_users(self.channel_users[channel], channel)

        # Update the user listbox for the channel with sorted users
        self.update_user_listbox(channel)

    async def handle_part(self, tokens):
        user_info = tokens.hostmask.nickname
        channel = tokens.params[0]
        part_message = f"<X> {user_info} has parted from channel {channel}\n"

        # Update the message history for the channel
        if channel not in self.channel_messages:
            self.channel_messages[channel] = []

        self.channel_messages[channel].append(part_message)

        # Trim the messages list if it exceeds 100 lines
        self.trim_messages(channel, server_name=None)

        # Display the message in the text_widget only if the channel matches the current channel
        if channel == self.current_channel and self.gui.irc_client == self:
            self.gui.insert_text_widget(part_message)
            self.gui.highlight_nickname()

        # Check if the user is in the channel_users list for the channel
        user_found = False
        for user_with_symbol in self.channel_users.get(channel, []):
            # Check if the stripped user matches user_info
            if user_with_symbol.lstrip('@+%') == user_info:
                user_found = True
                self.channel_users[channel].remove(user_with_symbol)
                break

        if user_found:
            # Update the user listbox for the channel
            self.update_user_listbox(channel)
        else:
            print(f"{user_info} User not found.")
            pass

    async def handle_quit(self, tokens):
        user_info = tokens.hostmask.nickname
        reason = tokens.params[0] if tokens.params else "No reason"
        quit_message = f"<X> {user_info} has quit: {reason}\n"

        # Remove the user from all channel_users lists
        for channel, users in self.channel_users.items():
            user_found = False
            for idx, user_with_symbol in enumerate(users):
                # Check if the stripped user matches user_info
                if user_with_symbol.lstrip('@+%') == user_info:
                    user_found = True
                    del self.channel_users[channel][idx]
                    
                    # Update the message history for the channel
                    if channel not in self.channel_messages:
                        self.channel_messages[channel] = []

                    self.channel_messages[channel].append(quit_message)

                    # Trim the messages list if it exceeds 100 lines
                    self.trim_messages(channel, server_name=None)

                    # Display the message in the text_widget only if the channel matches the current channel
                    if channel == self.current_channel and self.gui.irc_client == self:
                        self.gui.insert_text_widget(quit_message)
                        self.gui.highlight_nickname()

                    break

            if user_found:
                # Update the user listbox for the channel
                self.update_user_listbox(channel)

    async def handle_nick(self, tokens):
        old_nick = tokens.hostmask.nickname
        new_nick = tokens.params[0]

        # Update the user's nick in all channel_users lists they are part of
        for channel, users in self.channel_users.items():
            for idx, user_with_symbol in enumerate(users):
                # Check if the stripped user matches old_nick
                if user_with_symbol.lstrip('@+%') == old_nick:
                    # Extract the mode symbols from the old nickname
                    mode_symbols = ''.join([c for c in user_with_symbol if c in '@+%'])
                    
                    # Replace old_nick with new_nick, retaining the mode symbols
                    users[idx] = mode_symbols + new_nick
                    
                    # Update the user listbox for the channel if necessary
                    self.update_user_listbox(channel)

                    # Display the nick change message in the channel
                    if channel not in self.channel_messages:
                        self.channel_messages[channel] = []
                    self.channel_messages[channel].append(f"<@> {old_nick} has changed their nickname to {new_nick}\n")

                    # Trim the messages list if it exceeds 100 lines
                    self.trim_messages(channel, server_name=None)
                    
                    # Insert message into the text widget only if this is the current channel
                    if channel == self.current_channel and self.gui.irc_client == self:
                        self.gui.insert_text_widget(f"<@> {old_nick} has changed their nickname to {new_nick}\n")
                        self.gui.highlight_nickname()

                    break

        # If the old nickname is the same as the client's current nickname, update the client state
        if old_nick == self.nickname:
            await self.change_nickname(new_nick, is_from_token=True)

    def sort_users(self, users, channel):
        sorted_users = []
        current_modes = self.user_modes.get(channel, {})

        raw_users = []
        for user_with_possible_mode in users:
            detected_modes = set()
            for mode, symbol in self.mode_to_symbol.items():
                if user_with_possible_mode.startswith(symbol):
                    detected_modes.add(mode)
                    user_with_possible_mode = user_with_possible_mode[len(symbol):]

            # Update the user's modes in the current_modes dictionary
            if detected_modes:
                if user_with_possible_mode in current_modes:
                    current_modes[user_with_possible_mode].update(detected_modes)
                else:
                    current_modes[user_with_possible_mode] = detected_modes

            raw_users.append(user_with_possible_mode)

        # Now, for each raw user, apply the highest-priority mode
        mode_priority = list(self.mode_to_symbol.keys())
        for user in raw_users:
            modes = current_modes.get(user, set())

            # Pick the highest priority mode for the user
            chosen_mode = None
            for priority_mode in mode_priority:
                if priority_mode in modes:
                    chosen_mode = priority_mode
                    break

            mode_symbol = self.mode_to_symbol.get(chosen_mode, "")
            sorted_users.append(f"{mode_symbol}{user}")

        # Sort the user list based on the mode symbols
        sorted_users = sorted(
            sorted_users,
            key=lambda x: (mode_priority.index(next((m for m, s in self.mode_to_symbol.items() if s == x[0]), None)) if x[0] in self.mode_to_symbol.values() else len(mode_priority), x)
        )

        # Update the user modes dictionary and the channel_users list
        self.user_modes[channel] = current_modes
        self.channel_users[channel] = sorted_users
        return sorted_users

    async def handle_mode(self, tokens):
        channel = tokens.params[0]
        mode_change = tokens.params[1]
        user = tokens.params[2] if len(tokens.params) > 2 else None

        # Ignore ban and unban and quiet modes
        ignored_modes = ['+b', '-b', '-q', '+q']
        if mode_change in ignored_modes:
            message = f"<!> {mode_change} mode for {user if user else 'unknown'}\n"
            if channel == self.current_channel:
                self.gui.insert_text_widget(f"{message}")
                self.gui.highlight_nickname()

            # Update the message history for the channel
            if channel not in self.channel_messages:
                self.channel_messages[channel] = []
            self.channel_messages[channel].append(message)

            return

        if channel in self.joined_channels and user:
            current_modes = self.user_modes.get(channel, {})

            # Handle addition of modes
            if mode_change.startswith('+'):
                mode = mode_change[1]
                current_modes.setdefault(user, set()).add(mode)
                
                # Show message and save to history
                message = f"<+> {user} has been given mode +{mode}\n"
                if channel == self.current_channel and self.gui.irc_client == self:
                    self.gui.insert_text_widget(f"{message}")
                    self.gui.highlight_nickname()

                # Update the message history for the channel
                if channel not in self.channel_messages:
                    self.channel_messages[channel] = []

                self.channel_messages[channel].append(message)

                # Trim the messages list if it exceeds 100 lines
                self.trim_messages(channel, server_name=None)

            # Handle removal of modes
            elif mode_change.startswith('-'):
                mode = mode_change[1]
                if mode in self.mode_to_symbol:  # <-- Check here
                    symbol_to_remove = self.mode_to_symbol[mode]
                    self.channel_users[channel] = [
                        u.replace(symbol_to_remove, '') if u.endswith(user) else u
                        for u in self.channel_users.get(channel, [])
                    ]
                else:
                    print(f"Unknown mode: {mode}")

                user_modes = current_modes.get(user, set())
                user_modes.discard(mode)

                # Show message and save to history
                message = f"<-> {user} has had mode +{mode} removed\n"
                if channel == self.current_channel and self.gui.irc_client == self:
                    self.gui.insert_text_widget(f"{message}")
                    self.gui.highlight_nickname()

                # Update the message history for the channel
                if channel not in self.channel_messages:
                    self.channel_messages[channel] = []

                self.channel_messages[channel].append(message)

                # Trim the messages list if it exceeds 100 lines
                self.trim_messages(channel, server_name=None)

                if not user_modes:
                    if user in current_modes:
                        del current_modes[user]  # Remove the user's entry if no modes left
                    else:
                        print(f"User {user} not found in current modes. Adding with no modes.")
                        user_modes = set()

                        # Check for special characters in the user's nickname and add corresponding modes
                        if '@' in user:
                            user_modes.add('o')  # Add the '@' mode
                        if '+' in user:
                            user_modes.add('v')  # Add the '+' mode

                        current_modes[user] = user_modes  # Add the user with an empty set of modes
                else:
                    current_modes[user] = user_modes  # Update the user's modes

            self.user_modes[channel] = current_modes

            # Update the user list to reflect the new modes
            sorted_users = self.sort_users(self.channel_users.get(channel, []), channel)
            self.channel_users[channel] = sorted_users

            self.update_user_listbox(channel)

    def update_user_listbox(self, channel):
        current_users = self.channel_users.get(channel, [])
        sorted_users = self.sort_users(current_users, channel)
        
        # Only update the user listbox if the channel is the currently selected channel
        if channel == self.current_channel and self.gui.irc_client == self:
            # Update the Tkinter Listbox to reflect the current users in the channel
            self.gui.user_listbox.delete(0, tk.END)  # Clear existing items
            for user in sorted_users:
                self.gui.user_listbox.insert(tk.END, user)
                       
    def handle_isupport(self, tokens):
        params = tokens.params[:-1]  # Exclude the trailing "are supported by this server" message
        isupport_message = " ".join(params)
        self.gui.insert_server_widget(f"ISUPPORT: {isupport_message}\n")

        # Parse PREFIX for mode-to-symbol mapping
        for param in params:
            if param.startswith("PREFIX="):
                _, mappings = param.split("=")
                modes, symbols = mappings[1:].split(")")
                self.mode_to_symbol = dict(zip(modes, symbols))
            elif param.startswith("CHANTYPES="):
                _, channel_types = param.split("=")
                self.chantypes = channel_types

    async def handle_who_reply(self, tokens):
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
                message = f"User {details['nickname']} ({details['username']}@{details['host']}) on {details['server']} in {details['channel']}\n"
                messages.append(message)
            final_message = "\n".join(messages)
            self.gui.insert_text_widget(final_message)
            # Reset the who_details for future use
            self.who_details = []

    async def handle_whois_replies(self, command, tokens):
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

            elif command == "330":
                logged_in_as = tokens.params[2]
                if nickname not in self.whois_data:
                    self.whois_data[nickname] = {}
                self.whois_data[nickname]["Logged In As"] = logged_in_as

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

                    self.gui.insert_text_widget(whois_response)
                    await self.save_whois_to_file(nickname)

    async def save_whois_to_file(self, nickname):
        """Save WHOIS data for a given nickname to a file."""
        script_directory = os.path.dirname(os.path.abspath(__file__))
        
        # Construct the full path for the WHOIS directory
        whois_directory = os.path.join(script_directory, 'whois')
        
        # Create the WHOIS directory if it doesn't exist
        os.makedirs(whois_directory, exist_ok=True)

        # Construct the full path for the whois file inside the WHOIS directory
        filename = os.path.join(whois_directory, f'whois_{nickname}.txt')
        
        with open(filename, 'w', encoding='utf-8') as file:
            for key, value in self.whois_data[nickname].items():
                file.write(f"{key}: {value}\n")

            # Generate and append the /ignore suggestion
            ignore_suggestion = f"*!{self.whois_data[nickname]['Username']}@{self.whois_data[nickname]['Hostname']}"
            file.write(f"\nSuggested /ignore mask: {ignore_suggestion}\n")

    def handle_time_request(self, tokens):
        """
        Handle the server's response for the TIME command.
        """
        server_name = tokens.params[0]  # The server's name
        local_time = tokens.params[1]   # The local time on the server

        message = f"Server Time from {server_name}: {local_time}"
        self.gui.insert_text_widget(message)

    async def handle_kick_event(self, tokens):
        """
        Handle the KICK event from the server.
        """
        channel = tokens.params[0]
        kicked_nickname = tokens.params[1]
        reason = tokens.params[2] if len(tokens.params) > 2 else 'No reason provided'

        # Update the message history for the channel
        if channel not in self.channel_messages:
            self.channel_messages[channel] = []

        # Display the kick message in the chat window only if the channel is the current channel
        kick_message_content = f"<X> {kicked_nickname} has been kicked from {channel} by {tokens.hostmask.nickname} ({reason})"
        self.channel_messages[channel].append(kick_message_content + "\n")

        # Trim the messages list if it exceeds 100 lines
        self.trim_messages(channel, server_name=None)

        if channel == self.current_channel and self.gui.irc_client == self:
            self.gui.insert_text_widget(kick_message_content + "\n")
            self.gui.highlight_nickname()

        # Remove the user from the channel_users list for the channel
        user_found = False
        for user_with_symbol in self.channel_users.get(channel, []):
            # Check if the stripped user matches kicked_nickname
            if user_with_symbol.lstrip('@+%') == kicked_nickname:
                user_found = True
                self.channel_users[channel].remove(user_with_symbol)
                break

        if user_found:
            # Update the user listbox for the channel
            self.update_user_listbox(channel)

    async def handle_list_response(self, tokens):
        channel_name = tokens.params[1]
        user_count = tokens.params[2]
        topic = tokens.params[3]
        # Add the channel information to a dictionary or list (to be implemented)
        self.download_channel_list[channel_name] = {
            'user_count': user_count,
            'topic': topic
        }

    def show_channel_list_window(self):
        self.channel_window = ChannelListWindow(self, self.master)

    async def save_channel_list_to_file(self):
        with open("channel_list.txt", "w", encoding='utf-8') as f:
            for channel, info in self.download_channel_list.items():
                f.write(f"{channel} - Users: {info['user_count']} - Topic: {info['topic']}\n")

    def handle_names_list(self, tokens):
        self.current_channel = tokens.params[2]
        users = tokens.params[3].split(" ")

        # If this channel isn't in channel_users, initialize it with an empty list
        if self.current_channel not in self.channel_users:
            self.channel_users[self.current_channel] = []

        # Append the users to the channel's list only if they are not already in it
        for user in users:
            if user not in self.channel_users[self.current_channel]:
                self.channel_users[self.current_channel].append(user)

    def handle_end_of_names_list(self):
        if self.current_channel:
            # Sort the entire list of users for the channel
            sorted_users = self.sort_users(self.channel_users[self.current_channel], self.current_channel)
            self.channel_users[self.current_channel] = sorted_users
            self.update_user_listbox(self.current_channel)  # Pass current_channel here
            self.current_channel = ""

    def handle_pong(self, tokens):
        pong_server = tokens.params[-1]  # Assumes the server name is the last parameter
        current_time = time.time()

        if self.ping_start_time is not None:
            ping_time = current_time - self.ping_start_time
            ping_time_formatted = "{:.3f}".format(ping_time).lstrip('0') + " s"
            self.gui.update_ping_label(ping_time_formatted)

        self.ping_start_time = None

    def handle_372(self, tokens):
        motd_line = tokens.params[-1]
        self.motd_lines.append(motd_line)

    def handle_376(self, tokens):
        full_motd = "\n".join(self.motd_lines)
        self.gui.insert_text_widget(f"Message of the Day:\n{full_motd}\n")
        self.motd_lines.clear()

    def handle_900(self, tokens):
        logged_in_as = tokens.params[3]
        self.gui.insert_server_widget(f"Successfully authenticated as: {logged_in_as}\n")

    def handle_396(self, tokens):
        hidden_host = tokens.params[1]
        reason = tokens.params[2]
        self.gui.insert_server_widget(f"Your host is now hidden as: {hidden_host}. Reason: {reason}\n")

    def handle_error(self, tokens):
        error_message = ' '.join(tokens.params) if tokens.params else 'Unknown error'
        self.gui.insert_text_widget(f"ERROR: {error_message}\n")

    def handle_topic(self, tokens):
        channel_name = tokens.params[1]
        command = tokens.command

        if command == "332":
            # RPL_TOPIC (numeric 332) - Topic for the channel is being sent
            topic = tokens.params[2]
            # Check if the server entry exists in the dictionary
            if self.server not in self.gui.channel_topics:
                self.gui.channel_topics[self.server] = {}
            # Set the topic for the channel under the server entry
            self.gui.channel_topics[self.server][channel_name] = topic
            self.gui.current_topic.set(f"{topic}")

        elif command == "333":
            # RPL_TOPICWHOTIME (numeric 333) - Who set the topic and when
            who_set = tokens.params[2]

        elif command == "TOPIC":
            # TOPIC command is received indicating a change in topic
            channel_name = tokens.params[0]
            topic = tokens.params[1]
            # Check if the server entry exists in the dictionary
            if self.server not in self.gui.channel_topics:
                self.gui.channel_topics[self.server] = {}
            # Set the topic for the channel under the server entry
            self.gui.channel_topics[self.server][channel_name] = topic
            self.gui.current_topic.set(f"{topic}")

    def handle_nickname_doesnt_exist(self, tokens):
        """
        Handle the "401" response, which indicates that a given nickname doesn't exist on the server.
        """
        if len(tokens.params) >= 2:
            # Extract the nickname from the second element of the list
            nickname = tokens.params[1]
            
            self.gui.insert_text_widget(f"The nickname '{nickname}' doesn't exist on the server.\n")
        else:
            print("Invalid response format for '401'.")

    async def handle_incoming_message(self, config_file):
        buffer = ""
        current_users_list = []
        current_channel = ""
        timeout_seconds = 256  # seconds

        while True:
            try:
                async with self.rate_limit_semaphore:
                    data = await asyncio.wait_for(self.reader.read(4096), timeout_seconds)
            except asyncio.TimeoutError:
                self.gui.insert_text_widget("Read operation timed out!\n")
                continue
            except OSError as e:
                if e.winerror == 121:  # I hate this WinError >:C
                    self.gui.insert_text_widget(f"WinError: {e}\n")
                    await self.reconnect(config_file)
                else:
                    self.gui.insert_text_widget(f"Unhandled OSError: {e}\n")
                    continue
            except Exception as e:  # General exception catch
                self.gui.insert_text_widget(f"An unexpected error occurred: {e}\n")
                continue

            if not data:
                break

            decoded_data = data.decode('UTF-8', errors='ignore')
            cleaned_data = decoded_data.replace("\x06", "")  # Remove the character with ASCII value 6
            buffer += cleaned_data

            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                try:
                    # Check for an empty line or line with only whitespace before attempting to tokenize
                    if len(line.strip()) == 0:
                        #print(f"Debug: Received an empty or whitespace-only line: '{line}'\n")
                        continue

                    # Additional check: Ensure that the line has at least one character
                    if len(line) < 1:
                        #print(f"Debug: Received a too-short line: '{line}'\n")
                        continue

                    # Debug statement to print the line before tokenizing
                    #print(f"Debug: About to tokenize the line - '{line}'")

                    tokens = irctokens.tokenise(line)
                except ValueError as e:
                    self.gui.insert_text_widget(f"Error: {e}\n")
                    continue
                except IndexError as ie:
                    self.gui.insert_text_widget(f"IndexError: {ie}. Line: '{line}'\n")
                    continue

                match tokens.command:
                    case "ERROR":
                        self.handle_error(tokens)
                    case "353":  # NAMES list
                        self.handle_names_list(tokens)
                                
                    case "366":  # End of NAMES list
                        self.handle_end_of_names_list()

                    case "372":
                        self.handle_372(tokens)
                    case "376":
                        self.handle_376(tokens)
                    case "900":
                        self.handle_900(tokens)
                    case "396":
                        self.handle_396(tokens)

                    case "305":
                        message = "You are no longer marked as being away"
                        self.gui.insert_text_widget(f"{message}\n")

                    case "306":
                        message = "You have been marked as being away"
                        self.gui.insert_text_widget(f"{message}\n")

                    case "391":
                        self.handle_time_request(tokens)

                    case "352" | "315":
                        await self.handle_who_reply(tokens)

                    case "311" | "312" | "313" | "317" | "319" | "301" | "671" | "338" | "318" | "330":
                        await self.handle_whois_replies(tokens.command, tokens)

                    case "332" | "333" | "TOPIC":
                        self.handle_topic(tokens)

                    case "324":
                        self.handle_mode_info(tokens)

                    case "329":
                        self.handle_creation_time(tokens)

                    case "328":
                        self.handle_328(tokens)

                    case "367":  
                        self.handle_banlist(tokens)
                            
                    case "368":  
                        self.handle_endofbanlist(tokens)

                    case "401":
                        self.handle_nickname_doesnt_exist(tokens)

                    case "442":
                        self.handle_not_on_channel(tokens)

                    case "443":
                        self.handle_already_on_channel(tokens)

                    case "472":
                        self.handle_unknown_mode(tokens)

                    case "473" | "475" | "474" | "471":
                        channel = tokens.params[1]
                        reason = tokens.params[2] if len(tokens.params) > 2 else ""

                        # Combine information into one message
                        message = f"Cannot join channel {channel} - {reason}"
                        self.gui.insert_text_widget(f"{message}\n")

                    case "477":
                        await self.handle_cannot_join_channel(tokens)

                    case "482":
                        self.handle_not_channel_operator(tokens)

                    case "322":  # Channel list
                        await self.handle_list_response(tokens)
                        await self.channel_window.update_channel_info(tokens.params[1], tokens.params[2], tokens.params[3])
                    case "323":  # End of channel list
                        await self.save_channel_list_to_file()

                    case "KICK":
                        await self.handle_kick_event(tokens)
                    case "NOTICE":
                        await self.handle_notice_message(tokens)
                    case "PRIVMSG":
                        async with self.privmsg_rate_limit_semaphore:
                            await self.handle_privmsg(tokens)
                    case "JOIN":
                        await self.handle_join(tokens)
                    case "PART":
                        await self.handle_part(tokens)
                    case "QUIT":
                        await self.handle_quit(tokens)
                    case "NICK":
                        await self.handle_nick(tokens)
                    case "MODE":
                        await self.handle_mode(tokens)
                    case "PING":
                        ping_param = tokens.params[0]
                        await self.send_message(f'PONG {ping_param}')
                    case "PONG":
                        self.handle_pong(tokens)
                    case _:
                        print(f"Debug: Unhandled command {tokens.command}. Full line: {line}")
                        if line.startswith(f":{self.server}"):
                            await self.handle_server_message(line)

    def handle_already_on_channel(self, tokens):
        channel = tokens.params[2]
        message = tokens.params[3]
        self.gui.insert_server_widget(f"{channel}: {message}\n")

    def handle_not_on_channel(self, tokens):
        channel = tokens.params[1]
        message = tokens.params[2]
        self.gui.insert_server_widget(f"{channel}: {message}\n")

    def handle_unknown_mode(self, tokens):
        channel = tokens.params[1]
        message = tokens.params[2]
        self.gui.insert_server_widget(f"Unknown mode for {channel}: {message}\n")

    def handle_mode_info(self, tokens):
        channel = tokens.params[1]
        modes = tokens.params[2]
        self.gui.insert_server_widget(f"Modes for {channel}: {modes}\n")

    def handle_creation_time(self, tokens):
        channel = tokens.params[1]
        timestamp = int(tokens.params[2])  # Convert timestamp to an integer if it's a string
        creation_date = datetime.datetime.utcfromtimestamp(timestamp)
        formatted_date = creation_date.strftime('%Y-%m-%d %H:%M:%S UTC')  # Format the date as desired
        self.gui.insert_server_widget(f"Creation time for {channel}: {formatted_date}\n")

    def handle_not_channel_operator(self, tokens):
        channel = tokens.params[1]
        message = tokens.params[2]
        self.gui.insert_server_widget(f"{channel}: {message}\n")

    def handle_328(self, tokens):
        channel = tokens.params[1]
        url = tokens.params[2]
        self.gui.insert_server_widget(f"URL for {channel} {url}\n")

    async def handle_cannot_join_channel(self, tokens):
        channel_name = tokens.params[1]
        error_message = tokens.params[2]
        
        error_text = f"Cannot join channel {channel_name}: {error_message}\n"
        self.gui.insert_text_widget(error_text)

    def sanitize_channel_name(self, channel):
        #gotta remove any characters that are not alphanumeric or allowed special characters
        return re.sub(r'[^\w\-\[\]{}^`|]', '_', channel)

    def log_message(self, server, channel, sender, message, is_sent=False):
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

        # Determine script directory
        script_directory = os.path.dirname(os.path.abspath(__file__))

        logs_directory = os.path.join(script_directory, 'Logs')

        try:
            # Create the Logs directory if it doesn't exist
            os.makedirs(logs_directory, exist_ok=True)

            # Construct the full path for the log file inside the Logs directory
            filename = os.path.join(logs_directory, f'irc_log_{server}_{self.sanitize_channel_name(channel)}.txt')

            with open(filename, 'a', encoding='utf-8') as file:
                file.write(log_line)
        except Exception as e:
            print(f"Error logging message: {e}")

    def handle_query_command(self, args, timestamp):
        if len(args) < 2:
            self.gui.insert_text_widget(f"{timestamp}Error: Please provide a nickname for the query command.\n")
            return

        nickname = args[1]
        
        # Remove @ and + symbols from the nickname
        nickname = nickname.lstrip("@+")

        if nickname not in self.joined_channels:
            self.open_dm(nickname, timestamp)
        else:
            self.gui.insert_text_widget(f"{timestamp}You already have a DM open with {nickname}.\n")

    def handle_cq_command(self, args, timestamp):
        if len(args) < 2:
            self.gui.insert_text_widget(f"{timestamp}Usage: /cq <nickname>\n")
        else:
            nickname = args[1]
            if nickname in self.joined_channels:
                self.close_dm(nickname, timestamp)
            else:
                self.gui.insert_text_widget(f"No open private message with {nickname}.\n")

    def open_dm(self, nickname, timestamp):
        # Add the DM to the channel list
        self.joined_channels.append(nickname)
        self.gui.channel_lists[self.server] = self.joined_channels
        self.update_gui_channel_list()
        self.gui.insert_text_widget(f"{timestamp}Opened DM with {nickname}.\n")

    def close_dm(self, nickname, timestamp):
        # Remove the DM from the list of joined channels
        self.joined_channels.remove(nickname)

        # Remove the DM's messages from the channel_messages dictionary
        if self.server in self.channel_messages and nickname in self.channel_messages[self.server]:
            del self.channel_messages[self.server][nickname]

        # Remove the DM's entry from the highlighted_channels dictionary
        if self.server_name in self.highlighted_channels:
            self.highlighted_channels[self.server_name].pop(nickname, None)

        # Update the GUI's list of channels
        self.update_gui_channel_list()

        # Display a message indicating the DM was closed
        self.gui.insert_text_widget(f"Private message with {nickname} closed.\n")

    async def leave_channel(self, channel):
        await self.send_message(f'PART {channel}')
        if channel in self.joined_channels:
            self.joined_channels.remove(channel)

            # Remove the channel entry from the highlighted_channels dictionary
            if self.server_name in self.highlighted_channels:
                self.highlighted_channels[self.server_name].pop(channel, None)

            self.gui.channel_lists[self.server] = self.joined_channels
            self.update_gui_channel_list()

            # Remove the channel's history
            self.channel_messages[channel] = []

    async def handle_kick_command(self, args):
        if len(args) < 3:
            self.gui.insert_text_widget("Usage: /kick <user> <channel> [reason]\n")
            return
        user = args[1].lstrip('@+')
        channel = args[2]
        reason = ' '.join(args[3:]) if len(args) > 3 else None
        kick_message = f'KICK {channel} {user}' + (f' :{reason}' if reason else '')
        await self.send_message(kick_message)
        self.gui.insert_text_widget(f"Kicked {user} from {channel} for {reason}\n")

    async def handle_invite_command(self, args):
        if len(args) < 3:
            self.gui.insert_text_widget("Usage: /invite <user> <channel>\n")
            return
        user = args[1]
        channel = args[2]
        await self.send_message(f'INVITE {user} {channel}\n')
        self.gui.insert_text_widget(f"Invited {user} to {channel}\n")

    async def handle_notice_command(self, args):
        if len(args) < 3:
            self.gui.insert_text_widget("Usage: /notice <target> <message>\n")
            return
        target = args[1]
        message = ' '.join(args[2:])
        await self.send_message(f'NOTICE {target} :{message}\n')
        self.gui.insert_text_widget(f"Sent NOTICE to {target}: {message}\n")

    async def connect_to_specific_server(self, server_name):
        config_file = f"conf.{server_name}.rude"
        await self.gui.init_client_with_config(config_file, server_name)

    async def disconnect(self):
        if self.reader and not self.reader.at_eof():
            self.writer.close()
            await self.writer.wait_closed()
            await reset_state()

        self.gui.insert_text_widget("Disconnected from the server.\n")

    async def command_parser(self, user_input):
        args = user_input[1:].split() if user_input.startswith('/') else []
        primary_command = args[0] if args else None

        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')

        match primary_command:
            case "join":
                channel_name = args[1]
                await self.join_channel(channel_name)

            case "query":  # open a DM with a user
                self.handle_query_command(args, timestamp)

            case "cq":  # close a private message (query) with a user
                self.handle_cq_command(args, timestamp)

            case "quote":  # sends raw IRC message to the server
                if len(args) < 2:
                    self.gui.insert_text_widget(f"{timestamp}Error: Please provide a raw IRC command after /quote.\n")
                    return

                raw_command = " ".join(args[1:])
                await self.send_message(raw_command)
                self.gui.insert_text_widget(f"{timestamp}Sent raw command: {raw_command}\n")

            case "away":  # set the user as away
                away_message = " ".join(args[1:]) if len(args) > 1 else None
                if away_message:
                    await self.send_message(f"AWAY :{away_message}")
                    self.gui.insert_text_widget(f"{away_message}\n")
                    self.gui.update_users_label(away=True)
                else:
                    await self.send_message("AWAY")
                    self.gui.update_users_label(away=True)

            case "back":  # remove the "away" status
                await self.send_message("AWAY")
                self.gui.update_users_label(away=False)

            case "msg":  # send a private message to a user
                if len(args) < 3:
                    # Display an error message if not enough arguments are provided
                    self.gui.insert_text_widget(f"{timestamp}Usage: /msg <nickname> <message>\n")
                else:
                    nickname = args[1]
                    message = " ".join(args[2:])
                    await self.send_message(f"PRIVMSG {nickname} :{message}")
                    self.gui.insert_text_widget(f'<{self.nickname} -> {nickname}> {message}\n')

            case "CTCP":
                if len(args) < 3:
                    self.gui.insert_text_widget(f"{timestamp}Error: Please provide a nickname and CTCP command.\n")
                    return
                target_nick = args[1]
                ctcp_command = args[2]
                await self.send_ctcp_request(target_nick, ctcp_command)

            case "mode":
                if len(args) < 2:
                    self.gui.insert_text_widget("Error: Please provide a mode and a channel.\n")
                    self.gui.insert_text_widget("Usage: /mode [channel] [+|-][mode flags] [target]\n")
                    self.gui.insert_text_widget("Example for channel: /mode #channel_name +o username\n")
                    self.gui.insert_text_widget("Example for user: /mode #channel_name +o username\n")
                    return

                channel = args[1]
                mode = None
                target = None

                if len(args) > 2:
                    mode = args[2]

                if len(args) > 3:
                    target = args[3]

                await self.set_mode(channel, mode, target)

            case "who":
                await self.handle_who_command(args[1:])

            case "whois": #who is that?
                target = user_input.split()[1]
                await self.whois(target)

            case "part":
                channel_name = args[1]
                await self.leave_channel(channel_name)

            case "time":
                await self.send_message(f"TIME")

            case "me":
                if self.current_channel:
                    await self.handle_action(args)
                else:
                    self.gui.insert_text_widget(f"No channel selected. Use /join to join a channel.\n")

            case "list":
                await self.send_message("LIST")
                # Create the channel list window
                self.show_channel_list_window()

            case "ch":
                for channel in self.joined_channels:
                    self.gui.insert_text_widget(f'{channel}\n')

            case "sw":
                channel_name = args[1]
                if channel_name in self.joined_channels:
                    self.current_channel = channel_name
                    await self.display_last_messages(self.current_channel)
                    self.gui.highlight_nickname()
                else:
                    self.gui.insert_text_widget(f"Not a member of channel {channel_name}\n")

            case "topic":
                new_topic = ' '.join(args[1:])
                await self.request_send_topic(new_topic)

            case "names":
                await self.refresh_user_list_for_current_channel()

            case "banlist":
                channel = args[1] if len(args) > 1 else self.current_channel
                if channel:
                    await self.send_message(f"MODE {channel} +b")

            case "nick":
                if len(args) < 2:
                    self.gui.insert_text_widget(f"{timestamp}Error: Please provide a new nickname.\n")
                    return
                new_nick = args[1]
                await self.change_nickname(new_nick, is_from_token=False)

            case "ping":
                await self.ping_server()

            case "sa":
                if len(args) < 2:
                    self.gui.insert_text_widget(f"{timestamp}Error: Please provide a message to send to all channels.\n")
                    return
                message = " ".join(args[1:])
                await self.send_message_to_all_channels(message)

            case "quit":
                quit_message = " ".join(args[1:]) if len(args) > 0 else None
                self.save_channel_messages()
                await self.gui.send_quit_to_all_clients(quit_message)
                await asyncio.sleep(1)
                self.master.destroy()
                return False

            case "help":
                self.display_help()

            case "fortune":
                file_name_arg = args[1] if len(args) > 1 else None
                await self.fortune(file_name_arg)
            case "cowsay":
                await self.handle_cowsay_command(args)

            case "ignore":
                self.ignore_user(args)
                
            case "unignore":
                self.unignore_user(args)

            case "kick":
                await self.handle_kick_command(args)

            case "invite":
                await self.handle_invite_command(args)

            case "clear": #Clears the screen
                self.gui.clear_chat_window()

            case "mac":
                await self.handle_mac_command(args)

            case "notice":
                await self.handle_notice_command(args)

            case "connect":
                server_name = args[1] if len(args) > 1 else None
                if server_name:
                    await self.connect_to_specific_server(server_name)
                else:
                    self.gui.insert_text_widget("Usage: /connect <server_name>\n")

            case "disconnect":
                await self.disconnect()
                await self.gui.remove_server_from_dropdown(server_name=None)

            case None:
                if not user_input:
                    return
                escaped_input = self.escape_color_codes(user_input)
                if self.current_channel:
                    await self.send_message(f'PRIVMSG {self.current_channel} :{escaped_input}')
                    self.gui.insert_text_widget(f"{timestamp}<{self.nickname}> {escaped_input}\n")
                    self.gui.highlight_nickname()

                    # Check if it's a DM or channel
                    if self.current_channel.startswith(self.chantypes):  # It's a channel
                        if self.current_channel not in self.channel_messages:
                            self.channel_messages[self.current_channel] = []
                        self.channel_messages[self.current_channel].append(f"{timestamp}<{self.nickname}> {escaped_input}\n")

                    else:  # It's a DM
                        server_name = self.server  # Replace this with the actual server name if needed
                        if server_name not in self.channel_messages:
                            self.channel_messages[server_name] = {}
                        if self.current_channel not in self.channel_messages[server_name]:
                            self.channel_messages[server_name][self.current_channel] = []
                        self.channel_messages[server_name][self.current_channel].append(f"{timestamp}<{self.nickname}> {escaped_input}\n")

                    # Trim the messages list if it exceeds 100 lines
                    messages = self.channel_messages.get(server_name, {}).get(self.current_channel, []) if not self.current_channel.startswith("#") else self.channel_messages.get(self.current_channel, [])
                    if len(messages) > 100:
                        messages = messages[-100:]

                    # Log the sent message using the new logging method
                    self.log_message(self.server_name, self.current_channel, self.nickname, escaped_input, is_sent=True)

                else:
                    self.gui.insert_text_widget(f"No channel selected. Use /join to join a channel.\n")

        return True

    async def handle_mac_command(self, args):
        if len(args) < 2:
            available_macros = ", ".join(self.ASCII_ART_MACROS.keys())
            self.gui.insert_text_widget(f"Available ASCII art macros: {available_macros}\n")
            self.gui.insert_text_widget("Usage: /mac <macro_name>\n")
            return

        macro_name = args[1]
        if macro_name in self.ASCII_ART_MACROS:
            current_time = datetime.datetime.now().strftime('[%H:%M:%S] ')
            for line in self.ASCII_ART_MACROS[macro_name].splitlines():
                formatted_message = self.format_message(line, current_time)
                await self.send_message(f'PRIVMSG {self.current_channel} :{formatted_message}')
                self.gui.insert_text_widget(f"{current_time}<{self.nickname}> {formatted_message}")
                self.gui.highlight_nickname()
                await asyncio.sleep(0.5)
                await self.append_to_channel_history(self.current_channel, line)
        else:
            self.gui.insert_text_widget(f"Unknown ASCII art macro: {macro_name}. Type '/mac' to see available macros.\n")

    def format_message(self, line, current_time):
        # Process the whole string and escape color codes
        processed_line = self.escape_color_codes(line)

        # Add current time and nickname to the message
        formatted_message = f'{processed_line}\n'

        return formatted_message

    def escape_color_codes(self, line):
        # Escape color codes in the string
        escaped_line = re.sub(r'\\x([0-9a-fA-F]{2})', lambda match: bytes.fromhex(match.group(1)).decode('utf-8'), line)
        
        return escaped_line

    async def load_ascii_art_macros(self):
        """Load ASCII art from files into a dictionary asynchronously."""
        self.gui.insert_text_widget("Loading ASCII art macros...\n")
        script_directory = os.path.dirname(os.path.abspath(__file__))
        ASCII_ART_DIRECTORY = os.path.join(script_directory, 'Art')

        for file in os.listdir(ASCII_ART_DIRECTORY):
            if file.endswith(".txt"):
                file_path = os.path.join(ASCII_ART_DIRECTORY, file)
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    macro_name, _ = os.path.splitext(file)
                    self.ASCII_ART_MACROS[macro_name] = await f.read()

    async def update_available_macros(self):
        """Update the available macros list."""
        self.gui.insert_text_widget("Reloading Macros...\n")
        self.ASCII_ART_MACROS = {}
        await self.load_ascii_art_macros()
        self.gui.insert_text_widget("Macros Reloaded!\n")
        available_macros = ", ".join(self.ASCII_ART_MACROS.keys())
        self.gui.insert_text_widget(f"Available ASCII art macros: {available_macros}\n") 

    def ignore_user(self, args):
        user_to_ignore = " ".join(args[1:])
        if user_to_ignore not in self.ignore_list:
            self.ignore_list.append(user_to_ignore)
            self.gui.insert_text_widget(f"You've ignored {user_to_ignore}.\n")
            self.save_ignore_list()
        else:
            self.gui.insert_text_widget(f"{user_to_ignore} is already in your ignore list.\n")

    def unignore_user(self, args):
        if len(args) < 2:  # Check if the user has provided the username to unignore
            self.gui.insert_text_widget("Usage: unignore <username>\n")
            return

        user_to_unignore = args[1]
        if user_to_unignore in self.ignore_list:
            self.ignore_list.remove(user_to_unignore)
            self.gui.insert_text_widget(f"You've unignored {user_to_unignore}.\n")
            self.save_ignore_list()
        else:
            self.gui.insert_text_widget(f"{user_to_unignore} is not in your ignore list.\n")

    def save_ignore_list(self):
        script_directory = os.path.dirname(os.path.abspath(__file__))
        
        # Construct the full path for the ignore_list.txt
        file_path = os.path.join(script_directory, 'ignore_list.txt')
        with open(file_path, "w", encoding='utf-8') as f:
            for user in self.ignore_list:
                f.write(f"{user}\n")

    def load_ignore_list(self):
        script_directory = os.path.dirname(os.path.abspath(__file__))
        
        # Construct the full path for the ignore_list.txt
        file_path = os.path.join(script_directory, 'ignore_list.txt')
        
        if os.path.exists(file_path):
            with open(file_path, "r", encoding='utf-8') as f:
                self.ignore_list = [line.strip() for line in f.readlines()]
        else:
            # If the file doesn't exist, create it
            with open(file_path, "w", encoding='utf-8') as f:
                # You can add default content to the file if needed
                pass

    def reload_ignore_list(self):
        self.ignore_list = []
        self.load_ignore_list()
        self.gui.insert_text_widget(f"Ignore List reloaded.\n")

    def handle_banlist(self, tokens):
        """
        Handle the RPL_BANLIST reply, which provides info about each ban mask.
        """
        channel = tokens.params[1]
        banmask = tokens.params[2]
        setter = tokens.params[3]
        timestamp = tokens.params[4]
        
        # Construct the ban information message
        ban_info = f"Channel: {channel}, Banmask: {banmask}, Set by: {setter}, Timestamp: {timestamp}\n"
        
        # Update the GUI's message text with this ban information
        self.gui.insert_text_widget(ban_info)

    def handle_endofbanlist(self, tokens):
        """
        Handle the RPL_ENDOFBANLIST reply, signaling the end of the ban list.
        """
        channel = tokens.params[1]
        
        # Notify the user that the ban list has ended
        end_message = f"End of ban list for channel: {channel}\n"
        self.gui.insert_text_widget(end_message) 

    async def append_to_channel_history(self, channel, message, is_action=False):
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
        
        # Escape color codes in the message
        escaped_message = self.escape_color_codes(message)

        formatted_message = f"{timestamp}<{self.nickname}> {escaped_message}\n"

        # Initialize the server name
        server_name = self.server

        # Determine if it's a channel or DM
        if channel.startswith(self.chantypes):  # It's a channel
            if channel not in self.channel_messages:
                self.channel_messages[channel] = []
            self.channel_messages[channel].append(formatted_message)
        else:  # It's a DM
            if server_name not in self.channel_messages:
                self.channel_messages[server_name] = {}
            if channel not in self.channel_messages[server_name]:
                self.channel_messages[server_name][channel] = []
            self.channel_messages[server_name][channel].append(formatted_message)

        # Trim the history if it exceeds 100 lines
        self.trim_messages(channel, server_name)

    async def handle_cowsay_command(self, args):
        script_directory = os.path.dirname(os.path.abspath(__file__))

        if len(args) > 1:
            file_name_arg = args[1]
            # Construct the potential file path using the absolute path
            potential_path = os.path.join(script_directory, "Fortune Lists", f"{file_name_arg}.txt")

            # Check if the provided argument corresponds to a valid fortune file
            if os.path.exists(potential_path):
                await self.fortune_cowsay(file_name_arg)
            else:
                # If not a valid file name, consider the rest of the arguments as a custom message
                custom_message = ' '.join(args[1:])
                await self.cowsay_custom_message(custom_message)
        else:
            await self.fortune_cowsay()

    def cowsay(self, message):
        """Formats the given message in a 'cowsay' format."""

        # Find the longest line in the input message to determine the maximum width.
        max_line_length = max(len(line) for line in message.split('\n'))
        # Adjust for the added spaces and border characters
        adjusted_width = max_line_length - 4  # 2 for initial and end space + 2 for border characters

        # Manually split lines to check for one-word lines.
        raw_lines = message.split('\n')
        wrapped_lines = []
        for line in raw_lines:
            if len(line.split()) == 1:  # Single word line
                wrapped_lines.append(line)
            else:
                wrapped_lines.extend(textwrap.wrap(line, adjusted_width))

        # Format lines using cowsay style.
        if len(wrapped_lines) == 1:
            # Special case: single line message.
            combined_message = f"/ {wrapped_lines[0].ljust(adjusted_width)} \\"
        else:
            lines = [f"/ {wrapped_lines[0].ljust(adjusted_width)} \\"]
            for line in wrapped_lines[1:-1]:
                lines.append(f"| {line.ljust(adjusted_width)} |")
            lines.append(f"\\ {wrapped_lines[-1].ljust(adjusted_width)} /")
            combined_message = '\n'.join(lines)

        # Find the longest line again (after formatting) to adjust the borders accordingly.
        max_line_length = max(len(line) for line in combined_message.split('\n'))

        top_border = ' ' + '_' * (max_line_length - 2)
        
        # Set the bottom border to match the max line length
        bottom_border = ' ' + '-' * (max_line_length - 2)

        cow = """
       \\   ^__^
        \\  (oo)\\_______
           (__)\\       )\\/\\
               ||----w |
               ||     ||"""

        return f"{top_border}\n{combined_message}\n{bottom_border}{cow}"

    def wrap_text(self, text, width=100):
        """Dont spam that channel"""
        return textwrap.fill(text, width)

    def get_fortune_file(self, file_name=None):
        script_directory = os.path.dirname(os.path.abspath(__file__))
        fortune_directory = os.path.join(script_directory, "Fortune Lists")
        
        if file_name:
            return os.path.join(fortune_directory, file_name + ".txt")
        
        fortune_files = [os.path.join(fortune_directory, f) for f in os.listdir(fortune_directory) if f.endswith('.txt')]
        return random.choice(fortune_files)

    async def fortune_cowsay(self, file_name=None):
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
        file_name = self.get_fortune_file(file_name)

        with open(file_name, 'r', encoding='utf-8') as f:
            fortunes = f.read().strip().split('%')
            chosen_fortune = random.choice(fortunes).strip()

        wrapped_fortune_text = self.wrap_text(chosen_fortune)
        cowsay_fortune = self.cowsay(wrapped_fortune_text)

        for line in cowsay_fortune.split('\n'):
            formatted_message = f"{timestamp}<{self.nickname}> {line}\n"
            await self.send_message(f'PRIVMSG {self.current_channel} :{line}')
            self.gui.insert_text_widget(formatted_message)
            self.gui.highlight_nickname()
            await asyncio.sleep(0.4)
            await self.append_to_channel_history(self.current_channel, line)

    async def cowsay_custom_message(self, message):
        """Wrap a custom message using the cowsay format."""
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
        wrapped_message = self.wrap_text(message)
        cowsay_output = self.cowsay(wrapped_message)
        
        for line in cowsay_output.split('\n'):
            formatted_message = f"{timestamp}<{self.nickname}> {line}\n"
            await self.send_message(f'PRIVMSG {self.current_channel} :{line}')
            self.gui.insert_text_widget(formatted_message)
            self.gui.highlight_nickname()
            await asyncio.sleep(0.4)
            await self.append_to_channel_history(self.current_channel, line)

    async def fortune(self, file_name=None):
        """Choose a random fortune from one of the lists"""
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
        file_name = self.get_fortune_file(file_name)

        with open(file_name, 'r', encoding='utf-8') as f:  # Notice the encoding parameter
            fortunes = f.read().strip().split('%')
            chosen_fortune = random.choice(fortunes).strip()

        for line in chosen_fortune.split('\n'):
            formatted_message = f"{timestamp}<{self.nickname}> {line}\n"
            await self.send_message(f'PRIVMSG {self.current_channel} :{line}')
            self.gui.insert_text_widget(formatted_message)
            self.gui.highlight_nickname()
            await asyncio.sleep(0.4)
            await self.append_to_channel_history(self.current_channel, line)

    async def send_ctcp_request(self, target_nick, ctcp_command):
        """Sends a CTCP request to a target."""
        ctcp_message = f"\x01{ctcp_command.upper()}\x01"
        await self.send_message(f'PRIVMSG {target_nick} :{ctcp_message}')

    async def set_mode(self, channel, mode, target=None):
        """Sets the mode for a specified target in a specified channel.
        If target is None, sets the mode for the channel.
        """
        if mode and target:
            await self.send_message(f'MODE {channel} {mode} {target}')
        elif mode:
            await self.send_message(f'MODE {channel} {mode}')
        else:
            await self.send_message(f'MODE {channel}')

    async def request_send_topic(self, new_topic=None):
        if self.current_channel:
            if new_topic:
                # Set the new topic
                await self.send_message(f'TOPIC {self.current_channel} :{new_topic}')
            else:
                # Request the current topic
                await self.send_message(f'TOPIC {self.current_channel}')
        else:
            self.gui.insert_text_widget("No channel selected. Use /join to join a channel.\n")

    async def refresh_user_list_for_current_channel(self):
        if self.current_channel:
            await self.send_message(f'NAMES {self.current_channel}')
        else:
            self.gui.insert_text_widget("No channel selected. Use /join to join a channel.\n")

    async def change_nickname(self, new_nick, is_from_token=False):
        if not is_from_token:
            await self.send_message(f'NICK {new_nick}')
        self.nickname = new_nick  # update local state
        self.gui.update_nick_channel_label() 

    async def ping_server(self):
        # Initialize ping_start_time to the current time
        self.ping_start_time = time.time()

        await self.send_message(f'PING {self.server}')

    async def send_message_to_all_channels(self, message):
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
        formatted_message = f"{timestamp}<{self.nickname}> {message}\n"
        
        for channel in self.joined_channels:
            await self.send_message(f'PRIVMSG {channel} :{message}')
            
            # Save the message to the channel_messages dictionary
            if channel not in self.channel_messages:
                self.channel_messages[channel] = []
            self.channel_messages[channel].append(formatted_message)
            
            # Trim the messages list if it exceeds 100 lines
            self.trim_messages(channel, server_name=None)

        self.gui.insert_text_widget(f"Message: {message} sent to all channels")

    async def handle_who_command(self, args):
        """
        Handle the WHO command entered by the user.
        """
        if not args:
            # General WHO
            await self.send_message('WHO')
        elif args[0].startswith(self.chantypes):
            # WHO on a specific channel
            channel = args[0]
            await self.send_message(f'WHO {channel}')
        else:
            # WHO with mask or user host
            mask = args[0]
            await self.send_message(f'WHO {mask}')

    async def whois(self, target):
        """
        Who is this? Sends a whois request
        """
        await self.send_message(f'WHOIS {target}')

    async def handle_action(self, args):
        action_message = ' '.join(args[1:])
        formatted_message = f"* {self.nickname} {action_message}"
        await self.send_message(f'PRIVMSG {self.current_channel} :\x01ACTION {action_message}\x01')
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
        self.gui.insert_text_widget(f"{timestamp}{formatted_message}\n")
        self.gui.highlight_nickname()

        # Save the action message to the channel_messages dictionary
        if self.current_channel not in self.channel_messages:
            self.channel_messages[self.current_channel] = []
        self.channel_messages[self.current_channel].append(f"{timestamp}{formatted_message}\n")

        # Trim the messages list if it exceeds 100 lines
        self.trim_messages(self.current_channel, server_name=None)

    def display_help(self):
        # Categories and their associated commands
        categories = {
            "Channel Management": [
                "Use Your Right Click for Config and more.",
                "To use formatting use the format control characters as follows",
                "/join <channel> - Joins a channel",
                "/part <channel> - Leaves a channel",
                "/ch - Shows channels joined",
                "/sw <channel> - Switches to a channel",
                "/topic - Requests the topic for the current channel",
                "/names - Refreshes the user list for the current channel",
                "/banlist - Shows ban list for channel",
                "/invite <user> <channel> - invites a user to a channel",
                "/kick <user> <channel> [message]",
            ],
            "String Formatting": [
                "\\x02 - Bold",
                "\\x1D - Italic",
                "\\x1F - Underline",
                "\\x03<colorcode> - Color",
                "\\x0F - Terminate formatting - end of format string",
                "Example: \\x0304example text\\x0F",
            ],
            "Private Messaging": [
                "/query <nickname> - Opens a DM with a user",
                "/cq <nickname> - Closes a DM with a user",
                "/msg <nickname> [message] - Sends a private message to a user",
            ],
            "User Commands": [
                "/nick <new nickname> - Changes the user's nickname",
                "/away [message] - Sets the user as away",
                "/back - Removes the 'away' status",
                "/who <mask> - Lists users matching a mask",
                "/whois <nickname> - Shows information about a user",
                "/me <action text> - Sends an action to the current channel",
                "/clear - clears the chat window and removes all messages for the current channel",
            ],
            "Server Interaction": [
                "/ping - Pings the currently selected server",
                "/quote <IRC command> - Sends raw IRC message to the server",
                "/CTCP <nickname> <command> - Sends a CTCP request",
                "/mode <mode> [channel] - Sets mode for user (optionally in a specific channel)",
            ],
            "Broadcasting": [
                "/sa [message] - Sends a message to all channels",
                "/mac <macro> - sends a chosen macro to a channel /mac - shows available macros",
                "/notice <target> [message]",
            ],
            "Help and Connection": [
                "/quit - Closes connection and client",
                "/help - Redisplays this message",
                "/disconnect - Will disconnect you from the currently selected server",
                "/connect <server_name> - Will connect you to the given server, is case sensitive.",
            ],
        }

        # Display the categorized commands
        for category, commands in categories.items():
            self.gui.insert_text_widget(f"\n{category}:\n")
            for cmd in commands:
                self.gui.insert_text_widget(f"{cmd}\n")
                self.gui.insert_and_scroll()

    def set_gui(self, gui):
        self.gui = gui

    def set_server_name(self, server_name):
        self.server_name = server_name
        self.gui.update_nick_channel_label()

    async def main_loop(self):
        while True:
            try:
                loop = asyncio.get_event_loop()
                user_input = await loop.run_in_executor(None, input, f'{self.current_channel} $ {self.nickname}')
                should_continue = await self.command_parser(user_input)
                if not should_continue:
                    break
            except KeyboardInterrupt:
                await self.send_message('QUIT')
                break

    async def start(self):
        await self.connect()

        asyncio.create_task(self.keep_alive())
        asyncio.create_task(self.handle_incoming_message())

        await self.main_loop()

    async def display_last_messages(self, channel, num=100, server_name=None):
        if server_name:
            messages = self.channel_messages.get(server_name, {}).get(channel, [])
        else:
            messages = self.channel_messages.get(channel, [])

        for message in messages[-num:]:
            self.gui.insert_text_widget(message)
