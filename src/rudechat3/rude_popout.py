import tkinter as tk
import asyncio
import configparser
import os
import time
import datetime
import json
import re
import random
from threading import Thread
from tkinter import scrolledtext, Listbox, Scrollbar
from .format_decoder import Attribute, decoder

class RudePopOut:
    def __init__(self, root, selected_channel, irc_client, nick_name, main_app):
        self.root = root
        self.selected_channel = selected_channel
        self.irc_client = irc_client
        self.nick_name = nick_name
        self.main_app = main_app
        self.script_directory = os.path.dirname(os.path.abspath(__file__))

        # Load configuration from gui_config.ini
        self.load_configuration()
        self.nickname_colors = self.load_nickname_colors()

        # Apply main_bg_color and main_fg_color to root
        self.root.configure(bg=self.main_bg_color)
        self.root.title(f"{selected_channel}")

        # Create a main frame for the pop-out window
        self.frame = tk.Frame(self.root, bg="black")
        self.frame.grid(row=1, column=0, columnspan=2, sticky="nsew")

        # Main text widget (scrolled text)
        self.text_widget = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD)
        self.text_widget.grid(row=0, column=0, sticky="nsew")
        self.text_widget.configure(bg=self.widgets_bg_color, fg=self.widgets_fg_color)

        # User list frame
        self.user_frame = tk.Frame(self.frame, bg="black")
        self.user_frame.grid(row=0, column=1, sticky="nsew")

        # Label for Users
        self.user_label = tk.Label(self.user_frame, text="Users", bg=self.widgets_bg_color, fg='white')
        self.user_label.grid(row=0, column=0, sticky='ew')

        # User listbox
        self.user_listbox = Listbox(self.user_frame, height=25, width=16, bg=self.widgets_bg_color, fg=self.widgets_fg_color)
        self.user_listbox.grid(row=1, column=0, sticky='nsew')

        # User list scrollbar
        self.user_scrollbar = Scrollbar(self.user_frame, orient="vertical", command=self.user_listbox.yview)
        self.user_listbox.config(yscrollcommand=self.user_scrollbar.set)
        self.user_scrollbar.grid(row=1, column=1, sticky='ns')

        # Entry widget for message input
        self.entry = tk.Entry(self.frame)
        self.entry.grid(row=1, column=0, sticky='ew', padx=10, pady=5)
        self.entry.bind('<Return>', self.send_text)
        self.entry.bind('<Tab>', self.handle_tab_complete)
        self.entry.configure(bg=self.entry_bg_color, fg=self.entry_fg_color, insertbackground=self.entry_insertbackground)

        # Close button (smaller size)
        self.close_button = tk.Button(self.frame, text="Pop In", command=self.close_window, width=8)
        self.close_button.grid(row=1, column=1, sticky='e', padx=(0, 10), pady=5)
        self.close_button.configure(bg=self.button_bg_color, fg=self.button_fg_color)

        # Initialize tab completion related attributes
        self.tab_complete_completions = []
        self.tab_complete_index = 0
        self.last_tab_time = 0
        self.tab_completion_timer = None
        self.tab_complete_terminator = ":"

        self.update_gui_user_list(selected_channel)

    def load_configuration(self):
        # Load configuration from gui_config.ini
        config = configparser.ConfigParser()
        config_file = os.path.join(self.script_directory, 'gui_config.ini')
        config.read(config_file)

        # Load colors from the [GUI] and [WIDGETS] sections
        self.main_fg_color = config.get('GUI', 'main_fg_color')
        self.main_bg_color = config.get('GUI', 'main_bg_color')
        self.widgets_fg_color = config.get('WIDGETS', 'entry_fg')
        self.widgets_bg_color = config.get('WIDGETS', 'entry_bg')
        self.entry_fg_color = config.get('WIDGETS', 'entry_fg')
        self.entry_bg_color = config.get('WIDGETS', 'entry_bg')
        self.entry_insertbackground = config.get('WIDGETS', 'entry_insertbackground')
        self.button_fg_color = config.get('WIDGETS', 'entry_fg')
        self.button_bg_color = config.get('WIDGETS', 'entry_bg')
        self.user_nickname_color = config.get('GUI', 'main_nickname_color', fallback='#39ff14')
        self.generate_nickname_colors = config.getboolean('GUI', 'generate_nickname_colors', fallback=True)

    def send_text(self, event=None):
        try:
            user_text = self.entry.get()
            timestamp = datetime.datetime.now().strftime('[%H:%M:%S]')
            if user_text:
                # Insert text in the main text widget
                self.insert_text(f"{timestamp} <{self.nick_name}> {user_text}\n")
                self.entry.delete(0, tk.END)

                # Determine the server and current channel
                server = self.irc_client.server
                current_channel = self.selected_channel

                # Update channel_messages dictionary
                if server not in self.irc_client.channel_messages:
                    self.irc_client.channel_messages[server] = {}
                if current_channel not in self.irc_client.channel_messages[server]:
                    self.irc_client.channel_messages[server][current_channel] = []

                self.irc_client.channel_messages[server][current_channel].append(f"{timestamp} <{self.nick_name}> {user_text}\n")

                self.log_message(self.irc_client.server_name, current_channel, self.nick_name, user_text, is_sent=True)

                # Send the message through the IRC client
                asyncio.run_coroutine_threadsafe(
                    self.irc_client.send_message(f"PRIVMSG {current_channel} :{user_text}"), 
                    self.irc_client.loop
                )
                self.highlight_nickname()
        except Exception as e:
            print(f"Exception in send_text: {e}")

    def close_window(self):
        # Add the channel back to the channel_listbox
        self.main_app.channel_listbox.insert(tk.END, self.selected_channel)
        # Remove the channel and window from the popped_out_channels and pop_out_windows
        if self.selected_channel in self.main_app.popped_out_channels:
            self.main_app.popped_out_channels.remove(self.selected_channel)
        if self.selected_channel in self.main_app.pop_out_windows:
            del self.main_app.pop_out_windows[self.selected_channel]
        # Close the window
        self.root.destroy()

    def update_gui_user_list(self, channel):
        # Clear existing items in user listbox
        self.user_listbox.delete(0, tk.END)
        
        # Populate with users for the given channel
        for user in self.irc_client.channel_users.get(channel, []):
            self.user_listbox.insert(tk.END, user)

    def load_nickname_colors(self):
        nickname_colors_path = os.path.join(self.script_directory, 'nickname_colours.json')

        try:
            with open(nickname_colors_path, 'r') as file:
                nickname_colors = json.load(file)
            return nickname_colors
        except FileNotFoundError:
            print(f"Nickname colors file not found at {nickname_colors_path}. Returning an empty dictionary.")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in nickname colors file: {e}. Returning an empty dictionary.")
            return {}
        except Exception as e:
            print(f"An unexpected error occurred while loading nickname colors: {e}. Returning an empty dictionary.")
            return {}

    def highlight_nickname(self):
        """Highlight the user's nickname in the text_widget."""
        user_nickname = self.irc_client.nickname
        if not user_nickname:
            return

        # Configure the color for the user's nickname
        self.text_widget.tag_configure("nickname", foreground=self.user_nickname_color)

        # Start at the beginning of the text_widget
        start_idx = "1.0"
        while True:
            # Find the position of the next instance of the user's nickname
            start_idx = self.text_widget.search(user_nickname, start_idx, stopindex=tk.END, regexp=True, nocase=True)
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
            # Find the opening '<'
            start_idx = self.text_widget.search('<', start_idx, stopindex=tk.END)
            if not start_idx:
                break
            # Find the closing '>' ensuring no newlines between
            end_idx = self.text_widget.search('>', start_idx, f"{start_idx} lineend")
            if end_idx:
                end_idx = f"{end_idx}+1c"  # Include the '>' character
                # Extract the nickname with '<' and '>'
                nickname_with_brackets = self.text_widget.get(start_idx, end_idx)

                # If nickname doesn't have an assigned color, generate one
                if self.generate_nickname_colors == True:
                    if nickname_with_brackets not in self.nickname_colors:
                        self.nickname_colors[nickname_with_brackets] = self.generate_random_color()
                    nickname_color = self.nickname_colors[nickname_with_brackets]
                elif self.generate_nickname_colors == False:
                    if nickname_with_brackets not in self.nickname_colors:
                        self.nickname_colors[nickname_with_brackets] = self.main_fg_color
                    nickname_color = self.nickname_colors[nickname_with_brackets]

                # If it's the main user's nickname, set color to green
                if nickname_with_brackets == f"<{self.irc_client.nickname}>":
                    nickname_color = self.user_nickname_color

                self.text_widget.tag_configure(f"nickname_{nickname_with_brackets}", foreground=nickname_color)
                self.text_widget.tag_add(f"nickname_{nickname_with_brackets}", start_idx, end_idx)
                start_idx = end_idx
            else:
                start_idx = f"{start_idx}+1c"
        self.insert_and_scroll()

    def generate_random_color(self):
        while True:
            # Generate random values for each channel
            r = random.randint(50, 255)
            g = random.randint(50, 255)
            b = random.randint(50, 255)
            
            # Ensure the difference between the maximum and minimum channel values is above a threshold
            if max(r, g, b) - min(r, g, b) > 50:  # 50 is the threshold, you can adjust this value as needed
                return "#{:02x}{:02x}{:02x}".format(r, g, b)

    def handle_tab_complete(self, event):
        """
        Tab complete with cycling through possible matches.
        """
        # Get the current input in the entry field
        user_input = self.entry.get()
        cursor_pos = self.entry.index(tk.INSERT)

        # Find the partial nick before the cursor position
        partial_nick = ''
        for i in range(cursor_pos - 1, -1, -1):
            char = user_input[i]
            if not char.isalnum() and char not in "_-^[]{}\\`|":
                break
            partial_nick = char + partial_nick

        # Cancel any previous timers
        if self.tab_completion_timer is not None:
            self.root.after_cancel(self.tab_completion_timer)

        # Get the user list for the current channel
        current_channel = self.selected_channel
        if current_channel in self.irc_client.channel_users:
            user_list = self.irc_client.channel_users[current_channel]
        else:
            return

        # Remove @ and + symbols from nicknames
        user_list_cleaned = [nick.lstrip('~&@%+') for nick in user_list]

        # Initialize or update completions list
        if not self.tab_complete_completions or (time.time() - self.last_tab_time) > 1.0:
            self.tab_complete_completions = [nick for nick in user_list_cleaned if nick.startswith(partial_nick)]
            self.tab_complete_index = 0

        # Update the time of the last tab press
        self.last_tab_time = time.time()

        if self.tab_complete_completions:
            # Fetch the next completion
            completed_nick = self.tab_complete_completions[self.tab_complete_index]
            remaining_text = user_input[cursor_pos:]
            completed_text = user_input[:cursor_pos - len(partial_nick)] + completed_nick + remaining_text
            self.entry.delete(0, tk.END)
            self.entry.insert(0, completed_text)
            # Cycle to the next completion
            self.tab_complete_index = (self.tab_complete_index + 1) % len(self.tab_complete_completions)

        # Set up a timer to append ": " after half a second if no more tab presses
        self.tab_completion_timer = self.root.after(250, self.append_colon_to_nick)

        # Prevent default behavior of the Tab key
        return 'break'

    def append_colon_to_nick(self):
        current_text = self.entry.get()
        self.entry.delete(0, tk.END)
        self.entry.insert(0, current_text + self.tab_complete_terminator + " ")

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
                log_line = f'[{timestamp}] <{self.nick_name}> {lines[0]}\n'
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
                log_line += f'           <{sender if is_sent else self.nick_name}> {line}\n'

        # Determine script directory
        script_directory = os.path.dirname(os.path.abspath(__file__))

        logs_directory = os.path.join(script_directory, 'Logs')

        try:
            if channel == self.nick_name:
                channel = sender
            # Create the Logs directory if it doesn't exist
            os.makedirs(logs_directory, exist_ok=True)

            # Construct the full path for the log file inside the Logs directory
            filename = os.path.join(logs_directory, f'irc_log_{server}_{self.sanitize_channel_name(channel)}.txt')

            with open(filename, 'a', encoding='utf-8') as file:
                file.write(log_line)
        except Exception as e:
            print(f"Error logging message: {e}")

    def insert_and_scroll(self):
        self.text_widget.see(tk.END)

    def insert_text(self, message):
        try:
            urls = self.find_urls(message)

            # Set the Text widget state to NORMAL before inserting and configuring tags
            self.text_widget.config(state=tk.NORMAL)

            formatted_text = decoder(message)

            # Run URL tagging in a separate thread
            url_thread = Thread(target=self.tag_urls_async, args=(urls,))
            url_thread.start()

            self.tag_text(formatted_text)
        except Exception as e:
            print(f"Exception in insert_text {e}")

    def tag_text(self, formatted_text):
        # Initialize a cache for tag configurations to avoid redundant setups
        tag_cache = {}
        
        # Initialize variables to track current tag configuration
        current_tag_name = None
        current_tag_config = {}

        for text, attributes in formatted_text:
            # Create a tag name based on the attributes
            tag_name = "_".join(str(attr) for attr in attributes)

            # Check if the tag configuration has changed
            if tag_name not in tag_cache:
                # If tag configuration is new, determine and cache it
                tag_config = self.configure_tag_based_on_attributes(attributes)
                self.text_widget.tag_configure(tag_name, **tag_config)
                tag_cache[tag_name] = tag_config
            else:
                # Use cached configuration
                tag_config = tag_cache[tag_name]

            # Update current tag configuration if it has changed
            if tag_name != current_tag_name:
                current_tag_name = tag_name
                current_tag_config = tag_config

            # Insert the formatted text with the current tag
            self.text_widget.insert(tk.END, text, (current_tag_name,))

    def configure_tag_based_on_attributes(self, attributes):
        # This method configures tag based on attributes efficiently
        tag_config = {}
        if any(attr.bold for attr in attributes):
            tag_config['font'] = (self.font_family, self.font_size, 'bold')
        if any(attr.italic for attr in attributes):
            tag_config['font'] = (self.font_family, self.font_size, 'italic')
        if any(attr.underline for attr in attributes):
            tag_config['underline'] = True
        if any(attr.strikethrough for attr in attributes):
            tag_config['overstrike'] = True
        if attributes and attributes[0].colour != 0:
            irc_color_code = f"{attributes[0].colour:02d}"
            hex_color = self.main_app.irc_colors.get(irc_color_code, 'white')
            tag_config['foreground'] = hex_color
        if attributes and attributes[0].background != 1:
            irc_background_code = f"{attributes[0].background:02d}"
            hex_background = self.main_app.irc_colors.get(irc_background_code, 'black')
            tag_config['background'] = hex_background
        return tag_config

    def tag_urls_async(self, urls):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        tasks = [self.tag_url(url) for url in urls]
        loop.run_until_complete(asyncio.gather(*tasks))

        loop.close()

        # Set the Text widget state back to DISABLED after configuring tags
        self.text_widget.config(state=tk.DISABLED)
        self.insert_and_scroll()

    async def tag_url(self, url):
        tag_name = f"url_{url}"
        self.text_widget.tag_configure(tag_name, foreground="blue", underline=1)

        start_idx = "1.0"
        while True:
            start_idx = self.text_widget.search(url, start_idx, tk.END, tag_name)
            if not start_idx:
                break
            end_idx = f"{start_idx}+{len(url)}c"
            self.text_widget.tag_add(tag_name, start_idx, end_idx)
            self.text_widget.tag_bind(tag_name, "<Button-1>", lambda event, url=url: self.open_url(event, url))
            start_idx = end_idx

    def find_urls(self, text):
        # A "simple" regex to detect URLs
        url_pattern = re.compile(r'(\w+://[^\s()<>]*\([^\s()<>]*\)[^\s()<>]*(?<![.,;!?])|www\.[^\s()<>]*\([^\s()<>]*\)[^\s()<>]*(?<![.,;!?])|\w+://[^\s()<>]+(?<![.,;!?])|www\.[^\s()<>]+(?<![.,;!?]))')
        return url_pattern.findall(text)

    def open_url(self, event, url):
        import webbrowser
        webbrowser.open(url)