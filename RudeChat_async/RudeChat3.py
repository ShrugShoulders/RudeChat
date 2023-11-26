import asyncio
import base64
import ssl
import configparser
import datetime
import irctokens
import time
import textwrap
import random
import datetime
import logging
import os
import re
import sys
import tkinter as tk
from plyer import notification
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tkinter import Tk, Frame, Label, Entry, Listbox, Scrollbar, StringVar

class AsyncIRCClient:
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
        self.whois_executed = set()
        self.decoder = irctokens.StatefulDecoder()
        self.encoder = irctokens.StatefulEncoder()
        self.gui = gui
        self.reader = None
        self.writer = None
        self.sasl_authenticated = False

        self.load_ignore_list()

    async def read_config(self, config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        self.server = config.get('IRC', 'server')
        self.port = config.getint('IRC', 'port')
        self.ssl_enabled = config.getboolean('IRC', 'ssl_enabled')
        self.nickname = config.get('IRC', 'nickname')
        self.nickserv_password = config.get('IRC', 'nickserv_password')
        self.auto_join_channels = config.get('IRC', 'auto_join_channels').split(',')
        
        # Read new SASL-related fields
        self.sasl_enabled = config.getboolean('IRC', 'sasl_enabled', fallback=False)
        self.sasl_username = config.get('IRC', 'sasl_username', fallback=None)
        self.sasl_password = config.get('IRC', 'sasl_password', fallback=None)
        
        # Read server name from config file
        self.server_name = config.get('IRC', 'server_name', fallback=None)
        self.gui.update_nick_channel_label()

    async def connect(self):
        await self.connect_to_server()
        await self.send_initial_commands()
        await self.wait_for_welcome()

    async def connect_to_server(self):
        TIMEOUT = 60  # seconds
        self.gui.insert_text_widget(f'Connecting to server: {self.server}:{self.port}\r\n')
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
            self.gui.insert_text_widget(f"Connection timeout. Please try again later.\r\n")
        except OSError as e:
            if e.winerror == 121:  # The semaphore error that I hate.
                self.gui.insert_text_widget("The semaphore timeout period has expired. Reconnecting...\r\n")
                success = await self.reconnect()
                if success:
                    self.gui.add_server_to_combo_box(self.server_name)
            else:
                self.gui.insert_text_widget(f"An unexpected error occurred: {str(e)}\r\n")

    async def send_initial_commands(self):
        self.gui.insert_text_widget(f'Sent client registration commands.\r\n')
        await self.send_message(f'NICK {self.nickname}')
        await self.send_message(f'USER {self.nickname} 0 * :{self.nickname}')
        
        # Start capability negotiation
        if self.sasl_enabled:
            print("[DEBUG] About to send CAP LS 302")  # Debug message
            await self.send_message('CAP LS 302')
        else:
            print("[DEBUG] SASL is not enabled.")  # Debug message

        if self.nickserv_password:
            await self.send_message(f'PRIVMSG NickServ :IDENTIFY {self.nickserv_password}')

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
        self.gui.insert_text_widget(f"Message of the Day:\n{full_motd}\r\n")
        self.gui.insert_and_scroll()
        # Clear the MOTD buffer for future use
        self.motd_lines.clear()
            
    async def wait_for_welcome(self):
        MAX_RETRIES = 5
        RETRY_DELAY = 5  # seconds
        retries = 0

        while retries < MAX_RETRIES:
            print(f"Retry count: {retries}")
            try:
                await self._await_welcome_message()
                return  # Successfully connected and received 001
            except (OSError, ConnectionError) as e:
                self.gui.insert_text_widget(f"Error occurred: {e}. Retrying in {RETRY_DELAY} seconds.\r\n")
                success = await self.reconnect()
                if success:
                    return  # Successfully reconnected
                retries += 1
                await asyncio.sleep(RETRY_DELAY)
        self.gui.insert_text_widget("Failed to reconnect after multiple attempts. Please check your connection.\r\n")

    def handle_connection_info(self, tokens):
        connection_info = tokens.params[-1]  # Assumes the connection info is the last parameter
        self.gui.insert_text_widget(f"Server Info: {connection_info}\r\n")
        self.gui.insert_and_scroll()

    def handle_global_users_info(self, tokens):
        global_users_info = tokens.params[-1]  # Assumes the global users info is the last parameter
        self.gui.insert_text_widget(f"Server Users Info: {global_users_info}\r\n")
        self.gui.insert_and_scroll()

    async def handle_nickname_conflict(self, tokens):
        new_nickname = self.nickname + str(random.randint(1, 99))
        await self.send_message(f'NICK {new_nickname}')
        self.nickname = new_nickname
        self.gui.insert_text_widget(f"Nickname already in use. Changed nickname to: {self.nickname}\r\n")

    async def initial_ping(self, tokens):
        ping_param = tokens.params[0]
        await self.send_message(f'PONG {ping_param}')
        self.gui.insert_and_scroll()

    async def automatic_join(self):
        for channel in self.auto_join_channels:
            await self.join_channel(channel)
            await asyncio.sleep(0.5)

    async def _await_welcome_message(self):
        self.gui.insert_text_widget(f'Waiting for welcome message from server.\r\n')
        buffer = ""
        received_001 = False  

        while True:
            data = await self.reader.read(4096)
            if not data:
                raise ConnectionError("Connection lost while waiting for welcome message.")
            
            decoded_data = data.decode('UTF-8', errors='ignore')
            buffer += decoded_data
            while '\r\n' in buffer:
                line, buffer = buffer.split('\r\n', 1)
                tokens = irctokens.tokenise(line)

                match tokens.command:
                    case "CAP":
                        await self.handle_cap(tokens)

                    case "AUTHENTICATE":
                        await self.handle_sasl_auth(tokens)

                    case "903":
                        await self.handle_sasl_successful()
                        sasl_authenticated = True

                    case "904":
                        self.handle_sasl_failed()

                    case "001":
                        self.gui.insert_text_widget(f'Connected to server: {self.server}:{self.port}\r\n')
                        received_001 = True  # Set this to True upon receiving 001
                        self.gui.insert_and_scroll()
                    case "005":  # Handling the ISUPPORT message
                        self.handle_isupport(tokens)
                        self.gui.insert_and_scroll()
                    case "250":
                        self.handle_connection_info(tokens)
                    case "266":
                        self.handle_global_users_info(tokens)
                    case "433":  # Nickname already in use
                        await self.handle_nickname_conflict(tokens)
                    case "372":  # Individual line of MOTD
                        self.handle_motd_line(tokens)
                    case "375":  # Start of MOTD
                        self.handle_motd_start(tokens)
                    case "376":  # End of MOTD
                        self.handle_motd_end(tokens)
                    case "PING":
                        await self.initial_ping(tokens)
                    case _:
                        self.gui.insert_and_scroll()
            if received_001:
                await self.automatic_join()
                return

    async def handle_cap(self, tokens):
        print(f"[DEBUG] Handling CAP: {tokens.params}")
        if not self.sasl_enabled:
            print(f"[DEBUG] SASL is not enabled.")
            return  # Skip SASL if it's not enabled
        if "LS" in tokens.params:
            print(f"[DEBUG] Sending CAP REQ :sasl")
            await self.send_message("CAP REQ :sasl")
        elif "ACK" in tokens.params:
            print(f"[DEBUG] Sending AUTHENTICATE PLAIN")
            await self.send_message("AUTHENTICATE PLAIN")

    async def handle_sasl_auth(self, tokens):
        print(f"[DEBUG] Handling AUTHENTICATE: {tokens.params}")
        if not self.sasl_enabled:
            print(f"[DEBUG] SASL is not enabled.")
            return  # Skip SASL if it's not enabled
        if tokens.params[0] == '+':
            auth_string = f"{self.sasl_username}\0{self.sasl_username}\0{self.sasl_password}"
            encoded_auth_string = base64.b64encode(auth_string.encode()).decode()
            print(f"[DEBUG] Sending AUTHENTICATE {encoded_auth_string[:5]}...")  # Truncate to not reveal sensitive info
            await self.send_message(f"AUTHENTICATE {encoded_auth_string}")

    async def handle_sasl_successful(self):
        print(f"[DEBUG] SASL authentication successful.")
        if not self.sasl_enabled:
            print(f"[DEBUG] SASL is not enabled.")
            return  # Skip SASL if it's not enabled
        self.gui.insert_text_widget(f"SASL authentication successful.\r\n")
        await self.send_message("CAP END")

    def handle_sasl_failed(self):
        print(f"[DEBUG] SASL authentication failed.")
        if not self.sasl_enabled:
            print(f"[DEBUG] SASL is not enabled.")
            return
        self.gui.insert_text_widget(f"SASL authentication failed. Disconnecting.\r\n")

    async def send_message(self, message):
        try:
            self.writer.write(f'{message}\r\n'.encode('UTF-8'))
            await asyncio.wait_for(self.writer.drain(), timeout=10)
        except TimeoutError:
            print("Timeout while sending message.")

    async def join_channel(self, channel):
        if not self.is_valid_channel(channel):
            print(f"Invalid channel name {channel}.")
            self.gui.insert_text_widget(f"Invalid channel name {channel}.\r\n")
            self.gui.insert_and_scroll()
            return

        await self.send_message(f'JOIN {channel}')
        self.joined_channels.append(channel)
        self.gui.channel_lists[self.server] = self.joined_channels  # Update the GUI channel list
        self.update_gui_channel_list()  # Update the channel list in GUI

    def is_valid_channel(self, channel):
        return any(channel.startswith(prefix) for prefix in self.chantypes)

    async def leave_channel(self, channel):
        await self.send_message(f'PART {channel}')
        if channel in self.joined_channels:
            self.joined_channels.remove(channel)
        self.gui.channel_lists[self.server] = self.joined_channels
        self.update_gui_channel_list()

    def update_gui_channel_list(self):
        self.gui.channel_listbox.delete(0, tk.END)  # Clear existing items
        for chan in self.joined_channels:
            self.gui.channel_listbox.insert(tk.END, chan)

    def update_gui_user_list(self, channel):
        print(f"Debug: channel_users = {self.channel_users}")  # Debug line
        self.gui.user_listbox.delete(0, tk.END)
        for user in self.channel_users.get(channel, []):
            self.gui.user_listbox.insert(tk.END, user)

    async def reset_state(self):
        self.joined_channels.clear()
        self.motd_lines.clear()
        self.channel_messages.clear()
        self.channel_users.clear()
        self.user_modes.clear()
        self.mode_to_symbol.clear()
        self.whois_data.clear()
        self.download_channel_list.clear()
        self.whois_executed.clear()

    async def reconnect(self):
        MAX_RETRIES = 5
        RETRY_DELAY = 5
        retries = 0
        while retries < MAX_RETRIES:
            try:
                # Reset client state before attempting to reconnect
                await self.reset_state()
                # Attempt to reconnect
                await self.connect()
                
                # Add server to combo box if reconnection is successful
                if self.gui:
                    self.gui.irc_client = self
                    self.gui.add_server_to_combo_box(self.server_name)  # Assuming such a method exists in your GUI class
                
                if hasattr(self.gui, 'insert_text_widget'):  
                    self.gui.insert_text_widget(f'Successfully reconnected.\r\n')
                    self.gui.insert_and_scroll()
                else:
                    print(f"GUI object not set")
                return True  # Successfully reconnected
            except Exception as e:
                retries += 1
                print(f'Failed to reconnect ({retries}/{MAX_RETRIES}): {e}. Retrying in {RETRY_DELAY} seconds.\r\n')
                await asyncio.sleep(RETRY_DELAY)
        return False  # Failed to reconnect after MAX_RETRIES

    async def keep_alive(self):
        while True:
            try:
                await asyncio.sleep(194)
                await self.send_message(f'PING {self.server}')
            except (ConnectionResetError, OSError) as e:
                print(f"Exception caught in keep_alive: {e}")

    async def handle_server_message(self, line):
        self.gui.insert_server_widget(line + "\r\n")
        self.gui.insert_and_scroll()

    async def handle_notice_message(self, tokens):
        sender = tokens.hostmask if tokens.hostmask else "Server"
        target = tokens.params[0]
        message = tokens.params[1]
        self.gui.insert_server_widget(f"NOTICE {sender}: {message}\r\n")
        self.gui.insert_and_scroll()

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
                        await self.send_message(f'NOTICE {sender} :\x01VERSION RudeChat3.0\x01')
                case "PING":
                    if tokens.command == "PRIVMSG":
                        await self.send_message(f'NOTICE {sender} :\x01PING {ctcp_content}\x01')
                case "TIME":
                    if tokens.command == "PRIVMSG":
                        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        await self.send_message(f'NOTICE {sender} :\x01TIME {current_time}\x01')
                case "ACTION":
                    action_message = f"{timestamp}* {sender} {ctcp_content}\r\n"
                    
                    # Update the message history
                    if target not in self.channel_messages:
                        self.channel_messages[target] = []
                    
                    self.channel_messages[target].append(action_message)
                    
                    # Display the message in the text_widget if the target matches the current channel or DM
                    if target == self.current_channel and self.gui.irc_client == self:
                        self.gui.insert_text_widget(action_message)
                        self.gui.highlight_nickname()
                        self.gui.insert_and_scroll()
                    else:
                        # If it's not the currently viewed channel, highlight the channel in green in the Listbox
                        for idx in range(self.gui.channel_listbox.size()):
                            if self.gui.channel_listbox.get(idx) == target:
                                current_bg = self.gui.channel_listbox.itemcget(idx, 'bg')
                                if current_bg != 'red':
                                    self.gui.channel_listbox.itemconfig(idx, {'bg':'green'})
                                break
                case _:
                    print(f"Unhandled CTCP command: {ctcp_command}")

    async def notify_user_of_mention(self, server, channel):
        notification_msg = f"Mention on {server} in {channel}"
        self.gui.insert_server_widget(f"\n{notification_msg}\n")
        self.gui.insert_and_scroll()

        # Highlight the mentioned channel in the Listbox
        for idx in range(self.gui.channel_listbox.size()):
            if self.gui.channel_listbox.get(idx) == channel:
                self.gui.channel_listbox.itemconfig(idx, {'bg':'red'})
                break
        
        # Play the beep sound/notification
        await self.trigger_beep_notification(channel_name=channel, message_content=notification_msg)

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

        # Check if the user is mentioned in the message
        if self.nickname in message:
            await self.notify_user_of_mention(self.server, target)

        # Check for CTCP command
        if message.startswith('\x01') and message.endswith('\x01'):
            await self.handle_ctcp(tokens)
            return

        # If the target is the bot's nickname, it's a DM
        if target == self.nickname:
            target = sender  # Consider the sender as the "channel" for DMs
            print(f"[DEBUG] Current target: {target}")

            # Check if we have executed WHOIS for this sender before
            if sender not in self.whois_executed:
                await self.send_message(f'WHOIS {sender}')
                self.whois_executed.add(sender)

            # Check if the server exists in the dictionary
            if self.server not in self.channel_messages:
                self.channel_messages[self.server] = {}

            # Check if the DM exists in the server's dictionary
            if target not in self.channel_messages[self.server]:
                self.channel_messages[self.server][target] = []

                # If it's a DM and not in the joined_channels list, add it
                if target == sender and target not in self.joined_channels:
                    print(f"[DEBUG] Current channel_messages: {self.channel_messages}")
                    self.joined_channels.append(target)
                    self.gui.channel_lists[self.server] = self.joined_channels
                    self.update_gui_channel_list()

            # Now it's safe to append the message
            self.channel_messages[self.server][target].append(f"{timestamp}<{sender}> {message}\r\n")
            self.log_message(target, sender, message, is_sent=False)

            # Identify the correct message list for trimming
            message_list = self.channel_messages[self.server][target]
        else:
            # It's a channel message
            if target not in self.channel_messages:
                self.channel_messages[target] = []
            
            self.channel_messages[target].append(f"{timestamp}<{sender}> {message}\r\n")
            self.log_message(target, sender, message, is_sent=False)

            # Identify the correct message list for trimming
            message_list = self.channel_messages[target]

        # Trim the messages list if it exceeds 200 lines
        if len(message_list) > 200:
            message_list = message_list[-200:]

        # Display the message in the text_widget if the target matches the current channel or DM
        if target == self.current_channel and self.gui.irc_client == self:
            self.gui.insert_text_widget(f"{timestamp}<{sender}> {message}\r\n")
            self.gui.highlight_nickname()
            self.gui.insert_and_scroll()
        else:
            # If it's not the currently viewed channel, highlight the channel in green in the Listbox
            for idx in range(self.gui.channel_listbox.size()):
                if self.gui.channel_listbox.get(idx) == target:
                    current_bg = self.gui.channel_listbox.itemcget(idx, 'bg')
                    if current_bg != 'red':
                        self.gui.channel_listbox.itemconfig(idx, {'bg':'green'})
                    break

    async def handle_join(self, tokens):
        user_info = tokens.hostmask.nickname
        channel = tokens.params[0]
        join_message = f"{user_info} has joined channel {channel}\r\n"

        # Update the message history for the channel
        if channel not in self.channel_messages:
            self.channel_messages[channel] = []

        self.channel_messages[channel].append(join_message)

        # Display the message in the text_widget only if the channel matches the current channel
        if channel == self.current_channel and self.gui.irc_client == self:
            self.gui.insert_text_widget(join_message)
            self.gui.insert_and_scroll()

        # If the user joining is the client's user, just return
        if user_info == self.nickname:
            return

        # Check if the user is not already in the channel_users list for the channel
        if user_info not in self.channel_users.get(channel, []):
            # Add the user to the channel_users list
            self.channel_users.setdefault(channel, []).append(user_info)
        else:
            already_in_message = f"{user_info} is already in the user list for channel {channel}\r\n"
            if channel == self.current_channel and self.gui.irc_client == self:
                self.gui.insert_text_widget(already_in_message)
                self.gui.insert_and_scroll()

        # Sort the user list for the channel
        sorted_users = self.sort_users(self.channel_users[channel], channel)

        # Update the user listbox for the channel with sorted users
        self.update_user_listbox(channel)

    async def handle_part(self, tokens):
        user_info = tokens.hostmask.nickname
        channel = tokens.params[0]
        part_message = f"{user_info} has parted from channel {channel}\r\n"

        # Update the message history for the channel
        if channel not in self.channel_messages:
            self.channel_messages[channel] = []

        self.channel_messages[channel].append(part_message)

        # Display the message in the text_widget only if the channel matches the current channel
        if channel == self.current_channel and self.gui.irc_client == self:
            self.gui.insert_text_widget(part_message)
            self.gui.insert_and_scroll()

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
        user_info = tokens.hostmask.nickname  # No stripping needed here
        reason = tokens.params[0] if tokens.params else "No reason"
        quit_message = f"{user_info} has quit: {reason}\r\n"

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

                    # Display the message in the text_widget only if the channel matches the current channel
                    if channel == self.current_channel and self.gui.irc_client == self:
                        self.gui.insert_text_widget(quit_message)
                        self.gui.insert_and_scroll()

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
                    self.channel_messages[channel].append(f"{old_nick} has changed their nickname to {new_nick}\r\n")
                    
                    # Insert message into the text widget only if this is the current channel
                    if channel == self.current_channel:
                        self.gui.insert_text_widget(f"{old_nick} has changed their nickname to {new_nick}\r\n")

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

        # Ignore ban and unban commands
        if mode_change in ['+b', '-b']:
            print(f"Ignoring ban/unban mode for {user if user else 'unknown'}")
            return

        if channel in self.joined_channels and user:
            current_modes = self.user_modes.get(channel, {})

            # Handle addition of modes
            if mode_change.startswith('+'):
                mode = mode_change[1]
                current_modes.setdefault(user, set()).add(mode)
                    
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
                    
                if not user_modes:
                    del current_modes[user]  # Remove the user's entry if no modes left
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
        if channel == self.current_channel:
            # Update the Tkinter Listbox to reflect the current users in the channel
            self.gui.user_listbox.delete(0, tk.END)  # Clear existing items
            for user in sorted_users:
                self.gui.user_listbox.insert(tk.END, user)
                       
    def handle_isupport(self, tokens):
        params = tokens.params[:-1]  # Exclude the trailing "are supported by this server" message
        isupport_message = " ".join(params)
        self.gui.insert_server_widget(f"ISUPPORT: {isupport_message}\r\n")
        self.gui.insert_and_scroll()

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
                message = f"User {details['nickname']} ({details['username']}@{details['host']}) on {details['server']} in {details['channel']}\r\n"
                messages.append(message)
            final_message = "\n".join(messages)
            self.gui.insert_text_widget(final_message)
            self.gui.insert_and_scroll()
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
                    self.gui.insert_and_scroll()
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

        # Display the information in your client's GUI
        message = f"Server Time from {server_name}: {local_time}"
        self.gui.insert_text_widget(message)

    async def handle_kick_event(self, tokens):
        """
        Handle the KICK event from the server.
        """
        channel = tokens.params[0]
        kicked_nickname = tokens.params[1]
        reason = tokens.params[2] if len(tokens.params) > 2 else 'No reason provided'

        # Display the kick message in the chat window
        kick_message_content = f"{kicked_nickname} has been kicked from {channel} by {tokens.hostmask.nickname} ({reason})"
        self.gui.insert_text_widget(kick_message_content + "\r\n")

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
        self.gui.insert_server_widget(f"PONG: {pong_server}\r\n")
        self.gui.insert_and_scroll()

    def handle_372(self, tokens):
        motd_line = tokens.params[-1]
        self.motd_lines.append(motd_line)

    def handle_376(self, tokens):
        full_motd = "\n".join(self.motd_lines)
        self.gui.insert_text_widget(f"Message of the Day:\n{full_motd}\r\n")
        self.gui.insert_and_scroll()
        self.motd_lines.clear()

    def handle_900(self, tokens):
        logged_in_as = tokens.params[3]
        self.gui.insert_server_widget(f"Successfully authenticated as: {logged_in_as}\r\n")
        self.gui.insert_and_scroll()

    def handle_396(self, tokens):
        hidden_host = tokens.params[1]
        reason = tokens.params[2]
        self.gui.insert_server_widget(f"Your host is now hidden as: {hidden_host}. Reason: {reason}\r\n")
        self.gui.insert_and_scroll()

    def handle_error(self, tokens):
        error_message = ' '.join(tokens.params) if tokens.params else 'Unknown error'
        self.gui.insert_text_widget(f"ERROR: {error_message}\r\n")
        self.gui.insert_and_scroll()

    async def handle_cap_main(self, tokens):
        subcommand = tokens.params[1].upper()
        if subcommand == "LS":
            capabilities = tokens.params[-1]
            self.gui.insert_text_widget(f"Server capabilities: {capabilities}\r\n")
            self.gui.insert_and_scroll()
            # Requesting SASL capability
            await self.send_message("CAP REQ :sasl")
        elif subcommand == "ACK":  # If the server acknowledges the capabilities you requested
            acknowledged_caps = tokens.params[-1]
            self.gui.insert_text_widget(f"Enabled capabilities: {acknowledged_caps}\r\n")
            self.gui.insert_and_scroll()

    def handle_topic(self, tokens):
        channel_name = tokens.params[1] 
        command = tokens.command

        if command == "332":
            topic = tokens.params[2]
            self.gui.channel_topics[channel_name] = topic
            self.gui.current_topic.set(f"Topic: {topic}")

        elif command == "333":
            who_set = tokens.params[2]

    async def handle_incoming_message(self):
        buffer = ""
        current_users_list = []
        current_channel = ""
        timeout_seconds = 256  # seconds
        #
        while True:
            try:
                data = await asyncio.wait_for(self.reader.read(4096), timeout_seconds)
            except asyncio.TimeoutError:
                self.gui.insert_text_widget("Read operation timed out!\n")
                continue
            except OSError as e:
                if e.winerror == 121:  # Check if the WinError code is 121
                    self.gui.insert_text_widget(f"WinError: {e}\n")
                    await self.reconnect()
                else:
                    self.gui.insert_text_widget(f"Unhandled OSError: {e}\n")
                    continue
            except Exception as e:  # General exception catch
                self.gui.insert_text_widget(f"An unexpected error occurred: {e}\n")

                continue

            if not data:
                break

            decoded_data = data.decode('UTF-8', errors='ignore')
            buffer += decoded_data

            while '\r\n' in buffer:
                line, buffer = buffer.split('\r\n', 1)
                try:
                    # Check for an empty line or line with only whitespace before attempting to tokenize
                    if len(line.strip()) == 0:
                        print(f"Debug: Received an empty or whitespace-only line: '{line}'\r\n")
                        continue

                    # Additional check: Ensure that the line has at least one character
                    if len(line) < 1:
                        print(f"Debug: Received a too-short line: '{line}'\r\n")
                        continue

                    # Debug statement to print the line before tokenizing
                    print(f"Debug: About to tokenize the line - '{line}'")

                    tokens = irctokens.tokenise(line)
                except ValueError as e:
                    self.gui.insert_text_widget(f"Error: {e}\r\n")
                    continue
                except IndexError as ie:
                    self.gui.insert_text_widget(f"IndexError: {ie}. Line: '{line}'\r\n")
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

                    case "391":
                        self.handle_time_request(tokens)

                    case "352" | "315":
                        await self.handle_who_reply(tokens)

                    case "311" | "312" | "313" | "317" | "319" | "301" | "671" | "338" | "318" | "330":
                        await self.handle_whois_replies(tokens.command, tokens)

                    case "332" | "333":
                        self.handle_topic(tokens)

                    case "367":  
                        self.handle_banlist(tokens)
                            
                    case "368":  
                        self.handle_endofbanlist(tokens)

                    case "322":  # Channel list
                        await self.handle_list_response(tokens)
                        await self.channel_window.update_channel_info(tokens.params[1], tokens.params[2], tokens.params[3])
                    case "323":  # End of channel list
                        await self.save_channel_list_to_file()
                        await self.channel_window.stop_progress_bar()

                    case "KICK":
                        await self.handle_kick_event(tokens)
                    case "NOTICE":
                        await self.handle_notice_message(tokens)
                    case "PRIVMSG":
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
                        print(f"sent PONG: {ping_param}")
                    case "CAP":
                        await self.handle_cap_main(tokens)
                    case "PONG":
                        self.handle_pong(tokens)
                    case _:
                        print(f"Debug: Unhandled command {tokens.command}. Full line: {line}")
                        if line.startswith(f":{self.server}"):
                            await self.handle_server_message(line)

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
        
        # Determine script directory
        script_directory = os.path.dirname(os.path.abspath(__file__))
        
        logs_directory = os.path.join(script_directory, 'Logs')
        
        try:
            # Create the Logs directory if it doesn't exist
            os.makedirs(logs_directory, exist_ok=True)

            # Construct the full path for the log file inside the Logs directory
            filename = os.path.join(logs_directory, f'irc_log_{self.sanitize_channel_name(channel)}.txt')

            with open(filename, 'a', encoding='utf-8') as file:
                file.write(log_line)
        except Exception as e:
            print(f"Error logging message: {e}")

    async def command_parser(self, user_input):
        args = user_input[1:].split() if user_input.startswith('/') else []
        primary_command = args[0] if args else None

        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')

        match primary_command:
            case "join":
                channel_name = args[1]
                await self.join_channel(channel_name)

            case "query":  # open a DM with a user
                if len(args) < 2:
                    self.gui.insert_text_widget(f"{timestamp}Error: Please provide a nickname for the query command.\r\n")
                    return

                nickname = args[1]
                if nickname not in self.joined_channels:
                    # Add the DM to the channel list
                    self.joined_channels.append(nickname)
                    self.gui.channel_lists[self.server] = self.joined_channels
                    self.update_gui_channel_list()
                    self.gui.insert_text_widget(f"{timestamp}Opened DM with {nickname}.\r\n")
                else:
                    self.gui.insert_text_widget(f"{timestamp}You already have a DM open with {nickname}.\r\n")

            case "cq":  # close a private message (query) with a user
                if len(args) < 2:
                    # Display an error message if not enough arguments are provided
                    self.update_message_text(f"{timestamp}Usage: /cq <nickname>\r\n")
                else:
                    nickname = args[1]

                    # Check if the DM exists in the list of open channels
                    if nickname in self.joined_channels:
                        # Remove the DM from the list of joined channels
                        self.joined_channels.remove(nickname)

                        # Remove the DM's messages from the channel_messages dictionary
                        if self.server in self.channel_messages and nickname in self.channel_messages[self.server]:
                            del self.channel_messages[self.server][nickname]

                        # Update the GUI's list of channels
                        self.update_gui_channel_list()

                        # Display a message indicating the DM was closed
                        self.gui.insert_text_widget(f"Private message with {nickname} closed.\r\n")
                    else:
                        self.gui.insert_text_widget(f"No open private message with {nickname}.\r\n")

            case "quote":  # sends raw IRC message to the server
                if len(args) < 2:
                    self.gui.insert_text_widget(f"{timestamp}Error: Please provide a raw IRC command after /quote.\r\n")
                    return

                raw_command = " ".join(args[1:])
                await self.send_message(raw_command)
                self.gui.insert_text_widget(f"{timestamp}Sent raw command: {raw_command}\r\n")

            case "away":  # set the user as away
                away_message = " ".join(args[1:]) if len(args) > 1 else None
                if away_message:
                    await self.send_message(f"AWAY :{away_message}")
                    self.gui.insert_text_widget(f"{timestamp}You are now set as away: {away_message}\r\n")
                else:
                    await self.send_message("AWAY")
                    self.gui.insert_text_widget(f"{timestamp}You are now set as away.\r\n")

            case "back":  # remove the "away" status
                await self.send_message("AWAY")
                self.gui.insert_text_widget(f"{timestamp}You are now back and no longer set as away.\r\n")

            case "msg":  # send a private message to a user
                if len(args) < 3:
                    # Display an error message if not enough arguments are provided
                    self.update_message_text(f"{timestamp}Usage: /msg <nickname> <message>\r\n")
                else:
                    nickname = args[1]
                    message = " ".join(args[2:])
                    await self.send_message(f"PRIVMSG {nickname} :{message}")
                    self.gui.insert_text_widget(f'<{self.nickname} -> {nickname}> {message}\r\n')

            case "CTCP":
                if len(args) < 3:
                    self.gui.insert_text_widget(f"{timestamp}Error: Please provide a nickname and CTCP command.\r\n")
                    return
                target_nick = args[1]
                ctcp_command = args[2]
                await self.send_ctcp_request(target_nick, ctcp_command)

            case "mode":
                if len(args) < 2:
                    self.gui.insert_text_widget(f"{timestamp}Error: Please provide a mode.\r\n")
                    self.gui.insert_text_widget("Usage: /mode [+|-][mode flags] [target] [channel]\r\n")
                    self.gui.insert_text_widget("Example for channel: /mode +o #channel_name\r\n")
                    self.gui.insert_text_widget("Example for user: /mode +o username #channel_name\r\n")
                    self.gui.insert_text_widget("If no channel is specified, the mode will be set for the current channel.\r\n")
                    return

                mode = args[1]
                target = None  # Initialize target to None
                channel = self.current_channel  # Default to current channel

                if len(args) > 2:
                    possible_target = args[2]
                    # Check if the third argument is a channel or a user
                    if possible_target.startswith(tuple(self.chantypes)):
                        channel = possible_target
                    else:
                        target = possible_target

                if len(args) > 3:
                    # If we have a fourth argument, it should be the channel
                    channel = args[3]

                if not channel:
                    self.gui.insert_text_widget(f"{timestamp}Error: No channel selected or provided.\r\n")
                    return

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
                    self.gui.insert_text_widget(f"No channel selected. Use /join to join a channel.\r\n")

            case "list":
                await self.send_message("LIST")
                # Create the channel list window
                self.show_channel_list_window()

            case "ch":
                for channel in self.joined_channels:
                    self.gui.insert_text_widget(f'{channel}\r\n')

            case "sw":
                channel_name = args[1]
                if channel_name in self.joined_channels:
                    self.current_channel = channel_name
                    await self.display_last_messages(self.current_channel)
                    self.gui.highlight_nickname()
                else:
                    self.gui.insert_text_widget(f"Not a member of channel {channel_name}\r\n")

            case "topic":
                # Use this line to join all the arguments after the first one (the command "topic")
                # This allows for multi-word topics
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
                    self.gui.insert_text_widget(f"{timestamp}Error: Please provide a new nickname.\r\n")
                    return
                new_nick = args[1]
                await self.change_nickname(new_nick, is_from_token=False)

            case "ping":
                await self.ping_server()

            case "sa":
                if len(args) < 2:
                    self.gui.insert_text_widget(f"{timestamp}Error: Please provide a message to send to all channels.\r\n")
                    return
                message = " ".join(args[1:])
                await self.send_message_to_all_channels(message)

            case "quit":
                await self.gui.send_quit_to_all_clients()
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

            case None:
                if self.current_channel:
                    await self.send_message(f'PRIVMSG {self.current_channel} :{user_input}')
                    self.gui.insert_text_widget(f"{timestamp}<{self.nickname}> {user_input}\r\n")
                    self.gui.highlight_nickname()
                    self.gui.insert_and_scroll()

                    # Check if it's a DM or channel
                    if self.current_channel.startswith(self.chantypes):  # It's a channel
                        if self.current_channel not in self.channel_messages:
                            self.channel_messages[self.current_channel] = []
                        self.channel_messages[self.current_channel].append(f"{timestamp}<{self.nickname}> {user_input}\r\n")

                    else:  # It's a DM
                        server_name = self.server  # Replace this with the actual server name if needed
                        if server_name not in self.channel_messages:
                            self.channel_messages[server_name] = {}
                        if self.current_channel not in self.channel_messages[server_name]:
                            self.channel_messages[server_name][self.current_channel] = []
                        self.channel_messages[server_name][self.current_channel].append(f"{timestamp}<{self.nickname}> {user_input}\r\n")

                    # Trim the messages list if it exceeds 200 lines
                    messages = self.channel_messages.get(server_name, {}).get(self.current_channel, []) if not self.current_channel.startswith("#") else self.channel_messages.get(self.current_channel, [])
                    if len(messages) > 200:
                        messages = messages[-200:]

                    # Log the sent message using the new logging method
                    self.log_message(self.current_channel, self.nickname, user_input, is_sent=True)

                else:
                    self.gui.insert_text_widget(f"No channel selected. Use /join to join a channel.\r\n")

        return True

    def ignore_user(self, args):
        user_to_ignore = " ".join(args[1:])
        if user_to_ignore not in self.ignore_list:
            self.ignore_list.append(user_to_ignore)
            self.gui.insert_text_widget(f"You've ignored {user_to_ignore}.\r\n")
            self.save_ignore_list()
        else:
            self.gui.insert_text_widget(f"{user_to_ignore} is already in your ignore list.\r\n")

    def unignore_user(self, args):
        if len(args) < 2:  # Check if the user has provided the username to unignore
            self.gui.insert_text_widget("Usage: unignore <username>\r\n")
            return

        user_to_unignore = args[1]
        if user_to_unignore in self.ignore_list:
            self.ignore_list.remove(user_to_unignore)
            self.gui.insert_text_widget(f"You've unignored {user_to_unignore}.\r\n")
            self.save_ignore_list()
        else:
            self.gui.insert_text_widget(f"{user_to_unignore} is not in your ignore list.\r\n")

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
        if os.path.exists("ignore_list.txt"):
            with open(file_path, "r", encoding='utf-8') as f:
                self.ignore_list = [line.strip() for line in f.readlines()]

    def reload_ignore_list(self):
        self.ignore_list = []
        self.load_ignore_list()
        self.gui.insert_text_widget(f"Ignore List reloaded.\r\n")

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
        self.gui.insert_text_widget(ban_info)

    def handle_endofbanlist(self, tokens):
        """
        Handle the RPL_ENDOFBANLIST reply, signaling the end of the ban list.
        """
        channel = tokens.params[1]
        
        # Notify the user that the ban list has ended
        end_message = f"End of ban list for channel: {channel}\r\n"
        self.gui.insert_text_widget(end_message) 

    async def append_to_channel_history(self, channel, message, is_action=False):
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
        formatted_message = f"{timestamp}<{self.nickname}> {message}\r\n"

        # Initialize the channel's history if it does not exist yet
        if channel not in self.channel_messages:
            self.channel_messages[channel] = []
        
        # Append the message to the channel's history
        self.channel_messages[channel].append(formatted_message)
        
        # Trim the history if it exceeds 200 lines
        if len(self.channel_messages[channel]) > 200:
            self.channel_messages[channel] = self.channel_messages[channel][-200:]

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
            formatted_message = f"{timestamp}<{self.nickname}> {line}\r\n"
            await self.send_message(f'PRIVMSG {self.current_channel} :{line}')
            self.gui.insert_text_widget(formatted_message)
            self.gui.insert_and_scroll()
            self.gui.highlight_nickname()
            await asyncio.sleep(0.4)
            await self.append_to_channel_history(self.current_channel, line)

    async def cowsay_custom_message(self, message):
        """Wrap a custom message using the cowsay format."""
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
        wrapped_message = self.wrap_text(message)
        cowsay_output = self.cowsay(wrapped_message)
        
        for line in cowsay_output.split('\n'):
            formatted_message = f"{timestamp}<{self.nickname}> {line}\r\n"
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
            formatted_message = f"{timestamp}<{self.nickname}> {line}\r\n"
            await self.send_message(f'PRIVMSG {self.current_channel} :{line}')
            self.gui.insert_text_widget(formatted_message)
            self.gui.insert_and_scroll()
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
        if target:
            await self.send_message(f'MODE {channel} {mode} {target}')
        else:
            await self.send_message(f'MODE {channel} {mode}')

    async def request_send_topic(self, new_topic=None):
        if self.current_channel:
            if new_topic:
                # Set the new topic
                await self.send_message(f'TOPIC {self.current_channel} :{new_topic}')
            else:
                # Request the current topic
                await self.send_message(f'TOPIC {self.current_channel}')
        else:
            self.gui.insert_text_widget("No channel selected. Use /join to join a channel.\r\n")

    async def refresh_user_list_for_current_channel(self):
        if self.current_channel:
            await self.send_message(f'NAMES {self.current_channel}')
        else:
            self.gui.insert_text_widget("No channel selected. Use /join to join a channel.\r\n")

    async def change_nickname(self, new_nick, is_from_token=False):
        if not is_from_token:
            await self.send_message(f'NICK {new_nick}')
        self.nickname = new_nick  # update local state
        self.gui.update_nick_channel_label() 

    async def ping_server(self):
        await self.send_message(f'PING {self.server}')

    async def send_message_to_all_channels(self, message):
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S] ')
        formatted_message = f"{timestamp}<{self.nickname}> {message}\r\n"
        
        for channel in self.joined_channels:
            await self.send_message(f'PRIVMSG {channel} :{message}')
            
            # Save the message to the channel_messages dictionary
            if channel not in self.channel_messages:
                self.channel_messages[channel] = []
            self.channel_messages[channel].append(formatted_message)
            
            # Trim the messages list if it exceeds 200 lines
            if len(self.channel_messages[channel]) > 200:
                self.channel_messages[channel] = self.channel_messages[channel][-200:]
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
        self.gui.insert_text_widget(f"{timestamp}{formatted_message}\r\n")
        self.gui.highlight_nickname()
        self.gui.insert_and_scroll()

        # Save the action message to the channel_messages dictionary
        if self.current_channel not in self.channel_messages:
            self.channel_messages[self.current_channel] = []
        self.channel_messages[self.current_channel].append(f"{timestamp}{formatted_message}\r\n")

        # Trim the messages list if it exceeds 200 lines
        if len(self.channel_messages[self.current_channel]) > 200:
            self.channel_messages[self.current_channel] = self.channel_messages[self.current_channel][-200:]

    def display_help(self):
        # Categories and their associated commands
        categories = {
            "Channel Management": [
                "/join <channel> - Joins a channel",
                "/part <channel> - Leaves a channel",
                "/ch - Shows channels joined",
                "/sw <channel> - Switches to a channel",
                "/topic - Requests the topic for the current channel",
                "/names - Refreshes the user list for the current channel",
            ],
            "Private Messaging": [
                "/query <nickname> - Opens a DM with a user",
                "/cq <nickname> - Closes a DM with a user",
                "/msg <nickname> <message> - Sends a private message to a user",
            ],
            "User Commands": [
                "/nick <new nickname> - Changes the user's nickname",
                "/away [message] - Sets the user as away",
                "/back - Removes the 'away' status",
                "/who <mask> - Lists users matching a mask",
                "/whois <nickname> - Shows information about a user",
                "/me <action text> - Sends an action to the current channel",
            ],
            "Server Interaction": [
                "/ping - Pings the currently selected server",
                "/quote <IRC command> - Sends raw IRC message to the server",
                "/CTCP <nickname> <command> - Sends a CTCP request",
                "/mode <mode> [channel] - Sets mode for user (optionally in a specific channel)",
            ],
            "Broadcasting": [
                "/sa <message> - Sends a message to all channels",
            ],
            "Help and Exiting": [
                "/quit - Closes connection and client",
                "/help - Redisplays this message",
            ],
        }

        # Display the categorized commands
        for category, commands in categories.items():
            self.gui.insert_text_widget(f"\n{category}:\n")
            self.gui.insert_and_scroll()
            for cmd in commands:
                self.gui.insert_text_widget(f"{cmd}\r\n")
                self.gui.insert_and_scroll()

    def set_gui(self, gui):
        self.gui = gui

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
        if self.nickserv_password:
            await self.send_message(f'PRIVMSG NickServ :IDENTIFY {self.nickserv_password}')

        asyncio.create_task(self.keep_alive())
        asyncio.create_task(self.handle_incoming_message())

        await self.main_loop()

    def display_last_messages(self, channel, num=200, server_name=None):
        if server_name:
            print(f"Server Name: {server_name}")
            messages = self.channel_messages.get(server_name, {}).get(channel, [])
            print(f"[DEBUG] Attempting to display DMs for server: {server_name}, channel: {channel}")
        else:
            messages = self.channel_messages.get(channel, [])
            print(f"[DEBUG] Attempting to display messages for channel: {channel}")

        print(f"[DEBUG] Messages to be displayed: {messages}")
        print(f"[DEBUG] self.channel_messages: {self.channel_messages}")

        for message in messages[-num:]:
            self.gui.insert_text_widget(message)


