"""
RudeCli-IRC-C: Rudimentary Command Line Interface IRC Client.
RudeCli assumes config.rude is available and configed properly:

Config Example:

[IRC]
server = irc.libera.chat
port = 6697
ssl_enabled = True
nickname = Rudecli
nickserv_password = your_password_here

You can set your password if you use nickserv to auto-auth.
to use ssl or not you can designate by port: no ssl: 6667 yes ssl: 6697
ssl_enabled = False needs port 6667
ssl_enabled = True needs port 6697(usually)

"""

import ssl
import socket
import sys
import threading
import configparser
import time
import datetime
import irctokens
import re
import os
import curses


class IRCClient:
    def __init__(self):
        self.joined_channels = []
        self.current_channel = ''
        self.channel_messages = {}  # Dictionary to store channel messages
        self.decoder = irctokens.StatefulDecoder() # Create a StatefulDecoder instance
        self.encoder = irctokens.StatefulEncoder() # Create a StatefulEncoder instance

    def read_config(self, config_file):
        config = configparser.ConfigParser()
        config.read(config_file)

        self.server = config.get('IRC', 'server')
        self.port = config.getint('IRC', 'port')
        self.ssl_enabled = config.getboolean('IRC', 'ssl_enabled')
        self.nickname = config.get('IRC', 'nickname')
        self.nickserv_password = config.get('IRC', 'nickserv_password')  # Read NickServ password from the config file

    def connect(self):
        print(f'Connecting to server: {self.server}:{self.port}')

        if self.ssl_enabled:
            context = ssl.create_default_context()
            self.irc = context.wrap_socket(socket.socket(socket.AF_INET6 if ':' in self.server else socket.AF_INET),
                                           server_hostname=self.server)
        else:
            self.irc = socket.socket(socket.AF_INET6 if ':' in self.server else socket.AF_INET)

        self.irc.connect((self.server, self.port))

        # Send necessary IRC commands to register the client with the server
        self.irc.send(bytes(f'NICK {self.nickname}\r\n', 'UTF-8'))
        self.irc.send(bytes(f'USER {self.nickname} 0 * :{self.nickname}\r\n', 'UTF-8'))
        time.sleep(5)
        print(f'Connected to server: {self.server}:{self.port}')

        # Authenticate with NickServ using the stored password
        self.send_message(f'PRIVMSG NickServ :IDENTIFY {self.nickserv_password}')

    def send_message(self, message):
        self.irc.send(bytes(f'{message}\r\n', 'UTF-8'))

    def join_channel(self, channel):
        self.send_message(f'JOIN {channel}')
        self.joined_channels.append(channel)
        self.channel_messages[channel] = []  # Initialize empty list for channel messages
        print(f'Joined channel: {channel}')

    def leave_channel(self, channel):
        self.send_message(f'PART {channel}')
        if channel in self.joined_channels:
            self.joined_channels.remove(channel)
        if channel in self.channel_messages:
            del self.channel_messages[channel]  # Remove channel messages
        print(f'Left channel: {channel}')
        if self.current_channel == channel:
            self.current_channel = ''

    def list_channels(self):
        self.send_message('LIST')

    def keep_alive(self):
        while True:
            time.sleep(190)
            param = self.server
            self.send_message(f'PING {param}')
            print(f'Sent Keep Alive: Ping')

    def handle_incoming_message(self):
        buffer = ""
        while True:
            data = self.irc.recv(4096).decode('UTF-8', errors='ignore')
            if not data:
                break

            buffer += data  # Append new data to the buffer

            # Process complete messages and keep the remaining in the buffer
            while '\r\n' in buffer:
                line, buffer = buffer.split('\r\n', 1)  # Split at the first '\r\n'
                
                try:
                    if len(line.strip()) == 0:  
                        continue
                    tokens = irctokens.tokenise(line)  
                except ValueError as e:
                    self.add_chat_message(f"Error: {e}")
                    continue  # Skip command-less lines

                # Extract sender's nickname
                sender = tokens.hostmask.nickname if tokens.source is not None else None

                # Handle specific commands
                if tokens.command == "PING":
                    # Respond with PONG
                    ping_param = tokens.params[0]
                    pong_response = f'PONG {ping_param}'
                    self.send_message(pong_response)
                    self.add_chat_message(f'PING received: Response: PONG')

                elif tokens.command == "PRIVMSG":
                    target = tokens.params[0]
                    message_content = tokens.params[1]

                    # Check if it's an ACTION message
                    if message_content.startswith("\x01ACTION") and message_content.endswith("\x01"):
                        action_content = message_content[8:-1]
                        action_message = f'* {sender} {action_content}'
                        if target not in self.channel_messages:
                            self.channel_messages[target] = []
                        self.channel_messages[target].append((sender, action_message))
                        if target == self.current_channel:
                            self.add_chat_message(f'{action_message}')
                        else:
                            self.notify_channel_activity(target)  # Notify user about activity

                    else:
                        # Regular PRIVMSG message
                        if target not in self.channel_messages:
                            self.channel_messages[target] = []
                        self.channel_messages[target].append((sender, message_content))
                        if target == self.current_channel:
                            self.add_chat_message(f'<{sender}> {message_content}')
                        else:
                            self.notify_channel_activity(target)  # Notify user about activity

                    # Log the message
                    self.log_message(target, sender, message_content)

                else:
                    # Server message
                    self.add_chat_message(f': {line}')

            # Refresh all windows to reflect the latest changes
            self.refresh_windows()

    def log_message(self, channel, sender, message, is_sent=False):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if is_sent:
            log_line = f'[{timestamp}] <{self.nickname}> {message}'
        else:
            log_line = f'[{timestamp}] <{sender}> {message}'
        directory = f'irc_log_{channel}'
        os.makedirs(directory, exist_ok=True)  # Create directory if it doesn't exist
        filename = f'{directory}/irc_log_{channel.replace("/", "_")}.txt'
        with open(filename, 'a') as file:
            file.write(log_line + '\n')

    def notify_channel_activity(self, channel):
        print(f'Activity in channel {channel}!')

    def display_channel_messages(self):
        if self.current_channel in self.channel_messages:
            messages = self.channel_messages[self.current_channel]
            print(f'Messages in channel {self.current_channel}:')
            for sender, message in messages:
                print(f'<{sender}> {message}')
        else:
            print('No messages to display in the current channel.')

