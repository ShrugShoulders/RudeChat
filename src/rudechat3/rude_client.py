#!/usr/bin/env python
from .list_window import ChannelListWindow
from .rude_pronouns import replace_pronouns
from .shared_imports import *

class RudeChatClient:
    def __init__(self, text_widget, server_text_widget, entry_widget, master, gui):
        self.master = master
        self.text_widget = text_widget
        self.entry_widget = entry_widget
        self.server_text_widget = server_text_widget
        self.gui = gui
        self.nicknamelen = 0
        self.chan_limit = 0
        self.channellen = 0
        self.topiclen = 0
        self.current_channel = ''
        self.nickname = ''
        self.chantypes = ''
        self.joined_channels = []
        self.motd_lines = []
        self.ignore_list = []
        self.detached_channels = []
        self.motd_dict = {}
        self.channel_messages = {}
        self.channel_users = {}
        self.user_modes = {}
        self.mode_to_symbol = {}
        self.whois_data = {}
        self.download_channel_list = {}
        self.highlighted_channels = {}
        self.highlighted_servers = {}
        self.mentions = {}
        self.ASCII_ART_MACROS = {}
        self.client_event_loops = {}
        self.tasks = {}
        self.whois_executed = set()
        self.decoder = irctokens.StatefulDecoder()
        self.encoder = irctokens.StatefulEncoder()
        self.reader = None
        self.writer = None
        self.ping_start_time = None
        self.isupport_flag = False
        self.loop_running = True
        self.config = ''
        self.message_handling_semaphore = asyncio.Semaphore(50)
        self.delete_lock_files()
        self.loop = asyncio.get_event_loop()
        self.time_zone = get_localzone()

    async def read_config(self, config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        self.server = config.get('IRC', 'server')
        self.port = config.getint('IRC', 'port')
        self.ssl_enabled = config.getboolean('IRC', 'ssl_enabled')
        self.nickname = config.get('IRC', 'nickname')
        self.use_nickserv_auth = config.getboolean('IRC', 'use_nickserv_auth', fallback=False)
        self.nickserv_password = config.get('IRC', 'nickserv_password') if self.use_nickserv_auth else None
        self.auto_join_channels = config.get('IRC', 'auto_join_channels', fallback=None).split(',')
        self.use_auto_join = config.getboolean('IRC', 'use_auto_join', fallback=True)
        self.auto_rejoin = config.getboolean('IRC', 'auto_rejoin', fallback=True)
        self.sasl_enabled = config.getboolean('IRC', 'sasl_enabled', fallback=False)
        self.sasl_username = config.get('IRC', 'sasl_username', fallback=None)
        self.sasl_password = config.get('IRC', 'sasl_password', fallback=None)
        self.server_name = config.get('IRC', 'server_name', fallback=None)
        self.znc_connection = config.getboolean('IRC', 'znc_connection', fallback=False)
        self.znc_password = config.get('IRC', 'znc_password', fallback=None)
        self.ignore_cert = config.get('IRC', 'ignore_cert', fallback=False)
        self.znc_user = config.get('IRC', 'znc_user', fallback=None)
        self.use_colors = config.getboolean('IRC', 'use_irc_colors', fallback=False)

        self.mention_note_color = config.get('IRC', 'mention_note_color', fallback='red')
        self.activity_note_color = config.get('IRC', 'activity_note_color', fallback='green')
        self.use_time_stamp = config.getboolean('IRC', 'use_time_stamp', fallback=True)
        self.show_full_hostmask = config.getboolean('IRC', 'show_hostmask', fallback=True)
        self.show_join_part_quit_nick = config.getboolean('IRC', 'show_join_part_quit_nick', fallback=True)
        self.use_beep_noise = config.getboolean('IRC', 'use_beep_noise', fallback=True)
        self.auto_whois = config.getboolean('IRC', 'auto_whois', fallback=True)
        self.custom_sounds = config.getboolean('IRC', 'custom_sounds', fallback=False)
        self.use_logging = config.getboolean('IRC', 'use_logging', fallback=True)
        self.replace_pronouns = config.getboolean('IRC', 'replace_pronouns', fallback=False)
        await self.load_channel_messages()
        self.load_ignore_list()
        self.gui.update_nick_channel_label()
        self.config = config_file

    def reload_config(self, config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        
        # Reload specific variables
        self.mention_note_color = config.get('IRC', 'mention_note_color', fallback='red')
        self.activity_note_color = config.get('IRC', 'activity_note_color', fallback='green')
        self.use_time_stamp = config.getboolean('IRC', 'use_time_stamp', fallback=True)
        self.show_full_hostmask = config.getboolean('IRC', 'show_hostmask', fallback=True)
        self.show_join_part_quit_nick = config.getboolean('IRC', 'show_join_part_quit_nick', fallback=True)
        self.use_beep_noise = config.getboolean('IRC', 'use_beep_noise', fallback=True)
        self.auto_whois = config.getboolean('IRC', 'auto_whois', fallback=True)
        self.custom_sounds = config.getboolean('IRC', 'custom_sounds', fallback=False)
        self.use_logging = config.getboolean('IRC', 'use_logging', fallback=True)
        self.use_colors = config.getboolean('IRC', 'use_irc_colors', fallback=False)
        self.replace_pronouns = config.getboolean('IRC', 'replace_pronouns', fallback=False)
        self.gui.update_nick_channel_label()

    def delete_lock_files(self):
        script_directory = os.path.dirname(os.path.abspath(__file__))
        lock_file_pattern = os.path.join(script_directory, '*.lock')
        lock_files = glob.glob(lock_file_pattern)

        for lock_file in lock_files:
            try:
                os.remove(lock_file)
            except OSError as e:
                print(f"Error deleting {lock_file}: {e}")

    async def load_channel_messages(self):
        script_directory = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_directory, f'channel_messages_{self.server_name}.json')
        try:
            async with aiofiles.open(file_path, 'r') as file:
                file_content = await file.read()
                if file_content:
                    self.channel_messages = json.loads(file_content)
                else:
                    self.channel_messages = {}
        except (FileNotFoundError, json.JSONDecodeError):
            self.channel_messages = {}

    async def save_channel_messages(self):
        script_directory = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_directory, f'channel_messages_{self.server_name}.json')
        lock_file_path = os.path.join(script_directory, f'channel_messages_{self.server_name}.lock')

        try:
            # Acquire the lock
            while os.path.exists(lock_file_path):
                await asyncio.sleep(0.1)  # Wait for the lock to be released

            async with aiofiles.open(lock_file_path, 'w') as lock_file:
                await lock_file.write("locked")

            # Read existing data
            existing_messages = {}
            if os.path.exists(file_path):
                try:
                    async with aiofiles.open(file_path, 'r') as file:
                        existing_messages = json.loads(await file.read())
                except json.JSONDecodeError:
                    print("JSON decode error occurred, initializing with an empty dictionary.")
                    existing_messages = {}

            # Update existing data with new channel messages
            existing_messages.update(self.channel_messages)

            # Write the updated data back to the file
            async with aiofiles.open(file_path, 'w') as file:
                await file.write(json.dumps(existing_messages, indent=2))

        except Exception as e:
            print(f"Error occurred while saving channel messages: {e}")

        finally:
            # Release the lock
            try:
                os.remove(lock_file_path)
            except Exception as e:
                print(f"Error occurred while removing lock file: {e}")

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
                if not self.ignore_cert:
                    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                    context.check_hostname = True
                    context.verify_mode = ssl.CERT_REQUIRED
                    self.reader, self.writer = await asyncio.wait_for(
                        asyncio.open_connection(self.server, self.port, ssl=context),
                        timeout=TIMEOUT
                    )
                elif self.ignore_cert:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    self.reader, self.writer = await asyncio.wait_for(
                        asyncio.open_connection(self.server, self.port, ssl=context),
                        timeout=TIMEOUT
                    )
            else:
                self.reader, self.writer = await asyncio.wait_for(
                    asyncio.open_connection(self.server, self.port),
                    timeout=TIMEOUT
                )

            if self.znc_connection:
                await self.send_message(f'PASS {self.znc_password}')

        except asyncio.TimeoutError:
            self.gui.insert_text_widget(f"Connection timeout. Please try again later.\n")
        except OSError as e:
            print("OSError Caught In connect_to_server")

    async def send_initial_commands(self):
        self.gui.insert_text_widget(f'Sent client registration commands.\n')

        # Start capability negotiation
        if self.sasl_enabled:
            self.gui.insert_text_widget("Beginning SASL Authentication\n")
            await self.send_message('CAP LS 302')
        else:
            self.gui.insert_text_widget("SASL is not enabled.\n")

        if self.znc_connection:
            await self.send_message(f'NICK {self.znc_user}')
            await self.send_message(f'USER {self.znc_user} 0 * :{self.znc_user}')
        elif not self.znc_connection:
            await self.send_message(f'NICK {self.nickname}')
            await self.send_message(f'USER {self.nickname} 0 * :{self.nickname}')

    def handle_motd_line(self, tokens):
        motd_line = tokens.params[-1]  # Assumes the MOTD line is the last parameter
        self.motd_lines.append(motd_line)

    def handle_motd_start(self, tokens):
        self.motd_lines.clear()
        motd_start_line = tokens.params[-1]  # Assumes the introductory line is the last parameter
        self.motd_lines.append(motd_start_line)

    def handle_motd_end(self, tokens):
        full_motd = "\n".join(self.motd_lines)
        
        if self.server_name in self.motd_dict:
            self.motd_dict[self.server_name] += full_motd + "\n"
        else:
            self.motd_dict[self.server_name] = full_motd + "\n"

        self.gui.insert_text_widget(f"Message of the Day:\n{full_motd}\n")
        self.motd_lines.clear()
            
    async def wait_for_welcome(self, config_file):
        try:
            await self._await_welcome_message()
            return  # Successfully connected and received 001
        except (OSError, ConnectionError) as e:
            print(f"Error occurred in wait_for_welcome: {e}.\n")
            return

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
        if self.use_auto_join:
            for channel in self.auto_join_channels:
                await self.join_channel(channel)
                await asyncio.sleep(0.1)
        else:
            pass

    async def auto_topic_nicklist(self):
        for channel in self.auto_join_channels:
            if channel in self.joined_channels:
                # Check if topic is empty
                if len(self.gui.channel_topics.get(self.server, {}).get(channel, [])) < 10:
                    await self.send_message(f"TOPIC {channel}")
                # Check if names list is empty
                if len(self.channel_users.get(channel, [])) < 10:
                    await self.send_message(f"NAMES {channel}")

    def server_message_handler(self, tokens):
        if len(tokens.params) > 3:
            params_combined = ' '.join(tokens.params[1:])
            self.add_server_message(params_combined + "\n")
        elif len(tokens.params) == 3:
            params_combined = ' '.join(tokens.params[1:])
            self.add_server_message(params_combined + "\n")
        else:
            data = tokens.params[1]
            self.add_server_message(data + "\n")

    async def join_znc_channel(self, tokens):
        channel = tokens.params[0]
        user_info = tokens.hostmask.nickname
        if user_info != self.nickname:
            self.handle_join(tokens)
            return

        if self.znc_connection:
            # Check if the server entry exists
            if self.server not in self.channel_messages:
                self.channel_messages[self.server] = {}

            # Add the channel entry if it doesn't exist
            if channel not in self.channel_messages[self.server]:
                self.channel_messages[self.server][channel] = []
            
            # Check if the channel is already in the list of joined channels
            if channel not in self.joined_channels:
                self.joined_channels.append(channel)
                self.gui.channel_lists[self.server] = self.joined_channels
                self.update_gui_channel_list()

    async def _await_welcome_message(self):
        self.gui.insert_text_widget(f'Waiting for welcome message from the server.\n')
        buffer = ""
        sync = True
        received_001 = False
        motd_received = False
        sasl_authenticated = False
        logged_in = False
        nickserv_sent = False
        got_396 = False
        znc_connected = False
        count_366 = 0
        got_topic = 0
        last_366_time = None
        TIMEOUT_SECONDS = 0.17
        MAX_WAIT_TIME = 60
        PRIVMSGTOKENS = []

        start_time = asyncio.get_event_loop().time()

        async def insert_processing_symbols(PRIVMSGTOKENS):
            symbol_list = ['░', '▒', '▓', '█']
            num_tokens = len(PRIVMSGTOKENS)
            block_thresholds = [num_tokens // len(symbol_list) * (i + 1) for i in range(len(symbol_list))]

            self.gui.insert_text_widget(f'\n\x0307\x02Processing Messages: \x0F')
            for i, tokens in enumerate(PRIVMSGTOKENS):
                for j, threshold in enumerate(block_thresholds):
                    if i < threshold:
                        self.gui.insert_text_widget(f'\x0303{symbol_list[j]}\x0F')
                        break
                await self.handle_privmsg(tokens, znc_privmsg=True)
            self.gui.insert_text_widget(f'\n\x0303\x02DONE!\x0F\n')

        def reset_timer(symbol):
            nonlocal last_366_time
            nonlocal sync
            if not self.use_auto_join:
                last_366_time = asyncio.get_event_loop().time()
                if motd_received:
                    if sync:
                        self.gui.insert_text_widget(f'\x0307\x02Syncing with ZNC:\x0F ')
                        sync = False
                    else:
                        self.gui.insert_text_widget(f'\x0303\x02{symbol}\x0F')

        def check_timeout():
            nonlocal last_366_time
            if not self.use_auto_join:
                if last_366_time is None:
                    return False
                return asyncio.get_event_loop().time() - last_366_time > TIMEOUT_SECONDS

        while True:
            data = await self.reader.read(4096)
            if not data:
                raise ConnectionError("Connection lost while waiting for the welcome message.")

            decoded_data = data.decode('UTF-8', errors='ignore')
            buffer += decoded_data
            while '\r\n' in buffer:
                line, buffer = buffer.split('\r\n', 1)
                tokens = irctokens.tokenise(line)
                if check_timeout():
                    # Timeout occurred
                    if self.znc_connection:
                        await insert_processing_symbols(PRIVMSGTOKENS)
                        await asyncio.sleep(0.000001)
                        return

                match tokens.command:
                    case "NOTICE":
                        self.handle_notice_message(tokens)
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
                        if logged_in and sasl_authenticated and self.isupport_flag and motd_received:
                            if self.use_auto_join:
                                await self.automatic_join()
                                return
                            elif not self.use_auto_join:
                                return

                    case "904":
                        self.gui.insert_text_widget("Handling SASL failed message\n")
                        self.handle_sasl_failed()

                    case "001":
                        if self.znc_connection:
                            reset_timer("!")
                        self.gui.insert_text_widget(f'Connected to the server: {self.server}:{self.port}\n')
                        received_001 = True
                        self.gui.insert_and_scroll()
                    case "002" | "003" | "004":
                        if self.znc_connection:
                            reset_timer("!")
                        self.server_message_handler(tokens)
                    case "005":
                        if self.znc_connection:
                            reset_timer("!")
                        self.handle_isupport(tokens)
                        self.isupport_flag = True
                        self.gui.insert_and_scroll()

                    case "251" | "252" | "253" | "254" | "255" | "265":
                        self.server_message_handler(tokens)
                    case "311" | "312" | "313" | "317" | "319" | "301" | "671" | "338" | "318" | "330":
                        await self.handle_whois_replies(tokens.command, tokens)
                    case "PART":
                        self.handle_part(tokens)
                    case "QUIT":
                        self.handle_quit(tokens)
                    case "NICK":
                        await self.handle_nick(tokens)
                    case "JOIN":
                        if self.znc_connection:
                            await self.join_znc_channel(tokens)
                            reset_timer("#")
                    case "PRIVMSG":
                        if self.znc_connection:
                            PRIVMSGTOKENS.append(tokens)
                        else:
                            await self.handle_privmsg(tokens)

                    case "MODE":
                        self.handle_mode(tokens)
                    case "305" | "306":
                        pass
                    case "328":
                        self.handle_328(tokens)

                    case "332" | "333" | "TOPIC":
                        self.handle_topic(tokens)
                        got_topic += 1
                        if not self.use_auto_join:
                            reset_timer("%")

                    case "353":  # NAMES list
                        self.handle_names_list(tokens)
                        if not self.use_auto_join:
                            reset_timer("&")
                                
                    case "366":  # End of NAMES list
                        self.handle_end_of_names_list(tokens)
                        count_366 += 1
                        if not self.use_auto_join:
                            reset_timer("@")

                        elif self.use_auto_join:
                            if count_366 >= len(self.joined_channels) and got_topic >= len(self.joined_channels) and znc_connected:
                                return

                    case "250":
                        self.handle_connection_info(tokens)

                    case "266":
                        self.handle_global_users_info(tokens)

                    case "433":
                        await self.handle_nickname_conflict(tokens)

                    case "372":
                        if self.znc_connection:
                            reset_timer("!")
                        self.handle_motd_line(tokens)

                    case "375":
                        if self.znc_connection:
                            reset_timer("!")
                        self.handle_motd_start(tokens)

                    case "376":
                        self.handle_motd_end(tokens)
                        motd_received = True
                        if not self.use_nickserv_auth and not self.sasl_enabled and not self.znc_connection:
                            if self.use_auto_join:
                                await self.automatic_join()
                                return
                            elif not self.use_auto_join:
                                return
                        elif self.znc_connection and self.isupport_flag and not self.sasl_enabled and not self.use_nickserv_auth:
                            if self.use_auto_join:
                                await self.automatic_join()
                                znc_connected = True
                                reset_timer("!")
                            elif not self.use_auto_join:
                                znc_connected = True
                                reset_timer("!")
                        elif sasl_authenticated and self.isupport_flag and not self.znc_connection:
                            if self.use_auto_join:
                                await self.automatic_join()
                                return
                            elif not self.use_auto_join:
                                return
                        elif self.use_nickserv_auth and not self.sasl_enabled and not self.znc_connection:
                            await self.send_message(f'PRIVMSG NickServ :IDENTIFY {self.nickname} {self.nickserv_password}\r\n')
                            self.gui.insert_text_widget(f"Sent NickServ authentication.\n")
                            nickserv_sent = True

                    case "PING":
                        await self.initial_ping(tokens)

                    case "900":
                        logged_in = True
                        if self.use_nickserv_auth and logged_in and nickserv_sent and not self.sasl_enabled:
                            if self.use_auto_join:
                                await self.automatic_join()
                                return
                            elif not self.use_auto_join:
                                return

                    case "396":
                        got_396 = True

                    case _:
                        input_line = f"_await_welcome_message: {line}"
                        self.save_error(tokens, input_line)
                        self.gui.insert_and_scroll()
                if check_timeout():
                    # Timeout occurred
                    if self.znc_connection:
                        await insert_processing_symbols(PRIVMSGTOKENS)
                        await asyncio.sleep(0.000001)
                        return

            # Check for overall timeout
            elapsed_time = asyncio.get_event_loop().time() - start_time
            if elapsed_time > MAX_WAIT_TIME:
                if self.znc_connection:
                    self.gui.insert_text_widget("\nMaximum sync time exceeded\n")
                    await insert_processing_symbols(PRIVMSGTOKENS)
                    await asyncio.sleep(0.000001)
                    return
                else:
                    gui.insert_text_widget("\nMaximum sync time exceeded\n")
                    return

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
        except AttributeError as e:
            pass
        except (BrokenPipeError, TimeoutError) as e:
            print("Connection lost or timeout while sending message.")
            self.loop_running = False
            await self.reconnect(self.config)
        except Exception as e:
            print(f"Exception in send_message: {e}")

    def is_valid_channel(self, channel):
        return any(channel.startswith(prefix) for prefix in self.chantypes)

    async def join_channel(self, channel):
        if not self.is_valid_channel(channel):
            self.gui.insert_text_widget(f"Invalid channel name {channel}.\n")
            return

        if len(channel) >= self.channellen:
            self.gui.insert_text_widget(f"Maximum Channel Character Limit Reached, Max Allowed: {self.channellen}")
            return

        if len(self.joined_channels) >= self.chan_limit:
            self.gui.insert_text_widget(f"You have reached the maximum number of channels allowed.\n")
            return

        if channel in self.joined_channels:
            self.gui.insert_text_widget(f"You are already in channel {channel}.\n")
            return

        # Ensure the server entry exists in the dictionary
        if self.server not in self.channel_messages:
            self.channel_messages[self.server] = {}

        # Ensure the channel entry exists in the dictionary
        if channel not in self.channel_messages[self.server]:
            self.channel_messages[self.server][channel] = []

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

    async def detach_channel(self, channel):
        if channel in self.joined_channels:
            self.detached_channels.append(channel)
            self.joined_channels.remove(channel)
            
            # Remove the channel entry from the highlighted_channels dictionary
            if self.server_name in self.highlighted_channels:
                self.highlighted_channels[self.server_name].pop(channel, None)

            self.gui.channel_lists[self.server] = self.joined_channels
            self.update_gui_channel_list()
            self.gui.insert_text_widget(f"You have \x02DETACHED\x0F from \x02{channel}\x0F\n")
            self.gui.insert_text_widget(f"To \x02REATTACH\x0F simply issue a normal /join \x02{channel}\x0F\n")

    def update_gui_channel_list(self):
        # Clear existing items
        self.gui.channel_listbox.delete(0, tk.END)

        for chan in self.joined_channels:
            if chan not in self.gui.popped_out_channels:
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
                        bg_color = highlighted_info.get('bg', self.mention_note_color)
                        self.gui.channel_listbox.itemconfig(new_index, {'bg': bg_color})

                        # Update the dictionary with the new index
                        updated_highlighted_channels[channel] = highlighted_info

        # Update the highlighted_channels dictionary with the new indexes
        self.highlighted_channels[self.server_name] = updated_highlighted_channels
        self.gui.scroll_channel_list()

    def update_gui_user_list(self, channel):
        self.gui.user_listbox.delete(0, tk.END)
        for user in self.channel_users.get(channel, []):
            self.gui.user_listbox.insert(tk.END, user)

    async def reset_state(self):
        self.motd_dict.clear()
        self.joined_channels.clear()
        self.motd_lines.clear()
        self.channel_users.clear()
        self.user_modes.clear()
        self.mode_to_symbol.clear()
        self.whois_data.clear()
        self.download_channel_list.clear()
        self.whois_executed.clear()

    async def stop_tasks(self, tasks_dict=None):
        if tasks_dict is None:
            tasks_dict = self.tasks

        # Create a list to store tasks that are not done
        not_done_tasks = []

        # Check if each task is done or not, and cancel only if it's not done
        for task_name, task in tasks_dict.items():
            if not task.done():
                not_done_tasks.append(task)
                task.cancel()

        # Wait for only the not done tasks to be canceled
        await asyncio.gather(*not_done_tasks, return_exceptions=True)

    def grab_server_name(self, config_file):
        if sys.platform.startswith('win'):
            split_config = config_file.split("\\")
            server = split_config[-1].split(".")
            return server[1]
        else:
            split_config = config_file.split("/")
            server = split_config[-1].split(".")
            return server[1]

    async def reconnect(self, config_file):
        disconnected_server = self.grab_server_name(config_file)
        MAX_RETRIES = 5
        if self.znc_connection:
            RETRY_DELAY = 1
        else:
            RETRY_DELAY = 245
        retries = 0
        self.add_server_message(f"****Resetting State\n")
        await self.reset_state()
        self.gui.insert_text_widget(f"You have been \x0304DISCONNECTED\x0F Auto Reconnecting In Progress\x0303... in 245seconds\x0F \n")
        self.add_server_message(f"You have been \x0304DISCONNECTED\x0F Auto Reconnecting In Progress\x0303... in 245seconds\x0F \n")
        while retries < MAX_RETRIES:
            retries += 1
            try:
                self.add_server_message(f"****Server {disconnected_server} Disconnected\n")
                self.add_server_message(f"****Giving Time For Ping TimeOut: {RETRY_DELAY}seconds\n")
                await asyncio.sleep(RETRY_DELAY)

                self.add_server_message("****Attempt Connection\n")
                await self.connect(config_file)
                self.loop_running = True
                self.add_server_message(f"****Connected: {self.loop_running}\n")
                return 
                    
            except Exception as e:
                print(f"Failed to reconnect ({retries}/{MAX_RETRIES}): {e}. Retrying in {RETRY_DELAY} seconds.")
                await asyncio.sleep(RETRY_DELAY)

        print(f"Failed to reconnect ({retries}/{MAX_RETRIES}): {e}. Retrying in {RETRY_DELAY} seconds.")

    async def keep_alive(self, config_file):
        while self.loop_running:
            try:
                # Measure ping time before sending PING
                self.ping_start_time = time.time()

                await asyncio.sleep(194)
                await self.send_message(f'PING {self.server}')

            except asyncio.CancelledError:
                # If the event loop is stopped, break out of the loop
                self.loop_running = False
                print("Exiting keep_alive loop.")

            except (ConnectionResetError, OSError) as e:
                print(f"Connection Exception caught in keep_alive: {e}")
                self.loop_running = False
                await self.reconnect(config_file)

            except AttributeError as e:
                print(f"AttributeError caught in keep_alive: {e}")

            except Exception as e:
                print(f"Unhandled exception in keep_alive: {e}")

    async def auto_save(self):
        while self.loop_running:
            try:
                await asyncio.sleep(30)
                await self.save_channel_messages()

            except asyncio.CancelledError:
                self.loop_running = False
                print("Exiting auto_save loop.")

            except (ConnectionResetError, OSError) as e:
                print(f"Exception caught in auto_save: {e}")
                self.loop_running = False

            except AttributeError as e:  # Catch AttributeError
                print(f"AttributeError caught in auto_save: {e}")

            except Exception as e:  # Catch other exceptions
                print(f"Unhandled exception in auto_save: {e}")

    async def auto_trim(self):
        while self.loop_running:
            try:
                await asyncio.sleep(125)
                self.trim_messages()

            except asyncio.CancelledError:
                self.loop_running = False
                print("Exiting auto_trim loop.")

            except (ConnectionResetError, OSError) as e:
                print(f"Exception caught in auto_trim: {e}")
                self.loop_running = False

            except AttributeError as e:  # Catch AttributeError
                print(f"AttributeError caught in auto_trim: {e}")

            except Exception as e:  # Catch other exceptions
                print(f"Unhandled exception in auto_trim: {e}")

    def handle_server_message(self, line):
        data = line + "\n"
        self.add_server_message(data)

    def handle_notice_message(self, tokens):
        sender = tokens.hostmask if tokens.hostmask else "Server"
        target = tokens.params[0]
        message = tokens.params[1]
        data = f"NOTICE {sender} {target}: {message}\n"
        if self.znc_connection and target not in self.gui.popped_out_channels:
            self.gui.insert_text_widget(f"{data}")
            self.add_server_message(data)
        elif self.znc_connection and target in self.gui.popped_out_channels:
            self.pipe_mode_to_pop_out(message, target)
            self.add_server_message(data)
        else:
            self.add_server_message(data)

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
                case "VERSION" | "version":
                    if tokens.command == "PRIVMSG":
                        await self.send_message(f'NOTICE {sender} :\x01VERSION RudeChat3.0.4\x01')
                        self.add_server_message(f"CTCP: {sender} {target}: {ctcp_command}\n")
                case "MOO" | "moo":
                    if tokens.command == "PRIVMSG":
                        await self.send_message(f'NOTICE {sender} :\x01MoooOOO! Hi Cow!! RudeChat3.0.4\x01')
                        self.add_server_message(f"CTCP: {sender} {target}: {ctcp_command}\n")
                case "PING" | "ping":
                    if tokens.command == "PRIVMSG":
                        timestamp = str(int(time.time()))  # Get the current Unix timestamp
                        await self.send_message(f'NOTICE {sender} :\x01PING {ctcp_content} {timestamp}\x01')
                        self.add_server_message(f"CTCP: {sender} {target}: {ctcp_command}\n")
                case "FINGER" | "finger":
                    if tokens.command == "PRIVMSG":
                        await self.send_message(f'NOTICE {sender} :\x01FINGER: {self.nickname} {self.server_name} RudeChat3.0.4\x01')
                        self.add_server_message(f"CTCP: {sender} {target}: {ctcp_command}\n")
                case "CLIENTINFO" | "clientinfo":
                    if tokens.command == "PRIVMSG":
                        await self.send_message(f'NOTICE {sender} :\x01CLIENTINFO VERSION TIME PING FINGER\x01')
                        self.add_server_message(f"CTCP: {sender} {target}: {ctcp_command}\n")
                case "TIME" | "time":
                    if tokens.command == "PRIVMSG":
                        tz = pytz.timezone(str(self.time_zone))
                        local_time = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
                        time_reply = "\x01TIME " + local_time + "\x01"
                        await self.send_message(f'NOTICE {sender} :{time_reply}')
                        self.add_server_message(f"CTCP: {sender} {target}: {ctcp_command}\n")
                case "ACTION":
                    await self.handle_action_ctcp(timestamp, sender, target, ctcp_content)
                case _:
                    print(f"Unhandled CTCP command: {ctcp_command}")

    def add_server_message(self, data):
        if not self.gui.show_server_window:
            if self.server_name in self.motd_dict:
                self.motd_dict[self.server_name] += data
                self.highlight_server(server_activity=True)
            else:
                self.motd_dict[self.server_name] = data
                self.highlight_server(server_activity=True)
        else:
            self.gui.insert_server_widget(data)

    async def handle_action_ctcp(self, timestamp, sender, target, ctcp_content):
        try:
            if self.use_time_stamp == True:
                action_message = f"{timestamp}* {sender} {ctcp_content}\n"
            elif self.use_time_stamp == False:
                action_message = f"* {sender} {ctcp_content}\n"

            # Update the message history
            if self.server not in self.channel_messages:
                self.channel_messages[self.server] = {}
            if target not in self.channel_messages[self.server]:
                self.channel_messages[self.server][target] = []

            self.channel_messages[self.server][target].append(action_message)

            # Display the message in the text_widget if the target matches the current channel or DM
            if target == self.current_channel and self.gui.irc_client == self and target not in self.gui.popped_out_channels:
                self.gui.insert_text_widget(action_message)
                self.gui.highlight_nickname()
            if target in self.gui.popped_out_channels:
                window = self.gui.pop_out_windows[target]
                window.insert_text(action_message)
                window.highlight_nickname()
            else:
                # If it's not the currently viewed channel, highlight the channel in green in the Listbox
                for idx in range(self.gui.channel_listbox.size()):
                    if self.gui.channel_listbox.get(idx) == target:
                        current_bg = self.gui.channel_listbox.itemcget(idx, 'bg')
                        if current_bg != 'red':
                            self.gui.channel_listbox.itemconfig(idx, {'bg':self.activity_note_color})
                        break
        except Exception as e:
            print(f"Exception in handle_action_ctcp: {e}")

    def trim_messages(self):
        for server, channels in self.channel_messages.items():
            for channel, messages in channels.items():
                # Trim the message history to the last 150 messages
                channels[channel] = messages[-125:]

    async def notify_user_of_mention(self, server, channel, sender, message):
        notification_msg = f"<{sender}> {message}"

        # Highlight the mentioned channel in the channel_listbox if it's not selected
        if (channel != self.current_channel) or (sender != self.current_channel):
            self.highlight_channel(channel)

        # Highlight the server in the server_listbox if it's not selected
        self.highlight_server()

        # Play the beep sound/notification
        if self.use_beep_noise == True:
            await self.trigger_beep_notification(channel_name=channel, message_content=notification_msg)

    def highlight_channel(self, channel):
        try:
            # Ensure the channel is part of the joined_channels before highlighting
            if channel in self.joined_channels and self.gui.irc_client == self:
                if channel != self.current_channel:
                    # Find and highlight the channel in the GUI listbox
                    for idx in range(self.gui.channel_listbox.size()):
                        if self.gui.channel_listbox.get(idx) == channel:
                            self.gui.channel_listbox.itemconfig(idx, {'bg': self.mention_note_color})
                            break
            else:
                pass
        except Exception as e:
            print(f"Exception in highlighted_channel: {e}")

    def highlight_server(self, server_activity=False):
        try:
            for idx in range(self.gui.server_listbox.size()):
                if self.gui.server_listbox.get(idx) == self.server_name and self.gui.irc_client != self:
                    self.gui.server_listbox.itemconfig(idx, {'bg': self.mention_note_color})
                    # Store the highlighted server information with red background
                    self.highlighted_servers[self.server_name] = {'index': idx, 'bg': self.mention_note_color}
                    break
                elif self.gui.server_listbox.get(idx) == self.server_name and server_activity == True:
                    self.gui.server_listbox.itemconfig(idx, {'bg': self.activity_note_color})
                    # Store the highlighted server information with green background
                    self.highlighted_servers[self.server_name] = {'index': idx, 'bg': self.activity_note_color}
                    break
        except Exception as e:
            print(f"Exception in highlight_server: {e}")

    async def trigger_beep_notification(self, channel_name=None, message_content=None):
        """
        You've been pinged! Plays a beep or noise on mention.
        """
        script_directory = os.path.dirname(os.path.abspath(__file__))
        try:
            if sys.platform.startswith("linux"):
                # Check if paplay is available
                if self.custom_sounds:
                    if shutil.which("paplay"):
                        # Linux-specific notification sound using paplay
                        sound_path = os.path.join(script_directory, "Sounds", "Notification4.wav")
                        os.system(f"paplay {sound_path}")
                elif not self.custom_sounds:
                    # System bell beep
                    os.system("echo -e '\a'")
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

            self.gui.trigger_desktop_notification(channel_name, message_content=message_content)
        except Exception as e:
            print(f"Error triggering desktop notification: {e}")

    async def handle_privmsg(self, tokens, znc_privmsg=False):
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
        sender = tokens.hostmask.nickname
        target = tokens.params[0]
        message = tokens.params[1]

        sender_hostmask = str(tokens.hostmask)
        user_mode = self.get_user_mode(sender, target)
        mode_symbol = self.get_mode_symbol(user_mode) if user_mode else ''
        if self.should_ignore_sender(sender_hostmask):
            return

        if self.is_ctcp_command(message):
            await self.handle_ctcp(tokens)
            return

        if self.is_direct_message(target):
            target = await self.get_direct_message_target(sender, target)
            await self.prepare_direct_message(sender, target, message, timestamp, mode_symbol, znc_privmsg)
        else:
            await self.handle_channel_message(sender, target, message, timestamp, mode_symbol, znc_privmsg)

        await self.notify_user_if_mentioned(message, target, sender, timestamp)

    def should_ignore_sender(self, sender_hostmask):
        return any(fnmatch.fnmatch(sender_hostmask, ignored) for ignored in self.ignore_list)

    async def notify_user_if_mentioned(self, message, target, sender, timestamp):
        # Compile a regex pattern to match the exact nickname
        pattern = re.compile(r'\b' + re.escape(self.nickname) + r'\b', re.IGNORECASE)
        
        # Check if the exact nickname is mentioned in the message
        if pattern.search(message):
            await self.notify_user_of_mention(self.server, target, sender, message)

            if self.znc_connection:
                if target != self.nickname and (target in self.detached_channels or 
                                                 (target not in self.joined_channels and target not in self.detached_channels)):
                    await self.auto_attach(target)

            self.mentions.setdefault(target, []).append(f'{timestamp} <{sender}> {message}')

    async def auto_attach(self, channel):
        try:
            self.joined_channels.append(channel)
            self.gui.channel_lists[self.server] = self.joined_channels
            self.update_gui_channel_list()

            self.highlight_channel(channel)

            channel_idx = self.joined_channels.index(channel)
            self.save_highlight(channel, channel_idx, is_mention=True)
            await self.send_message(f"NAMES {channel}")
            await self.send_message(f"TOPIC {channel}")
        except Exception as e:
            print(f"Exception in auto_attach: {e}")

    def is_ctcp_command(self, message):
        return message.startswith('\x01') and message.endswith('\x01')

    def is_direct_message(self, target):
        return target == self.nickname

    async def get_direct_message_target(self, sender, target):
        if self.auto_whois == True:
            if sender not in self.whois_executed:
                await self.send_message(f'WHOIS {sender}')
                self.whois_executed.add(sender)
            return target
        else:
            return target

    async def prepare_direct_message(self, sender, target, message, timestamp, mode_symbol, znc_privmsg):
        self.log_message(self.server_name, target, sender, message, is_sent=False)
        try:
            if sender != self.nickname:
                self.channel_messages.setdefault(self.server, {}).setdefault(sender, [])

                if self.is_direct_message(target) and sender not in self.joined_channels:
                    self.joined_channels.append(sender)
                    self.gui.channel_lists[self.server] = self.joined_channels
                    self.update_gui_channel_list()

                if znc_privmsg:
                    self.save_message(self.server, target, sender, message, mode_symbol, is_sent=False)
                    user_mention = self.is_it_a_mention(message)
                    if not user_mention:
                        await self.trigger_beep_notification(channel_name=sender, message_content=f"Message From {sender}")
                        self.highlight_channel_if_not_current(target, sender, user_mention)
                    elif user_mention:
                        self.highlight_channel_if_not_current(target, sender, user_mention)
                elif sender != self.current_channel and sender not in self.gui.popped_out_channels:
                    self.save_message(self.server, target, sender, message, mode_symbol, is_sent=False)
                    user_mention = self.is_it_a_mention(message)
                    if not user_mention:
                        await self.trigger_beep_notification(channel_name=sender, message_content=f"Message From {sender}")
                        self.highlight_channel_if_not_current(target, sender, user_mention)
                    elif user_mention:
                        self.highlight_channel_if_not_current(target, sender, user_mention)
                else:
                    self.save_message(self.server, target, sender, message, is_sent=False)

                    if sender not in self.gui.popped_out_channels:
                        self.display_message(timestamp, sender, message, target, mode_symbol, is_direct=True)
                    else:
                        self.pip_to_pop_out(timestamp, sender, message, target, mode_symbol)

        except Exception as e:
            print(f"Exception in prepare_direct_message: {e}")

    def pip_to_pop_out(self, timestamp, sender, message, target, mode_symbol):
        window = self.gui.pop_out_windows.get(target) or self.gui.pop_out_windows.get(sender)
        if window:
            formatted_message = f"{timestamp}<{mode_symbol}{sender}> {message}\n" if self.use_time_stamp else f"<{mode_symbol}{sender}> {message}\n"
            window.insert_text(formatted_message)
            window.highlight_nickname()

    async def handle_channel_message(self, sender, target, message, timestamp, mode_symbol, znc_privmsg):
        if znc_privmsg:
            if self.server not in self.channel_messages:
                self.channel_messages[self.server] = {}
            if target not in self.channel_messages[self.server]:
                self.channel_messages[self.server][target] = []
            self.save_message(self.server, target, sender, message, mode_symbol, is_sent=False)
            self.log_message(self.server_name, target, sender, message, is_sent=False)
            user_mention = self.is_it_a_mention(message)
            if not user_mention:
                self.highlight_channel_if_not_current(target, sender, user_mention)
            elif user_mention:
                self.highlight_channel_if_not_current(target, sender, user_mention)

        elif target != self.current_channel and target not in self.gui.popped_out_channels:
            if self.server not in self.channel_messages:
                self.channel_messages[self.server] = {}
            if target not in self.channel_messages[self.server]:
                self.channel_messages[self.server][target] = []
            self.save_message(self.server, target, sender, message, mode_symbol, is_sent=False)
            self.log_message(self.server_name, target, sender, message, is_sent=False)
            user_mention = self.is_it_a_mention(message)
            if not user_mention:
                self.highlight_channel_if_not_current(target, sender, user_mention)
            elif user_mention:
                self.highlight_channel_if_not_current(target, sender, user_mention)

        else:
            if self.server not in self.channel_messages:
                self.channel_messages[self.server] = {}
            if target not in self.channel_messages[self.server] and target != self.nickname:
                self.channel_messages[self.server][target] = []
            self.save_message(self.server, target, sender, message, mode_symbol, is_sent=False)
            self.log_message(self.server_name, target, sender, message, is_sent=False)

            if target not in self.gui.popped_out_channels:
                self.display_message(timestamp, sender, message, target, mode_symbol, is_direct=False)
            else:
                self.pip_to_pop_out(timestamp, sender, message, target, mode_symbol)

    def save_message(self, server, target, sender, message, mode_symbol, is_sent):
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
        if self.is_direct_message(target):
            # If it's a DM, handle it differently
            if sender not in self.channel_messages[server]:
                self.channel_messages[server][sender] = []  # Create a list for the sender if it doesn't exist
            message_list = self.channel_messages[server][sender]
        else:
            if target not in self.channel_messages[server]:
                self.channel_messages[server][target] = []  # Create a list for the target if it doesn't exist
            message_list = self.channel_messages[server][target]
        # Append the message to the appropriate list
        if self.use_time_stamp == True:
            message_list.append(f"{timestamp}<{mode_symbol}{sender}> {message}\n")
        elif self.use_time_stamp == False:
            message_list.append(f"<{mode_symbol}{sender}> {message}\n")

    def is_it_a_mention(self, message):
        if self.nickname.lower() in message.lower():
            return True
        else:
            return False

    def get_mode_symbol(self, mode):
        """Return the symbol corresponding to the IRC mode."""
        mode_symbols = {
            'o': '@',
            'v': '+',
            'q': '~',
            'a': '&',
            'h': '%',
        }
        return mode_symbols.get(mode, '')

    def get_user_mode(self, user, channel):
        """Retrieve the user's mode for the given channel."""
        channel_modes = self.user_modes.get(channel, {})
        user_modes = channel_modes.get(user, set())
        return next(iter(user_modes), None)  # Get the first mode if available, else None

    def display_message(self, timestamp, sender, message, target, mode_symbol, is_direct=False):
        if target == self.current_channel and self.gui.irc_client == self:
            if self.use_time_stamp:
                self.gui.insert_text_widget(f"{timestamp}<{mode_symbol}{sender}> {message}\n")
            else:
                self.gui.insert_text_widget(f"<{mode_symbol}{sender}> {message}\n")
            self.gui.highlight_nickname()
        elif sender == self.current_channel and self.gui.irc_client == self:
            if is_direct:
                if self.use_time_stamp:
                    self.gui.insert_text_widget(f"{timestamp}<{sender}> {message}\n")
                else:
                    self.gui.insert_text_widget(f"<{sender}> {message}\n")
                self.gui.highlight_nickname()
        else:
            user_mention = self.is_it_a_mention(message)
            if not user_mention:
                self.highlight_channel_if_not_current(target, sender, user_mention)
            else:
                self.highlight_channel_if_not_current(target, sender, user_mention)

    def highlight_channel_if_not_current(self, target, sender, user_mention):
        highlighted_channel = target
        if self.is_direct_message(target):
            highlighted_channel = sender

        # Find the channel's index in joined_channels, if it exists
        if highlighted_channel in self.joined_channels and user_mention == False:
            channel_idx = self.joined_channels.index(highlighted_channel)
            self.save_highlight(highlighted_channel, channel_idx, is_mention=False)
            self._highlight_channel_by_name(highlighted_channel, channel_idx)
        elif highlighted_channel in self.joined_channels and user_mention == True:
            channel_idx = self.joined_channels.index(highlighted_channel)
            self.highlight_channel(highlighted_channel)
            self.save_highlight(highlighted_channel, channel_idx, is_mention=True)

    def _highlight_channel_by_name(self, highlighted_channel, joined_idx):
        # Attempt to find the channel in the GUI listbox and highlight it
        if self.gui.irc_client == self:
            if highlighted_channel != self.current_channel:
                for idx in range(self.gui.channel_listbox.size()):
                    if self.gui.channel_listbox.get(idx) == highlighted_channel:
                        current_bg = self.gui.channel_listbox.itemcget(idx, 'bg')
                        if current_bg != 'red':
                            self.gui.channel_listbox.itemconfig(idx, {'bg': self.activity_note_color})
                        break

    def save_highlight(self, channel, joined_index, is_mention):
        # Initialize highlighted_channels for server_name if not already done
        try:
            if self.server_name not in self.highlighted_channels:
                self.highlighted_channels[self.server_name] = {}

            current_highlight = self.highlighted_channels[self.server_name].get(channel)

            if is_mention and self.gui.irc_client == self:
                self.highlighted_channels[self.server_name][channel] = {'index': joined_index, 'bg': self.mention_note_color}
            elif is_mention and self.gui.irc_client != self:
                self.highlighted_channels[self.server_name][channel] = {'index': joined_index, 'bg': self.mention_note_color}
            else:
                if not current_highlight and is_mention == False:
                    self.highlighted_channels[self.server_name][channel] = {'index': joined_index, 'bg': self.activity_note_color}
                elif current_highlight['bg'] != 'red':
                    self.highlighted_channels[self.server_name][channel] = {'index': joined_index, 'bg': self.activity_note_color}
        except Exception as e:
            print(f"Exception in save_highlight: {e}")

    def handle_join(self, tokens): #add options to show or hide these messages. 
        user_info = tokens.hostmask.nickname
        user_mask = tokens.hostmask
        channel = tokens.params[0]
        if self.show_full_hostmask == True:
            join_message = f"\x0312(&)\x0F {user_mask} has joined channel {channel}\n"
        elif self.show_full_hostmask == False:
            join_message = f"\x0312(&)\x0F {user_info} has joined channel {channel}\n"

        # Update the message history for the channel
        if self.server not in self.channel_messages:
            self.channel_messages[self.server] = {}
        if channel not in self.channel_messages[self.server]:
            self.channel_messages[self.server][channel] = []

        if self.show_join_part_quit_nick:
            self.channel_messages[self.server][channel].append(join_message)

        # Display the message in the text_widget only if the channel matches the current channel
        if channel == self.current_channel and self.gui.irc_client == self and channel not in self.gui.popped_out_channels:
            if self.show_join_part_quit_nick:
                self.gui.insert_text_widget(join_message)
                self.gui.highlight_nickname()
        if channel in self.gui.popped_out_channels:
            if self.show_join_part_quit_nick:
                self.pipe_mode_to_pop_out(join_message, channel)

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

    def handle_part(self, tokens):
        user_info = tokens.hostmask.nickname
        user_mask = tokens.hostmask
        channel = tokens.params[0]
        if self.show_full_hostmask == True:
            part_message = f"\x0304(X)\x0F {user_mask} has parted from channel {channel}\n"
        elif self.show_full_hostmask == False:
            part_message = f"\x0304(X)\x0F {user_info} has parted from channel {channel}\n"

        # Update the message history for the channel
        if self.server not in self.channel_messages:
            self.channel_messages[self.server] = {}
        if channel not in self.channel_messages[self.server]:
            self.channel_messages[self.server][channel] = []

        if self.show_join_part_quit_nick:
            self.channel_messages[self.server][channel].append(part_message)

        # Display the message in the text_widget only if the channel matches the current channel
        if channel == self.current_channel and self.gui.irc_client == self and channel not in self.gui.popped_out_channels:
            if self.show_join_part_quit_nick:
                self.gui.insert_text_widget(part_message)
                self.gui.highlight_nickname()
        if channel in self.gui.popped_out_channels:
            if self.show_join_part_quit_nick:
                self.pipe_mode_to_pop_out(part_message, channel)

        # Check if the user is in the channel_users list for the channel
        user_found = False
        for user_with_symbol in self.channel_users.get(channel, []):
            # Check if the stripped user matches user_info
            if user_with_symbol.lstrip('~&@%+') == user_info:
                user_found = True
                self.channel_users[channel].remove(user_with_symbol)
                break

        if user_found:
            # Update the user listbox for the channel
            self.update_user_listbox(channel)
        else:
            print(f"{user_info} User not found.")
            pass

    def handle_quit(self, tokens):
        user_info = tokens.hostmask.nickname
        user_mask = tokens.hostmask
        reason = tokens.params[0] if tokens.params else "No reason"
        if self.show_full_hostmask == True:
            quit_message = f"\x0304(X)\x0F {user_mask} has quit: {reason}\n"
        elif self.show_full_hostmask == False:
            quit_message = f"\x0304(X)\x0F {user_info} has quit: {reason}\n"

        # Remove the user from all channel_users lists
        for channel, users in self.channel_users.items():
            user_found = False
            for idx, user_with_symbol in enumerate(users):
                # Check if the stripped user matches user_info
                if user_with_symbol.lstrip('~&@%+') == user_info:
                    user_found = True
                    del self.channel_users[channel][idx]
                    
                    # Update the message history for the channel
                    if self.server not in self.channel_messages:
                        self.channel_messages[self.server] = {}
                    if channel not in self.channel_messages[self.server]:
                        self.channel_messages[self.server][channel] = []
                    if self.show_join_part_quit_nick:
                        self.channel_messages[self.server][channel].append(quit_message)

                    # Display the message in the text_widget only if the channel matches the current channel
                    if channel == self.current_channel and self.gui.irc_client == self and channel not in self.gui.popped_out_channels:
                        if self.show_join_part_quit_nick:
                            self.gui.insert_text_widget(quit_message)
                            self.gui.highlight_nickname()
                    if channel in self.gui.popped_out_channels:
                        if self.show_join_part_quit_nick:
                            self.pipe_mode_to_pop_out(quit_message, channel)

                    break

            if user_found:
                # Update the user listbox for the channel
                self.update_user_listbox(channel)

    async def handle_nick(self, tokens):
        old_nick = tokens.hostmask.nickname
        new_nick = tokens.params[0]
        message = f"\x0307(@)\x0F {old_nick} has changed their nickname to {new_nick}\n"

        # Update the user's nick in all channel_users lists they are part of
        for channel, users in self.channel_users.items():
            for idx, user_with_symbol in enumerate(users):
                # Check if the stripped user matches old_nick
                if user_with_symbol.lstrip('~&@%+') == old_nick:
                    # Extract the mode symbols from the old nickname
                    mode_symbols = ''.join([c for c in user_with_symbol if c in '~&@%+'])
                    
                    # Replace old_nick with new_nick, retaining the mode symbols
                    users[idx] = mode_symbols + new_nick
                    
                    # Update the user listbox for the channel if necessary
                    self.update_user_listbox(channel)

                    # Display the nick change message in the channel
                    if self.server not in self.channel_messages:
                        self.channel_messages[self.server] = {}
                    if channel not in self.channel_messages[self.server]:
                        self.channel_messages[self.server][channel] = []
                    if self.show_join_part_quit_nick:
                        self.channel_messages[self.server][channel].append(f"\x0307(@)\x0F {old_nick} has changed their nickname to {new_nick}\n")
                    
                    # Insert message into the text widget only if this is the current channel
                    if channel == self.current_channel and self.gui.irc_client == self and channel not in self.gui.popped_out_channels:
                        if self.show_join_part_quit_nick:
                            self.gui.insert_text_widget(message)
                            self.gui.highlight_nickname()
                    if channel in self.gui.popped_out_channels:
                        if self.show_join_part_quit_nick:
                            self.pipe_mode_to_pop_out(message, channel)

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
            key=lambda x: (mode_priority.index(next((m for m, s in self.mode_to_symbol.items() if s == x[0]), None)) if x and x[0] in self.mode_to_symbol.values() else len(mode_priority),x,))


        # Update the user modes dictionary and the channel_users list
        self.user_modes[channel] = current_modes
        self.channel_users[channel] = sorted_users
        return sorted_users

    def handle_mode(self, tokens):
        channel = tokens.params[0]
        mode_changes = tokens.params[1]
        users = tokens.params[2:] if len(tokens.params) > 2 else []
        
        user_index = 0
        adding = None

        for mode_change in mode_changes:
            if mode_change in '+-':
                adding = mode_change == '+'
                continue

            mode = mode_change
            user = users[user_index] if user_index < len(users) else None
            stripped_mode = mode.lstrip('+-')

            if adding is None:
                continue

            current_modes = self.user_modes.get(channel, {})

            if adding:
                if stripped_mode in self.chanmodes.get('no_parameter', []) or stripped_mode in self.chanmodes.get('parameter', []):
                    message = f"\x0304(!)\x0F +{mode} mode for {channel}\n"
                    self._log_channel_message(channel, message)
                    continue

                if stripped_mode in self.chanmodes.get('list', []):
                    message = f"\x0304(!)\x0F +{mode} mode for {user if user else 'unknown'}\n"
                    self._log_channel_message(channel, message)
                    continue

                if stripped_mode in self.chanmodes.get('setting', []):
                    message = f"\x0304(!)\x0F +{mode} {user} set for {channel}\n"
                    self._log_channel_message(channel, message)
                    continue

                current_modes.setdefault(user, set()).add(mode)
                message = f"\x0303(+)\x0F {user} has been given mode +{mode}\n"
                self._log_channel_message(channel, message)
                user_index += 1

            else:
                if stripped_mode in self.chanmodes.get('no_parameter', []) or stripped_mode in self.chanmodes.get('parameter', []):
                    message = f"\x0312(&)\x0F -{mode} mode for {channel}\n"
                    self._log_channel_message(channel, message)
                    continue

                if stripped_mode in self.chanmodes.get('list', []):
                    message = f"\x0312(&)\x0F -{mode} mode for {user if user else 'unknown'}\n"
                    self._log_channel_message(channel, message)
                    continue

                if stripped_mode in self.chanmodes.get('setting', []):
                    message = f"\x0312(&)\x0F -{mode} {user} set for {channel}\n"
                    self._log_channel_message(channel, message)
                    continue

                if mode in self.mode_to_symbol:
                    symbol_to_remove = self.mode_to_symbol[mode]
                    self.channel_users[channel] = [
                        u.replace(symbol_to_remove, '') if u.endswith(user) else u
                        for u in self.channel_users.get(channel, [])
                    ]

                user_modes = current_modes.get(user, set())
                user_modes.discard(mode)

                message = f"\x0304(-)\x0F {user} has had mode +{mode} removed\n"
                self._log_channel_message(channel, message)

                if not user_modes:
                    if user in current_modes:
                        del current_modes[user]
                    else:
                        print(f"User {user} not found in current modes. Adding with no modes.")
                        user_modes = set()
                        if '@' in user:
                            user_modes.add('o')
                        if '+' in user:
                            user_modes.add('v')
                        if '~' in user:
                            user_modes.add('q')
                        if '&' in user:
                            user_modes.add('a')
                        if '%' in user:
                            user_modes.add('h')
                        current_modes[user] = user_modes
                else:
                    current_modes[user] = user_modes

                self.user_modes[channel] = current_modes
                user_index += 1

            sorted_users = self.sort_users(self.channel_users.get(channel, []), channel)
            self.channel_users[channel] = sorted_users
            self.update_user_listbox(channel)
        return 

    def pipe_mode_to_pop_out(self, message, target):
        if target in self.gui.pop_out_windows:
            try:
                window = self.gui.pop_out_windows[target]
                formatted_message = f"{message}"
                window.insert_text(formatted_message)
                window.highlight_nickname()
                return
            except Exception as e:
                print(f"Exception in pipe_mode_to_pop_out: {e}")

    def _log_channel_message(self, channel, message):
        if channel != self.nickname:
            if channel == self.current_channel and self.gui.irc_client == self:
                if channel not in self.gui.popped_out_channels:
                    self.gui.insert_text_widget(f"{message}")
                    self.gui.highlight_nickname()
            if channel in self.gui.popped_out_channels:
                self.pipe_mode_to_pop_out(message, channel)
            if self.server not in self.channel_messages:
                self.channel_messages[self.server] = {}
            if channel not in self.channel_messages[self.server]:
                self.channel_messages[self.server][channel] = []
            self.channel_messages[self.server][channel].append(message)

    def update_user_listbox(self, channel):
        current_users = self.channel_users.get(channel, [])
        sorted_users = self.sort_users(current_users, channel)
        
        # Remove duplicates from the sorted_users list
        unique_users = list(dict.fromkeys(sorted_users))
        
        # Only update the user listbox if the channel is the currently selected channel
        if channel == self.current_channel and self.gui.irc_client == self and channel not in self.gui.popped_out_channels:
            # Update the Tkinter Listbox to reflect the current users in the channel
            self.gui.user_listbox.delete(0, tk.END)  # Clear existing items
            for user in unique_users:
                self.gui.user_listbox.insert(tk.END, user)
        
        if channel in self.gui.popped_out_channels:
            window = self.gui.pop_out_windows[channel]
            window.update_gui_user_list(channel)
                       
    def handle_isupport(self, tokens):
        params = tokens.params[:-1]  # Exclude the trailing "are supported by this server" message
        isupport_message = " ".join(params)

        data = f"ISUPPORT: {isupport_message}\n"
        self.add_server_message(data)

        # Parse ISUPPORT parameters
        for param in params:
            if param.startswith("PREFIX="):
                _, mappings = param.split("=")
                modes, symbols = mappings[1:].split(")")
                self.mode_to_symbol = dict(zip(modes, symbols))
            elif param.startswith("CHANTYPES="):
                _, channel_types = param.split("=")
                self.chantypes = channel_types
            elif param.startswith("NICKLEN="):
                _, nick_len = param.split("=")
                self.nicknamelen = int(nick_len)
            elif param.startswith("CHANLIMIT="):
                _, chan_limit = param.split("=")
                self.chan_limit = int(chan_limit.split(":")[1])
            elif param.startswith("CHANNELLEN="):
                _, channel_len = param.split("=")
                self.channellen = int(channel_len)
            elif param.startswith("TOPICLEN="):
                _, topic_len = param.split("=")
                self.topiclen = int(topic_len)
            elif param.startswith("CHANMODES="):
                _, chan_modes = param.split("=")
                mode_categories = chan_modes.split(',')
                self.chanmodes = {
                    'list': list(mode_categories[0]),
                    'parameter': list(mode_categories[1]),
                    'setting': list(mode_categories[2]),
                    'no_parameter': list(mode_categories[3])
                }

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

                    self.whois_display(whois_response)
                    await self.save_whois_to_file(nickname)

    def whois_display(self, whois_response):
        try:
            whois_channel = "&WHOIS&"
            if whois_channel not in self.joined_channels:
                self.joined_channels.append(whois_channel)
                self.gui.channel_lists[self.server] = self.joined_channels
                self.update_gui_channel_list()

            # Add data to the channel history
            if whois_channel not in self.channel_messages[self.server]:
                self.channel_messages[self.server][whois_channel] = [] 
            self.channel_messages[self.server][whois_channel].append(f"{whois_response}\n")

            # Update the GUI
            self.gui.insert_and_scroll()
        except Exception as e:
            print(f"Exception in help: {e}")

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
        if self.server not in self.channel_messages:
            self.channel_messages[self.server] = {}
        if channel not in self.channel_messages[self.server]:
            self.channel_messages[self.server][channel] = []

        # Display the kick message in the chat window only if the channel is the current channel
        kick_message_content = f"<X> {kicked_nickname} has been kicked from {channel} by {tokens.hostmask.nickname} ({reason})\n"
        self.channel_messages[self.server][channel].append(kick_message_content)

        if channel == self.current_channel and self.gui.irc_client == self and channel not in self.gui.popped_out_channels:
            self.gui.insert_text_widget(kick_message_content)
            self.gui.highlight_nickname()
        if channel in self.gui.popped_out_channels:
            self.pipe_mode_to_pop_out(kick_message_content, channel)

        # Remove the user from the channel_users list for the channel
        user_found = False
        for user_with_symbol in self.channel_users.get(channel, []):
            # Check if the stripped user matches kicked_nickname
            if user_with_symbol.lstrip('~&@%+') == kicked_nickname:
                user_found = True
                self.channel_users[channel].remove(user_with_symbol)
                break

        if user_found:
            # Update the user listbox for the channel
            self.update_user_listbox(channel)

        if kicked_nickname == self.nickname:
            try:
                if self.auto_rejoin:
                    await self.auto_rejoin_channel(channel)
                else:
                    await self.remove_kicked_channel(channel)
            except Exception as e:
                print(f"Exception upon attempting to remove kicked channel or auto_rejoin: {e}")

    async def remove_kicked_channel(self, channel):
        if channel in self.joined_channels:
            self.joined_channels.remove(channel)

            # Remove the channel entry from the highlighted_channels dictionary
            if self.server_name in self.highlighted_channels:
                self.highlighted_channels[self.server_name].pop(channel, None)

            self.gui.channel_lists[self.server] = self.joined_channels
            self.update_gui_channel_list()

    async def auto_rejoin_channel(self, channel):
        await self.remove_kicked_channel(channel)
        await asyncio.sleep(1)
        await self.join_channel(channel)

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
        script_directory = os.path.dirname(os.path.abspath(__file__))
        channel_list_path = os.path.join(script_directory, "channel_list.txt")

        with open(channel_list_path, "w", encoding='utf-8') as f:
            for channel, info in self.download_channel_list.items():
                f.write(f"{channel} - Users: {info['user_count']} - Topic: {info['topic']}\n")

    def handle_names_list(self, tokens):
        current_channel = tokens.params[2]
        users = tokens.params[3].split(" ")

        # If this channel isn't in channel_users, initialize it with an empty list
        if current_channel not in self.channel_users:
            self.channel_users[current_channel] = []

        # Append the users to the channel's list only if they are not already in it
        for user in users:
            if user not in self.channel_users[current_channel]:
                self.channel_users[current_channel].append(user)

    def handle_end_of_names_list(self, tokens):
        current_channel = tokens.params[1]
        if current_channel:
            # Get the list of users for the current channel or an empty list if the key doesn't exist
            channel_users = self.channel_users.get(current_channel, [])
            # Sort the list of users
            sorted_users = self.sort_users(channel_users, current_channel)
            # Update the channel users with the sorted list
            self.channel_users[current_channel] = sorted_users
            # Update the user listbox
            self.update_user_listbox(current_channel)

    def handle_pong(self, tokens):
        pong_server = tokens.params[-1]  # Assumes the server name is the last parameter
        current_time = time.time()
        data = f"PONG from {pong_server}\n"
        if pong_server.startswith('irc'):
            pass
        elif self.znc_connection and '.' in pong_server:
            pass
        else:
            self.add_server_message(data)

        if self.ping_start_time is not None:
            ping_time = current_time - self.ping_start_time
            ping_time_formatted = "{:.3f}".format(ping_time).lstrip('0') + " s"
            self.gui.update_ping_label(ping_time_formatted)

        self.ping_start_time = None

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

        while self.loop_running:
            try:
                async with self.message_handling_semaphore:
                    data = await asyncio.wait_for(self.reader.read(4096), timeout_seconds)
            except OSError as e:
                print(f"OS ERROR Caught In handle_incoming_message: {e}")
                self.loop_running = False
                await self.reconnect(config_file)
            except Exception as e:  # General exception catch
                print(f"An Unexpected Error Occurred In handle_incoming_message: {e}\n")
                self.loop_running = False
                await self.reconnect(config_file)
            except (BrokenPipeError, asyncio.streams.StreamWriterError) as e:
                print("Connection lost while sending message.")
                self.loop_running = False
                await self.reconnect(config_file)
            except asyncio.CancelledError:
                self.loop_running = False
                print("Exiting handle_incoming_message loop.")

            if not data:
                break

            decoded_data = data.decode('UTF-8', errors='ignore')
            cleaned_data = decoded_data.replace("\x06", "")  # Remove the character with ASCII value 6
            
            if not self.use_colors:
                # Remove IRC colors and formatting using regular expressions
                cleaned_data = re.sub(r'\x03(?:\d{1,2}(?:,\d{1,2})?)?', '', cleaned_data)
            
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
                    case "412":
                        pass
                    case "353":  # NAMES list
                        self.handle_names_list(tokens)
                                
                    case "366":  # End of NAMES list
                        self.handle_end_of_names_list(tokens)

                    case "305":
                        message = "You are no longer marked as being away"
                        self.gui.insert_text_widget(f"{message}\n")

                    case "306":
                        message = "You have been marked as being away"
                        self.gui.insert_text_widget(f"{message}\n")

                    case "307":
                        self.command_307(tokens)

                    case "391":
                        self.handle_time_request(tokens)

                    case "352" | "315":
                        await self.handle_who_reply(tokens)

                    case "311" | "312" | "313" | "317" | "319" | "301" | "671" | "338" | "318" | "330":
                        await self.handle_whois_replies(tokens.command, tokens)

                    case "332" | "333" | "TOPIC":
                        self.handle_topic(tokens)

                    case "321":
                        pass

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

                    case "378":
                        self.command_378(tokens)

                    case "379":
                        self.command_379(tokens)

                    case "401":
                        self.handle_nickname_doesnt_exist(tokens)

                    case "396":
                        self.command_396(tokens)

                    case "900":
                        self.command_900(tokens)

                    case "403":
                        self.command_403(tokens)

                    case "404":
                        self.command_404(tokens)

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
                        self.handle_cannot_join_channel(tokens)

                    case "482":
                        self.handle_not_channel_operator(tokens)

                    case "487":
                        self.command_487(tokens)
                    case "433":
                        self.command_433(tokens)
                    case "432":
                        self.command_432(tokens)

                    case "322":  # Channel list
                        await self.handle_list_response(tokens)
                        await self.channel_window.update_channel_info(tokens.params[1], tokens.params[2], tokens.params[3])
                    case "323":  # End of channel list
                        await self.save_channel_list_to_file()

                    case "KICK":
                        await self.handle_kick_event(tokens)
                    case "NOTICE":
                        self.handle_notice_message(tokens)
                    case "PRIVMSG":
                        await self.handle_privmsg(tokens)
                    case "JOIN":
                        self.handle_join(tokens)
                    case "PART":
                        self.handle_part(tokens)
                    case "QUIT":
                        self.handle_quit(tokens)
                    case "NICK":
                        await self.handle_nick(tokens)
                    case "MODE":
                        self.handle_mode(tokens)
                    case "PING":
                        ping_param = tokens.params[0]
                        await self.send_message(f'PONG {ping_param}')
                    case "KILL":
                        self.handle_kill_command(tokens)
                    case "PONG":
                        self.handle_pong(tokens)
                    case _:
                        input_line = f"handle_incoming_message: {line}"
                        self.save_error(tokens, input_line)
                        if line.startswith(f":{self.server}"):
                            self.handle_server_message(line)

    def save_error(self, tokens, line):
        script_directory = os.path.dirname(os.path.abspath(__file__))
        error_log_path = os.path.join(script_directory, "token_error_log.txt")
        error = f"Debug: Unhandled command {tokens.command}. Full line: {line}\n"

        try:
            with open(error_log_path, "a") as error_log_file:
                error_log_file.write(error)
        except FileNotFoundError:
            with open(error_log_path, "w") as error_log_file:
                error_log_file.write(error)

    def command_404(self, tokens):
        channel = tokens.params[1]
        message = tokens.params[2]
        data = f"{channel}: {message}"
        self.add_server_message(data)

    def command_900(self, tokens):
        logged_in_as = tokens.params[3]
        data = f"Successfully authenticated as: {logged_in_as}\n"
        self.add_server_message(data)

    def command_396(self, tokens):
        hidden_host = tokens.params[1]
        reason = tokens.params[2]
        data = f"Your host is now hidden as: {hidden_host}. Reason: {reason}\n"
        self.add_server_message(data)

    def command_403(self, tokens):
        target = tokens.params[1]
        message = tokens.params[2]
        data = f"{message}: {target}\n"
        self.add_server_message(data)

    def handle_kill_command(self, tokens):
        source = tokens.source
        user = tokens.params[0]
        message = tokens.params[1]
        data = f"{source} {user}: {message}\n"

        self.add_server_message(data)

    def command_379(self, tokens):
        source = tokens.source
        user = tokens.params[0]
        connecting_user = tokens.params[1]
        message = tokens.params[2]
        data = f"{source} {user}: {connecting_user} {message}\n"

        self.add_server_message(data)

    def command_378(self, tokens):
        source = tokens.source
        user = tokens.params[0]
        identified_nick = tokens.params[1]
        message = tokens.params[2]
        data = f"{source} {user} {identified_nick}: {message}\n"

        self.add_server_message(data)

    def command_307(self, tokens):
        source = tokens.source
        user = tokens.params[0]
        identified_nick = tokens.params[1]
        message = tokens.params[2]
        data = f"{source} {user} {identified_nick}: {message}\n"

        self.add_server_message(data)

    def command_432(self, tokens):
        source = tokens.source
        user = tokens.params[0]
        message = f"""{tokens.params[2]}"""
        data = f"{source} {user}: {message}\n"

        self.add_server_message(data)

    def command_487(self, tokens):
        source = tokens.source
        user = tokens.params[0]
        message = f"""{tokens.params[1]}"""
        data = f"{source} {user}: {message}\n"

        self.add_server_message(data)

    def command_433(self, tokens):
        source = tokens.source
        user = tokens.params[1]
        message = f"""{tokens.params[2]}"""
        data = f"{source} {user}: {message}\n"

        self.add_server_message(data)

    def handle_already_on_channel(self, tokens):
        channel = tokens.params[2]
        message = tokens.params[3]
        data = f"{channel}: {message}\n"

        self.add_server_message(data)

    def handle_not_on_channel(self, tokens):
        channel = tokens.params[1]
        message = tokens.params[2]
        data = f"{channel}: {message}\n"

        self.add_server_message(data)

    def handle_unknown_mode(self, tokens):
        channel = tokens.params[1]
        message = tokens.params[2]
        data = f"Unknown mode for {channel}: {message}\n"

        self.add_server_message(data)

    def handle_mode_info(self, tokens):
        channel = tokens.params[1]
        modes = tokens.params[2]
        data = f"Modes for {channel}: {modes}\n"

        self.add_server_message(data)

    def handle_creation_time(self, tokens):
        channel = tokens.params[1]
        timestamp = int(tokens.params[2])  # Convert timestamp to an integer if it's a string
        creation_date = datetime.datetime.utcfromtimestamp(timestamp)
        formatted_date = creation_date.strftime('%Y-%m-%d %H:%M:%S UTC')  # Format the date as desired
        data = f"Creation time for {channel}: {formatted_date}\n"

        self.add_server_message(data)

    def handle_not_channel_operator(self, tokens):
        channel = tokens.params[1]
        message = tokens.params[2]
        data = f"{channel}: {message}\n"

        self.add_server_message(data)

    def handle_328(self, tokens):
        channel = tokens.params[1]
        url = tokens.params[2]
        data = f"URL for {channel} {url}\n"

        self.add_server_message(data)

    def handle_cannot_join_channel(self, tokens):
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
        if not self.use_logging:
            return
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
            if channel == self.nickname:
                channel = sender
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
            self.gui.insert_text_widget(f"Error: Please provide a nickname for the query command.\n")
            return

        nickname = args[1]
        
        # Remove @ and + symbols from the nickname
        nickname = nickname.lstrip("~&@%+")

        if nickname not in self.joined_channels:
            self.open_dm(nickname, timestamp)
        else:
            self.gui.insert_text_widget(f"You already have a DM open with {nickname}.\n")

    def handle_cq_command(self, args, timestamp):
        if len(args) < 2:
            self.gui.insert_text_widget(f"Usage: /cq <nickname>\n")
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
        self.gui.insert_text_widget(f"Opened DM with {nickname}.\n")

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
            self.channel_messages[self.server][channel] = []

    async def handle_kick_command(self, args):
        if len(args) < 3:
            self.gui.insert_text_widget("Usage: /kick <user> <channel> [reason]\n")
            return
        user = args[1].lstrip('~&@%+')
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
        script_directory = os.path.dirname(os.path.abspath(__file__))
        config_file = f"conf.{server_name}.rude"
        config_path = os.path.join(script_directory, config_file)
        check_server = self.gui.server_checker(server_name)
        data = f"Config file '{config_file}' not found."

        # If config_file is found, pass its path to init_client_with_config
        if check_server:
            if os.path.exists(config_path):
                await self.connect(config_file)
        elif not check_server:
            if os.path.exists(config_path):
                await self.gui.init_client_with_config(config_path, server_name)
        else:
            self.add_server_message(data)

    async def disconnect(self, server_name=None):
        if server_name:
            client = self.gui.clients.get(server_name)
            if client:
                await client.send_message("QUIT")
        else:
            if self.reader and not self.reader.at_eof():
                self.writer.close()
                await self.writer.wait_closed()
            else:
                pass

        self.gui.insert_text_widget("Disconnected\n")

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
                    self.gui.insert_text_widget(f"Error: Please provide a raw IRC command after /quote.\n")
                    return

                raw_command = " ".join(args[1:])
                await self.send_message(raw_command)
                self.gui.insert_text_widget(f"Sent raw command: {raw_command}\n")

            case "mentions":
                if len(args) > 1 and args[1] == "clear":
                    self.mentions.clear()  
                    self.gui.insert_text_widget(f"All mentions have been cleared.\n")
                elif not self.mentions:
                    self.gui.insert_text_widget(f"No mentions found.\n")
                else:
                    for target, messages in self.mentions.items():
                        self.gui.insert_text_widget(f"Mentions for {target}:\n")
                        for message in messages:
                            self.gui.insert_text_widget(f" - {message}\n")

                    self.gui.highlight_nickname()

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
                    self.gui.insert_text_widget(f"Usage: /msg <nickname> <message>\n")
                else:
                    nickname = args[1]
                    message = " ".join(args[2:])
                    await self.send_message(f"PRIVMSG {nickname} :{message}")
                    self.gui.insert_text_widget(f'<{self.nickname} -> {nickname}> {message}\n')

            case "CTCP":
                if len(args) < 3:
                    self.gui.insert_text_widget(f"Error: Please provide a nickname and CTCP command.\n")
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

            case "sw":
                channel_name = args[1]
                if channel_name in self.joined_channels and channel_name not in self.gui.popped_out_channels:
                    self.current_channel = channel_name
                    await self.pop_out_return(channel_name)
                else:
                    self.gui.insert_text_widget(f"Not a member of channel or Channel in Pop Out Window: {channel_name}\n")

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
                    self.gui.insert_text_widget(f"Error: Please provide a new nickname.\n")
                    return
                new_nick = args[1]
                if len(new_nick) > self.nicknamelen:
                    self.gui.insert_text_widget(f"Error: New nickname is too long. Max Characters Allowed: {self.nicknamelen}\n")
                    return
                await self.change_nickname(new_nick, is_from_token=False)

            case "ping":
                if len(args) > 1:
                    user = args[1]
                    if user:
                        await self.ping_user(user)
                else:
                    await self.ping_server()

            case "quit":
                quit_message = " ".join(args[1:]) if len(args) > 0 else None
                await self.send_message(f"QUIT :{quit_message}")
                self.loop_running = False
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
                await self.ignore_user(args)
                
            case "unignore":
                await self.unignore_user(args)

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
                    data = "Please Enter A Server Name"
                    self.add_server_message(data)

            case "disconnect":
                server = args[1] if len(args) > 1 else None
                if server:
                    await self.disconnect(server)
                    await self.reset_state()
                else:
                    self.gui.insert_text_widget("Client Disconnected.")
                    self.gui.insert_server_widget("Client Disconnected.")
                    await self.disconnect()
                    await self.reset_state()

            case "detach":
                channel = args[1] if len(args) > 1 else None
                if channel and self.znc_connection:
                    await self.send_message(f"detach {channel}")
                    await self.detach_channel(channel)
                else:
                    self.gui.insert_text_widget("You're either not connected to a ZNC or haven't provided a channel.")

            case "sync":
                if self.znc_connection:
                    self.gui.insert_text_widget(f"Syncing Nicks & Channel Topics...")
                    await self.auto_topic_nicklist()
                else:
                    self.gui.insert_text_widget("You're Not Using A ZNC")
            case None:
                await self.handle_user_input(user_input, timestamp)

        return True

    async def send_message_chunks(self, message_chunks, timestamp):
        for chunk in message_chunks:
            # Split the chunk into lines
            lines = chunk.split('\n')

            # Send each line separately
            for line in lines:
                if line:  # Skip empty lines
                    # Send the line as a message
                    await self.send_message(f'PRIVMSG {self.current_channel} :{line}')
                    
                    # Get the mode symbol for the current user
                    user_mode = self.get_user_mode(self.nickname, self.current_channel)
                    mode_symbol = self.get_mode_symbol(user_mode) if user_mode else ''
                    
                    # Insert the message into the text widget
                    if self.use_time_stamp:
                        self.gui.insert_text_widget(f"{timestamp}<{mode_symbol}{self.nickname}> {line}\n")
                    else:
                        self.gui.insert_text_widget(f"<{mode_symbol}{self.nickname}> {line}\n")
                    self.gui.highlight_nickname()

                    # Check if it's a DM or channel
                    if self.current_channel.startswith(self.chantypes):  # It's a channel
                        self.user_input_channel_message(line, timestamp, mode_symbol)
                    else:  # It's a DM
                        self.user_input_dm_message(line, timestamp)

                    # If there's only one item in the list, don't wait
                    if len(message_chunks) == 1 and len(lines) == 1:
                        return
                    else:
                        await asyncio.sleep(0.7)

    def user_input_channel_message(self, chunk, timestamp, mode_symbol):
        if self.server not in self.channel_messages:
            self.channel_messages[self.server] = {}
        if self.current_channel not in self.channel_messages[self.server]:
            self.channel_messages[self.server][self.current_channel] = []

        if self.use_time_stamp == True:
            self.channel_messages[self.server][self.current_channel].append(f"{timestamp}<{mode_symbol}{self.nickname}> {chunk}\n")
        elif self.use_time_stamp == False:
            self.channel_messages[self.server][self.current_channel].append(f"<{mode_symbol}{self.nickname}> {chunk}\n")

        # Log the sent message using the new logging method
        self.log_message(self.server_name, self.current_channel, self.nickname, chunk, is_sent=True)

    def user_input_dm_message(self, chunk, timestamp):
        server_name = self.server  # Replace this with the actual server name if needed
        if server_name not in self.channel_messages:
            self.channel_messages[server_name] = {}
        if self.current_channel not in self.channel_messages[server_name]:
            self.channel_messages[server_name][self.current_channel] = []
        if self.use_time_stamp == True:
            self.channel_messages[server_name][self.current_channel].append(f"{timestamp}<{self.nickname}> {chunk}\n")
        elif self.use_time_stamp == False:
            self.channel_messages[server_name][self.current_channel].append(f"<{self.nickname}> {chunk}\n")

        # Log the sent message using the new logging method
        self.log_message(self.server_name, self.current_channel, self.nickname, chunk, is_sent=True)

    async def handle_user_input(self, user_input, timestamp):
        if not user_input:
            return
        
        # Escape color codes
        escaped_input = self.escape_color_codes(user_input)

        if self.replace_pronouns:
            escaped_input = replace_pronouns(escaped_input, self.current_channel)

        if self.current_channel:
            # Split the input into lines
            lines = escaped_input.splitlines()
            
            # Check the length of the first line
            first_line = lines[0]
            if len(first_line) > 420:
                # If the first line is longer than 420 characters, split the input into chunks
                message_chunks = [escaped_input[i:i+420] for i in range(0, len(escaped_input), 420)]
            else:
                # Otherwise, pass the input without chunking
                message_chunks = [escaped_input]
            
            # Send message chunks
            await self.send_message_chunks(message_chunks, timestamp)
        else:
            self.gui.insert_text_widget(f"No channel selected. Use /join to join a channel.\n")

    async def handle_mac_command(self, args):
        if len(args) < 2:
            available_macros = ", ".join(self.ASCII_ART_MACROS.keys())
            self.gui.insert_text_widget(f"Available ASCII art macros: {available_macros}\n")
            self.gui.insert_text_widget("Usage: /mac <macro_name>\n")
            return

        macro_name = args[1]
        selected_channel = self.current_channel  # Store the currently selected channel

        if macro_name in self.ASCII_ART_MACROS:
            current_time = datetime.datetime.now().strftime('[%H:%M:%S] ')
            for line in self.ASCII_ART_MACROS[macro_name].splitlines():
                formatted_message = self.format_message(line, current_time)
                await self.send_message(f'PRIVMSG {selected_channel} :{formatted_message}')
                await asyncio.sleep(0.4)
                if selected_channel == self.current_channel:
                    if self.use_time_stamp:
                        self.gui.insert_text_widget(f"{current_time}<{self.nickname}> {formatted_message}")
                    else:
                        self.gui.insert_text_widget(f"<{self.nickname}> {formatted_message}")
                    self.gui.highlight_nickname()
                await self.append_to_channel_history(selected_channel, line)
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
        self.gui.insert_text_widget("\nLoading ASCII art macros...\n")
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

    async def ignore_user(self, args):
        user_to_ignore = " ".join(args[1:])
        if user_to_ignore not in self.ignore_list:
            self.ignore_list.append(user_to_ignore)
            self.gui.insert_text_widget(f"You've ignored {user_to_ignore}.\n")
            await self.save_ignore_list()
        else:
            self.gui.insert_text_widget(f"{user_to_ignore} is already in your ignore list.\n")

    async def unignore_user(self, args):
        if len(args) < 2:  # Check if the user has provided the username to unignore
            self.gui.insert_text_widget("Usage: unignore <username>\n")
            return

        user_to_unignore = args[1]
        if user_to_unignore in self.ignore_list:
            self.ignore_list.remove(user_to_unignore)
            self.gui.insert_text_widget(f"You've unignored {user_to_unignore}.\n")
            await self.save_ignore_list()
        else:
            self.gui.insert_text_widget(f"{user_to_unignore} is not in your ignore list.\n")

    async def save_ignore_list(self):
        script_directory = os.path.dirname(os.path.abspath(__file__))
        
        # Construct the full path for the ignore_list.txt
        file_path = os.path.join(script_directory, 'ignore_list.txt')
        
        async with aiofiles.open(file_path, mode="w", encoding='utf-8') as f:
            for user in self.ignore_list:
                await f.write(f"{user}\n")

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
        if self.use_time_stamp == True:
            formatted_message = f"{timestamp}<{self.nickname}> {escaped_message}\n"
        elif self.use_time_stamp == False:
            formatted_message = f"<{self.nickname}> {escaped_message}\n"

        # Initialize the server name
        server_name = self.server

        # Determine if it's a channel or DM
        if channel.startswith(self.chantypes):  # It's a channel
            if self.server not in self.channel_messages:
                self.channel_messages[server_name] = {}
            if channel not in self.channel_messages[self.server]:
                self.channel_messages[server_name][channel] = []
            self.channel_messages[server_name][channel].append(formatted_message)
        else:  # It's a DM
            if server_name not in self.channel_messages:
                self.channel_messages[server_name] = {}
            if channel not in self.channel_messages[server_name]:
                self.channel_messages[server_name][channel] = []
            self.channel_messages[server_name][channel].append(formatted_message)

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
        def random_color():
            """Returns a random IRC color code."""
            return f'\x03{random.randint(2, 15):02d}'

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

        # Apply random colors
        top_border_colored = random_color() + top_border + '\x0F'
        bottom_border_colored = random_color() + bottom_border + '\x0F'
        combined_message_colored = '\n'.join([random_color() + line + '\x0F' for line in combined_message.split('\n')])

        return f"{top_border_colored}\n{combined_message_colored}\n{bottom_border_colored}{cow}"

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
        selected_channel = self.current_channel

        with open(file_name, 'r', encoding='utf-8') as f:
            fortunes = f.read().strip().split('%')
            chosen_fortune = random.choice(fortunes).strip()

        wrapped_fortune_text = self.wrap_text(chosen_fortune)
        cowsay_fortune = self.cowsay(wrapped_fortune_text)

        for line in cowsay_fortune.split('\n'):
            if self.use_time_stamp == True:
                formatted_message = f"{timestamp}<{self.nickname}> {line}\n"
            elif self.use_time_stamp == False:
                formatted_message = f"<{self.nickname}> {line}\n"
            await self.send_message(f'PRIVMSG {selected_channel} :{line}')
            await asyncio.sleep(0.4)
            await self.append_to_channel_history(selected_channel, line)
            if selected_channel == self.current_channel:
                self.gui.insert_text_widget(formatted_message)
                self.gui.highlight_nickname()

    async def cowsay_custom_message(self, message):
        """Wrap a custom message using the cowsay format."""
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
        selected_channel = self.current_channel
        wrapped_message = self.wrap_text(message)
        cowsay_output = self.cowsay(wrapped_message)
        
        for line in cowsay_output.split('\n'):
            if self.use_time_stamp == True:
                formatted_message = f"{timestamp}<{self.nickname}> {line}\n"
            elif self.use_time_stamp == False:
                formatted_message = f"<{self.nickname}> {line}\n"
            await self.send_message(f'PRIVMSG {selected_channel} :{line}')
            await asyncio.sleep(0.4)
            await self.append_to_channel_history(selected_channel, line)
            if selected_channel == self.current_channel:
                self.gui.insert_text_widget(formatted_message)
                self.gui.highlight_nickname()

    async def fortune(self, file_name=None):
        """Choose a random fortune from one of the lists"""
        selected_channel = self.current_channel
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
        file_name = self.get_fortune_file(file_name)

        with open(file_name, 'r', encoding='utf-8') as f:  # Notice the encoding parameter
            fortunes = f.read().strip().split('%')
            chosen_fortune = random.choice(fortunes).strip()

        for line in chosen_fortune.split('\n'):
            if self.use_time_stamp == True:
                formatted_message = f"{timestamp}<{self.nickname}> {line}\n"
            elif self.use_time_stamp == False:
                formatted_message = f"<{self.nickname}> {line}\n"
            await self.send_message(f'PRIVMSG {selected_channel} :{line}')
            await asyncio.sleep(0.4)
            await self.append_to_channel_history(selected_channel, line)
            if selected_channel == self.current_channel:
                self.gui.insert_text_widget(formatted_message)
                self.gui.highlight_nickname()

    async def send_ctcp_request(self, target_nick, ctcp_command):
        """Sends a CTCP request to a target."""
        ctcp_message = f"\x01{ctcp_command.upper()}\x01"
        await self.send_message(f'PRIVMSG {target_nick} :{ctcp_message}')

    async def set_mode(self, channel, mode, target=None):
        """Sets the mode for a specified target in a specified channel.
        If target is None, sets the mode for the channel.
        """
        stripped_mode = mode.lstrip('+-')

        if stripped_mode in self.chanmodes.get('list', []):
            if mode and target:
                await self.send_message(f'MODE {channel} {mode} {target}')

        elif stripped_mode in self.chanmodes.get('no_parameter', []):
            await self.send_message(f'MODE {channel} {mode}')

        elif stripped_mode in self.chanmodes.get('setting', []):
            if mode and target:
                await self.send_message(f'MODE {channel} {mode} {target}')

        elif stripped_mode in self.chanmodes.get('parameter', []):
            if mode and target:
                await self.send_message(f'MODE {channel} {mode} {target}')
            elif mode:
                await self.send_message(f'MODE {channel} {mode}')

        elif stripped_mode in self.mode_to_symbol:
            if target:
                await self.send_message(f'MODE {channel} {mode} {target}')
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
        self.gui.clear_user_listbox()
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

    async def ping_user(self, user):
        # Initialize ping_start_time to the current time
        self.ping_start_time = time.time()

        await self.send_message(f'PING {user}')

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
        escaped_input = self.escape_color_codes(action_message)
        formatted_message = f"* {self.nickname} {escaped_input}"
        await self.send_message(f'PRIVMSG {self.current_channel} :\x01ACTION {escaped_input}\x01')
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
        if self.use_time_stamp == True:
            self.gui.insert_text_widget(f"{timestamp}{formatted_message}\n")
        elif self.use_time_stamp == False:
            self.gui.insert_text_widget(f"{formatted_message}\n")
        self.gui.highlight_nickname()

        # Save the action message to the channel_messages dictionary
        if self.server not in self.channel_messages:
            self.channel_messages[self.server] = {}
        if self.current_channel not in self.channel_messages[self.server]:
            self.channel_messages[self.server][self.current_channel] = []
        if self.use_time_stamp == True:
            self.channel_messages[self.server][self.current_channel].append(f"{timestamp}{formatted_message}\n")
        elif self.use_time_stamp == False:
            self.channel_messages[self.server][self.current_channel].append(f"{formatted_message}\n")

    def display_help(self):
        # Categories and their associated commands
        categories = {
            "Channel Management": [
                "Use Your Right Click for Config and more.",
                "/join <channel> - Joins a channel",
                "/part <channel> - Leaves a channel",
                "/ch - Shows channels joined",
                "/sw <channel> - Switches to a channel",
                "/topic - Requests the topic for the current channel",
                "/names - Refreshes the user list for the current channel",
                "/banlist - Shows ban list for channel",
                "/invite <user> <channel> - invites a user to a channel",
                "/kick <user> <channel> [message]",
                "/mentions to show all mentions of your nickname. /mentions clear to clear these messages",
                "_________",
            ],
            "String Formatting": [
                "To use formatting use the format control characters as follows",
                "\\x02 - Bold",
                "\\x1D - Italic",
                "\\x1F - Underline",
                "\\x1E - Strike-Through",
                "\\x03<colorcode> - Color",
                "\\x0F - Terminate formatting - end of format string",
                "\\x16 - Inverse control character. Swaps the color",
                "Example: \\x0304example text\\x0F",
                "When using the GUI for format select first the type of format example: bold. Then select the color.",
                "_________",
            ],
            "Private Messaging": [
                "/query <nickname> - Opens a DM with a user",
                "/cq <nickname> - Closes a DM with a user",
                "/msg <nickname> [message] - Sends a private message to a user",
                "_________",
            ],
            "User Commands": [
                "/nick <new nickname> - Changes the user's nickname",
                "/away [message] - Sets the user as away",
                "/back - Removes the 'away' status",
                "/who <mask> - Lists users matching a mask",
                "/whois <nickname> - Shows information about a user",
                "/me <action text> - Sends an action to the current channel",
                "/clear - clears the chat window and removes all messages for the current channel",
                "_________",
            ],
            "Server Interaction": [
                "/ping [user] - Pings the currently selected server, if user is specified it will ping that user.",
                "/quote <IRC command> - Sends raw IRC message to the server",
                "/CTCP <nickname> <command> - Sends a CTCP request",
                "/mode <mode> [channel] - Sets mode for user (optionally in a specific channel)",
                "_________",
            ],
            "Broadcasting": [
                "/notice <target> [message]",
                "_________",
            ],
            "Help and Connection": [
                "/quit - Closes connection and client",
                "/help - Redisplays this message",
                "/disconnect - Will disconnect you from the currently connected servers",
                "/connect <server_name> - Will connect you to the given server, is case sensitive.",
                "_________",
            ],
            "ZNC Commands": [
                "/sync - Syncs your nickname list and channel topics.",
                "/detach - Detaches you from the given channel Example: /detach #channel",
                "_________",
            ],
            "Key Bindings": [
                "Alt+num(0,9) - switches to that channels index in the channel list.",
                "Alt+s - Cycles through the servers",
                "ctrl+tab - Cycles through the channels",
                "_________",
            ],
            "Fun": [
                "/cowsay: Built in, /cowsay <text> | /cowsay <fortune list>",
                "/fortune: Built in, /fortune <fortune list>",
                "/mac <macro> - sends a chosen macro to a channel /mac - shows available macros",
                "Fortune Lists: dadjoke(jokes your dad makes), yomama(YO MAMA SO FAT), therules(Ferengi Rules of Acquisition)",
                "Add your own fortune lists to the Fortune List folder in site-packages for python."
                "_________",
            ],
        }

        try:
            help_channel = "&HELP&"
            if help_channel not in self.joined_channels:
                self.joined_channels.append(help_channel)
                self.gui.channel_lists[self.server] = self.joined_channels
                self.update_gui_channel_list()

                # Add help data to the channel history
                for category, commands in categories.items():
                    if help_channel not in self.channel_messages[self.server]:
                        self.channel_messages[self.server][help_channel] = [] 
                    self.channel_messages[self.server][help_channel].append(f"{category}:\n")
                    for cmd in commands:
                        self.channel_messages[self.server][help_channel].append(f"{cmd}\n")

            # Update the GUI
            self.gui.insert_and_scroll()
        except Exception as e:
            print(f"Exception in help: {e}")

    def set_gui(self, gui):
        self.gui = gui

    def set_server_name(self, server_name):
        self.server_name = server_name
        self.gui.update_nick_channel_label()

    def display_last_messages(self, channel, num=125, server_name=None):
        if server_name:
            messages = self.channel_messages.get(server_name, {}).get(channel, [])
        for message in messages[-num:]:
            self.gui.insert_text_widget(message)

    def display_server_motd(self, server_name=None):
        if server_name:
            messages = self.motd_dict.get(server_name, [])
            self.gui.insert_text_widget(f"{messages}\n")

    def pop_out_switch(self):
        # Get the existing channel list from the channel_listbox
        channel_list = self.gui.channel_listbox.get(0, self.gui.channel_listbox.size())

        # Pick a channel at random from the channel list
        if channel_list:
            channel = random.choice(channel_list)
            self.gui.switch_channel(channel)

    async def pop_out_return(self, channel):
        await self.gui.switch_channel(channel)