class IRCGui:
    def __init__(self, master):
        self.master = master
        self.master.title("RudeChat")
        self.master.geometry("1200x800")
        self.master.configure(bg="black")

        # Main frame
        self.frame = tk.Frame(self.master, bg="black")
        self.frame.grid(row=1, column=0, columnspan=2, sticky="nsew")

        # Initialize other instance variables
        self.channel_lists = {}
        self.nickname_colors = {}
        self.clients = {}
        self.channel_topics = {}

        # Server and Topic Frame
        self.server_topic_frame = tk.Frame(self.master, bg="black")
        self.server_topic_frame.grid(row=0, column=0, columnspan=2, sticky='nsew')

        # Server selection dropdown
        self.server_var = tk.StringVar(self.master)
        self.server_dropdown = ttk.Combobox(self.server_topic_frame, textvariable=self.server_var, width=20)
        self.server_dropdown.grid(row=0, column=0, sticky='w')
        self.server_dropdown['values'] = []
        self.server_dropdown.bind('<<ComboboxSelected>>', self.on_server_change)

        # Topic label
        self.current_topic = tk.StringVar(value="Topic: ")
        self.topic_label = tk.Label(self.server_topic_frame, textvariable=self.current_topic, bg="black", fg="white", padx=5, pady=1)
        self.topic_label.grid(row=1, column=0, sticky='w')
        self.topic_label.bind("<Enter>", self.show_topic_tooltip)
        self.topic_label.bind("<Leave>", self.hide_topic_tooltip)
        self.tooltip = None

        # Main text widget
        self.text_widget = ScrolledText(self.frame, wrap='word', bg="black", fg="#C0FFEE")
        self.text_widget.grid(row=0, column=0, sticky="nsew")

        # List frames
        self.list_frame = tk.Frame(self.frame, bg="black")
        self.list_frame.grid(row=0, column=1, sticky="nsew")

        # User frame
        self.user_frame = tk.Frame(self.list_frame, bg="black")
        self.user_frame.grid(row=0, column=0, sticky="nsew")

        self.user_label = tk.Label(self.user_frame, text="Users", bg="black", fg="white")
        self.user_label.grid(row=0, column=0, sticky='ew')

        self.user_listbox = tk.Listbox(self.user_frame, height=25, width=16, bg="black", fg="#39ff14")
        self.user_scrollbar = tk.Scrollbar(self.user_frame, orient="vertical", command=self.user_listbox.yview)
        self.user_listbox.config(yscrollcommand=self.user_scrollbar.set)
        self.user_listbox.grid(row=1, column=0, sticky='nsew')
        self.user_scrollbar.grid(row=1, column=1, sticky='ns')

        # Channel frame
        self.channel_frame = tk.Frame(self.list_frame, bg="black")
        self.channel_frame.grid(row=1, column=0, sticky="nsew")

        self.channel_label = tk.Label(self.channel_frame, text="Channels", bg="black", fg="white")
        self.channel_label.grid(row=0, column=0, sticky='ew')

        self.channel_listbox = tk.Listbox(self.channel_frame, height=20, width=16, bg="black", fg="white")
        self.channel_scrollbar = tk.Scrollbar(self.channel_frame, orient="vertical", command=self.channel_listbox.yview)
        self.channel_listbox.config(yscrollcommand=self.channel_scrollbar.set)
        self.channel_listbox.grid(row=1, column=0, sticky='nsew')
        self.channel_scrollbar.grid(row=1, column=1, sticky='ns')
        self.channel_listbox.bind('<ButtonRelease-1>', self.on_channel_click)

        # Server frame
        self.server_frame = tk.Frame(self.master, height=100, bg="black")
        self.server_frame.grid(row=2, column=0, columnspan=2, sticky='ew')

        # Configure column to expand
        self.server_frame.grid_columnconfigure(0, weight=1)

        self.server_text_widget = ScrolledText(self.server_frame, wrap='word', height=5, bg="black", fg="#7882ff")
        self.server_text_widget.grid(row=0, column=0, sticky='nsew')

        # Entry widget
        self.entry_widget = tk.Entry(self.master)
        self.entry_widget.grid(row=3, column=1, sticky='ew')
        self.entry_widget.bind('<Tab>', self.handle_tab_complete)

        # Label for nickname and channel
        self.current_nick_channel = tk.StringVar(value="Nickname | #Channel" + " &>")
        self.nick_channel_label = tk.Label(self.master, textvariable=self.current_nick_channel, bg="black", fg="white", padx=5, pady=1)
        self.nick_channel_label.grid(row=3, column=0, sticky='w')

        # Initialize the AsyncIRCClient and set the GUI reference
        self.irc_client = AsyncIRCClient(self.text_widget, self.server_text_widget, self.entry_widget, self.master, self)

        # Configure grid weights
        self.master.grid_rowconfigure(0, weight=0)
        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_columnconfigure(0, weight=0)
        self.master.grid_columnconfigure(1, weight=1)

        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=0)

        self.list_frame.grid_rowconfigure(0, weight=1)
        self.list_frame.grid_columnconfigure(0, weight=0)

        self.user_frame.grid_rowconfigure(1, weight=1)
        self.user_frame.grid_columnconfigure(0, weight=1)

        self.channel_frame.grid_rowconfigure(1, weight=1)
        self.channel_frame.grid_columnconfigure(0, weight=1)

    def add_server_to_combo_box(self, server_name):
        # Get the current list of servers from the combo box
        current_servers = list(self.server_dropdown['values'])
        
        # Add the new server_name to the list if it's not already there
        if server_name not in current_servers:
            current_servers.append(server_name)
            
        # Update the combo box with the new list of servers
        self.server_dropdown['values'] = current_servers

    def show_topic_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
        x, y, _, _ = self.topic_label.bbox("insert")
        x += self.topic_label.winfo_rootx() + 25
        y += self.topic_label.winfo_rooty() + 25
        self.tooltip = tk.Toplevel(self.topic_label)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.current_topic.get(), justify='left')
        label.pack()

    def hide_topic_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
        self.tooltip = None

    def insert_text_widget(self, message):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, message)
        self.text_widget.config(state=tk.DISABLED)

    def insert_server_widget(self, message):
        self.server_text_widget.config(state=tk.NORMAL)
        self.server_text_widget.insert(tk.END, message)
        self.server_text_widget.config(state=tk.DISABLED)

    async def send_quit_to_all_clients(self):
        for irc_client in self.clients.values():
            await asyncio.sleep(1)
            await irc_client.send_message('QUIT')

    def add_client(self, server_name, irc_client):
        print(f"Adding client: {server_name}")  # Debugging line
        self.clients[server_name] = irc_client
        current_servers = list(self.server_dropdown['values'])
        current_servers.append(server_name)
        self.server_dropdown['values'] = current_servers
        self.server_var.set(server_name)  # Set the current server
        self.channel_lists[server_name] = irc_client.joined_channels
        print(f"Server Dropdown Values: {self.server_dropdown['values']}")  # Debugging line
        print(f"Current Clients: {self.clients.keys()}")  # Debugging line

    def on_server_change(self, event):
        selected_server = self.server_var.get()
        self.irc_client = self.clients.get(selected_server, None)
        if self.irc_client:
            self.irc_client.set_gui(self)
            self.irc_client.update_gui_channel_list()
        # Update the user list in GUI
        selected_channel = self.irc_client.current_channel
        if selected_channel:
            self.irc_client.update_gui_user_list(selected_channel)

    async def init_client_with_config(self, config_file, fallback_server_name):
        irc_client = AsyncIRCClient(self.text_widget, self.server_text_widget, self.entry_widget, self.master, self)
        await irc_client.read_config(config_file)
        await irc_client.connect()

        # Use the server_name if it is set in the configuration, else use fallback_server_name
        server_name = irc_client.server_name if irc_client.server_name else fallback_server_name
        
        self.add_client(server_name, irc_client)
        if irc_client.nickserv_password:
            await irc_client.send_message(f'PRIVMSG NickServ :IDENTIFY {irc_client.nickserv_password}')
        asyncio.create_task(irc_client.keep_alive())
        asyncio.create_task(irc_client.handle_incoming_message())

        async def on_enter_key(event):
            user_input = self.entry_widget.get()
            self.entry_widget.delete(0, tk.END)
            await self.irc_client.command_parser(user_input)
            self.text_widget.see(tk.END)

        loop = asyncio.get_event_loop()
        self.entry_widget.bind('<Return>', lambda event: loop.create_task(on_enter_key(event)))

    def on_channel_click(self, event):
        loop = asyncio.get_event_loop()
        # Get index of clicked item
        clicked_index = self.channel_listbox.curselection()
        if clicked_index:
            clicked_channel = self.channel_listbox.get(clicked_index[0])
            loop.create_task(self.switch_channel(clicked_channel))

            # Clear the background color changes of the clicked channel only
            self.channel_listbox.itemconfig(clicked_index, {'bg': 'black'})
            self.highlight_nickname()

    async def switch_channel(self, channel_name):
        print(f"[DEBUG] Attempting to switch to channel: {channel_name}")
        print(f"[DEBUG] Current channel_messages: {self.irc_client.channel_messages}")

        server = self.irc_client.server  # Assume the server is saved in the irc_client object
        print(f"{self.irc_client.server}")

        # Clear the text window
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.config(state=tk.DISABLED)

        # First, check if it's a DM
        if server in self.irc_client.channel_messages and \
           channel_name in self.irc_client.channel_messages[server]:
            print(f"[DEBUG] This is a DM with {channel_name} on server {server}")

            # Set current channel to the DM
            self.irc_client.current_channel = channel_name
            self.update_nick_channel_label()

            # Display the last messages for the current DM
            print(f"Debug: server = {server}")
            self.irc_client.display_last_messages(channel_name, server_name=server)
            self.insert_and_scroll()
            print(f"server: {server}")
            self.highlight_nickname()

            # No topic for DMs
            self.current_topic.set("Topic: N/A")

        # Then, check if it's a channel
        elif channel_name in self.irc_client.joined_channels:
            self.irc_client.current_channel = channel_name
            self.update_nick_channel_label()

            # Update topic label
            current_topic = self.channel_topics.get(channel_name, "N/A")
            self.current_topic.set(f"Topic: {current_topic}")

            # Display the last messages for the current channel
            self.irc_client.display_last_messages(self.irc_client.current_channel)
            self.highlight_nickname()

            self.irc_client.update_gui_user_list(channel_name)
            self.insert_and_scroll()
            print(f"Switching to channel {channel_name}. Current topic should be {self.channel_topics.get(channel_name, 'N/A')}")
            print(f"Current channel topics: {self.channel_topics}")

        else:
            self.insert_text_widget(f"Not a member of channel or unknown DM {channel_name}\r\n")

    def insert_and_scroll(self):
        self.text_widget.see(tk.END)
        self.server_text_widget.see(tk.END)

    def update_nick_channel_label(self):
        """Update the label with the current nickname and channel."""
        nickname = self.irc_client.nickname if self.irc_client.nickname else "Nickname"
        channel = self.irc_client.current_channel if self.irc_client.current_channel else "#Channel"
        self.current_nick_channel.set(f"{nickname} | {channel}" + " $>")

    def highlight_nickname(self):
        """Highlight the user's nickname in the text_widget."""
        user_nickname = self.irc_client.nickname
        if not user_nickname:
            return

        # Configure the color for the user's nickname
        self.text_widget.tag_configure("nickname", foreground="#39ff14")

        # Start at the beginning of the text_widget
        start_idx = "1.0"
        while True:
            # Find the position of the next instance of the user's nickname
            start_idx = self.text_widget.search(user_nickname, start_idx, stopindex=tk.END)
            if not start_idx:
                break

            # Calculate the end index based on the length of the nickname
            end_idx = self.text_widget.index(f"{start_idx}+{len(user_nickname)}c")

            # Apply the tag to the found nickname
            self.text_widget.tag_add("nickname", start_idx, end_idx)

            # Update the start index to search from the position after the current found nickname
            start_idx = end_idx

        # Start again at the beginning of the text_widget for other nicknames enclosed in <>
        start_idx = "1.0"
        while True:
            start_idx = self.text_widget.search('<', start_idx, stopindex=tk.END)
            if not start_idx:
                break

            end_idx = self.text_widget.search('>', start_idx, stopindex=tk.END)
            if not end_idx:
                break

            nickname = self.text_widget.get(start_idx + '+1c', end_idx + '-1c')

            # Check if a color for this nickname is already stored, if not, generate and store it
            if nickname not in self.nickname_colors:
                random_color = self.generate_random_color()
                self.nickname_colors[nickname] = random_color

            nickname_color = self.nickname_colors[nickname]
            self.text_widget.tag_add(nickname, start_idx, end_idx + '+1c')  # Include the '>'
            self.text_widget.tag_configure(nickname, foreground=nickname_color)

            # Update the start index to search from the position after the current found nickname
            start_idx = end_idx + '+1c'

    def generate_random_color(self):
        while True:
            # Generate random values for each channel
            r = random.randint(50, 255)
            g = random.randint(50, 255)
            b = random.randint(50, 255)
            
            # Ensure the difference between the maximum and minimum channel values is above a threshold
            if max(r, g, b) - min(r, g, b) > 50:  # 50 is the threshold, you can adjust this value as needed
                return "#{:02x}{:02x}{:02x}".format(r, g, b)

    def trigger_desktop_notification(self, channel_name=None, title="Ping", message_content=None):
        """
        Show a system desktop notification.
        """
        script_directory = os.path.dirname(os.path.abspath(__file__))
        # Check if the application window is the active window
        if self.is_app_focused():  # If the app is focused, return early
            return

        if channel_name:
            # Ensure channel_name is a string and replace problematic characters
            channel_name = str(channel_name).replace("#", "channel ")
            title = f"{title} from {channel_name}"
            if message_content:
                message = f"{channel_name}: {message_content}"
            else:
                message = f"You've been pinged in {channel_name}!"

        icon_path = os.path.join(script_directory, "rude.ico")

        try:
            # Desktop Notification
            notification.notify(
                title=title,
                message=message,
                app_icon=icon_path,  
                timeout=5,  
            )
        except Exception as e:
            print(f"Desktop notification error: {e}")

    def is_app_focused(self):
        return bool(self.master.focus_displayof())

    def handle_tab_complete(self, event):
        """
        Tab complete with cycling through possible matches.
        """
        # Get the current input in the input entry field
        user_input = self.entry_widget.get()
        cursor_pos = self.entry_widget.index(tk.INSERT)

        # Find the partial nick before the cursor position
        partial_nick = ''
        for i in range(cursor_pos - 1, -1, -1):
            char = user_input[i]
            if not char.isalnum() and char not in "_-^[]{}\\`|":
                break
            partial_nick = char + partial_nick

        # Cancel any previous timers
        if hasattr(self, 'tab_completion_timer'):
            self.master.after_cancel(self.tab_completion_timer)

        # Get the user list for the current channel
        current_channel = self.irc_client.current_channel
        if current_channel in self.irc_client.channel_users:
            user_list = self.irc_client.channel_users[current_channel]
        else:
            return

        # Remove @ and + symbols from nicknames
        user_list_cleaned = [nick.lstrip('@+') for nick in user_list]

        # Initialize or update completions list
        if not hasattr(self, 'tab_complete_completions') or not hasattr(self, 'last_tab_time') or (time.time() - self.last_tab_time) > 1.0:
            self.tab_complete_completions = [nick for nick in user_list_cleaned if nick.startswith(partial_nick)]
            self.tab_complete_index = 0

        # Update the time of the last tab press
        self.last_tab_time = time.time()

        if self.tab_complete_completions:
            # Fetch the next completion
            completed_nick = self.tab_complete_completions[self.tab_complete_index]
            remaining_text = user_input[cursor_pos:]
            completed_text = user_input[:cursor_pos - len(partial_nick)] + completed_nick + remaining_text
            self.entry_widget.delete(0, tk.END)
            self.entry_widget.insert(0, completed_text)
            # Cycle to the next completion
            self.tab_complete_index = (self.tab_complete_index + 1) % len(self.tab_complete_completions)

        # Set up a timer to append ": " after half a second if no more tab presses
        self.tab_completion_timer = self.master.after(300, self.append_colon_to_nick)

        # Prevent default behavior of the Tab key
        return 'break'

    def append_colon_to_nick(self):
        current_text = self.entry_widget.get()
        self.entry_widget.delete(0, tk.END)
        self.entry_widget.insert(0, current_text + ": ")