class CursesIRCClient(IRCClient):
    def __init__(self, stdscr):
        super().__init__()
        self.stdscr = stdscr
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        self.setup_windows()

    def setup_windows(self):
        self.status_window = curses.newwin(1, 80, 0, 0)
        self.chat_window = curses.newwin(22, 80, 1, 0)
        self.input_window = curses.newwin(1, 80, 23, 0)

        self.chat_window.scrollok(True)

    def refresh_windows(self):
        self.status_window.refresh()
        self.chat_window.refresh()
        self.input_window.refresh()

    def update_status(self, text):
        self.status_window.clear()
        self.status_window.addstr(0, 0, text)
        self.refresh_windows()

    def add_chat_message(self, text):
        self.chat_window.scroll(1)
        self.chat_window.addstr(21, 0, text)
        self.refresh_windows()

    def start(self):
        self.connect()

        # Start receive and keep alive threads
        receive_thread = threading.Thread(target=self.handle_incoming_message)
        receive_thread.daemon = True
        receive_thread.start()
        stay_alive = threading.Thread(target=self.keep_alive)
        stay_alive.daemon = True
        stay_alive.start()

        while True:
            # Clear the input window and update the status
            self.input_window.clear()
            self.update_status(f'{self.current_channel} $ {self.nickname} ε>')

            # Initialize an empty string to hold user input
            user_input = ""

            while True:
                # Get a character from the user
                ch = self.input_window.getch()

                # If Enter is pressed, break the loop
                if ch == ord('\n'):
                    break
                
                elif ch == curses.KEY_BACKSPACE or ch == 127:  # Handle backspace
                    # Remove last character from user_input
                    user_input = user_input[:-1]
                    
                    # Move the cursor back one position and delete the character
                    y, x = self.input_window.getyx()
                    self.input_window.move(y, x-1)
                    self.input_window.delch()

                else:
                    # Make sure the cursor position doesn't exceed the window width
                    if len(user_input) + len(f'{self.current_channel} $ {self.nickname} ε>') < self.input_window.getmaxyx()[1]:
                        # Append the character to user input and display it
                        user_input += chr(ch)
                        self.input_window.addstr(0, len(user_input) + len(f'{self.current_channel} $ {self.nickname} ε>') - 1, chr(ch))

            # Convert the captured input to a UTF-8 string
            user_input = user_input.encode('utf-8').decode('utf-8')

            # Process the user input
            if user_input.startswith('/join'):
                channel_name = user_input.split()[1]
                self.join_channel(channel_name)
                self.add_chat_message(f'Joined channel: {channel_name}')
            elif user_input.startswith('/leave'):
                channel_name = user_input.split()[1]
                self.leave_channel(channel_name)
                self.add_chat_message(f'Left channel: {channel_name}')
            elif user_input.startswith('/ch'):
                joined_channels_str = ', '.join(self.joined_channels)
                self.add_chat_message(f'Joined channels: {joined_channels_str}')
            elif user_input.startswith('/sw'):
                channel_name = user_input.split()[1]
                self.current_channel = channel_name
                self.add_chat_message(f'Switched to channel {self.current_channel}')
            elif user_input.startswith('/messages'):
                self.display_channel_messages()
            elif user_input.startswith('/quit'):
                self.send_message('QUIT')
                sys.exit(0)
            elif user_input.startswith('/help'):
                help_text = "/join to join a channel, /leave to leave a channel, /ch to list joined channels, /sw <channel> to switch, /messages to show messages, /quit to exit."
                self.add_chat_message(help_text)
            elif self.current_channel:
                self.send_message(f'PRIVMSG {self.current_channel} :{user_input}')
                self.log_message(self.current_channel, self.nickname, user_input, is_sent=True)
                self.add_chat_message(f'<{self.nickname}> {user_input}')
            else:
                self.add_chat_message('You are not in a channel. Use /join <channel> to join a channel.')

            # Refresh all windows to reflect the latest changes
            self.refresh_windows()

def main(stdscr):
    config_file = 'conf.rude'
    irc_client = CursesIRCClient(stdscr)
    irc_client.read_config(config_file)
    irc_client.start()

if __name__ == '__main__':
    curses.wrapper(main)