class ChannelListWindow(tk.Toplevel):
    def __init__(self, client, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Channel List")
        self.geometry("790x400")
        
        self.client = client  # The AsyncIRCClient instance
        self.total_channels = 0  # Initialize the total_channels variable
        self.is_destroyed = False  # To check if the window has been destroyed
        
        self.create_widgets()
        
        # Start the periodic UI update
        self.after(100, self.update_ui_periodically)
        
        # Start populating the channel list
        asyncio.create_task(self.populate_channel_list())
        
    def create_widgets(self):
        self.tree = ttk.Treeview(self, columns=("Channel", "Users", "Topic"), show='headings')
        self.tree.heading("Channel", text="Channel")
        self.tree.heading("Users", text="Users")
        self.tree.heading("Topic", text="Topic")
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.close_button = ttk.Button(self, text="Close", command=self.destroy)
        self.close_button.grid(row=1, column=0, columnspan=2, pady=10, padx=10, sticky="ew")
        
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", mode="determinate")
        self.progress_bar.grid(row=2, column=0, columnspan=2, pady=10, padx=10, sticky="ew")
        
        # Make the Treeview and scrollbar resizable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
    async def populate_channel_list(self):
        processed_channels = 0
        processed_channel_names = set()  # To keep track of channels already processed
        
        while True:
            if self.is_destroyed:
                break  # Stop populating if the window is destroyed

            new_total_channels = len(self.client.download_channel_list)

            # Update the total channel count if it has changed
            if new_total_channels != self.total_channels:
                self.total_channels = new_total_channels

            # Populate the list with new channels
            for channel, info in self.client.download_channel_list.items():
                if channel not in processed_channel_names:
                    # Insert the new channel into the Treeview
                    self.tree.insert("", tk.END, values=(channel, info['user_count'], info['topic']))

                    # Mark this channel as processed and increment the counter
                    processed_channel_names.add(channel)
                    processed_channels += 1

                    # Update the progress bar
                    if self.total_channels != 0:
                        progress = (processed_channels / self.total_channels) * 100
                        self.progress_bar["value"] = progress

            await asyncio.sleep(0.1)  # Allow time for more channels to be added

        await self.stop_progress_bar()

    def update_ui_periodically(self):
        if self.is_destroyed:
            return

        # Update the progress bar, Treeview, etc. here
        if self.total_channels != 0:
            progress = (self.processed_channels / self.total_channels) * 100
            self.progress_bar["value"] = progress

        self.after(100, self.update_ui_periodically)

    async def update_channel_info(self, channel_name, user_count, topic):
        self.tree.insert("", tk.END, values=(channel_name, user_count, topic))

    async def stop_progress_bar(self):
        if not self.is_destroyed:
            self.progress_bar.stop()

    def destroy(self):
        self.is_destroyed = True
        super().destroy()


MAX_RETRIES = 5  # Max number of times to retry on semaphore error
RETRY_DELAY = 5  # Time in seconds to wait before retrying

async def initialize_clients(app):
    files = os.listdir()
    config_files = [f for f in files if f.startswith("conf") and f.endswith(".rude")]
    config_files.sort()

    async def try_init_client_with_config(config_file, fallback_server_name, retries=0):
        try:
            await app.init_client_with_config(config_file, fallback_server_name)
        except OSError as e:
            if e.winerror == 121:  # The semaphore timeout error
                retries += 1
                if retries <= MAX_RETRIES:
                    print(f"Semaphore timeout error. Retrying {retries}/{MAX_RETRIES}...")
                    await asyncio.sleep(RETRY_DELAY)
                    await try_init_client_with_config(config_file, fallback_server_name, retries)
                else:
                    print("Max retries reached. Skipping this server.")
            else:
                print(f"An unexpected error occurred: {str(e)}")
        except Exception as e:
            print(f"Failed to connect to {fallback_server_name} due to {e}. Proceeding to the next server.")

    tasks = [try_init_client_with_config(cf, f'Server_{i+1}') for i, cf in enumerate(config_files)]
    await asyncio.gather(*tasks)

    if app.server_dropdown['values']:
        first_server = app.server_dropdown['values'][0]
        app.server_var.set(first_server)
        app.on_server_change(None)

def main():
    root = tk.Tk()
    app = IRCGui(root)

    loop = asyncio.get_event_loop()

    loop.create_task(initialize_clients(app))

    def tk_update():
        try:
            loop.stop()
            loop.run_forever()
        finally:
            loop.stop()
            root.after(100, tk_update)

    root.after(100, tk_update)
    root.mainloop()

if __name__ == '__main__':
    main()
