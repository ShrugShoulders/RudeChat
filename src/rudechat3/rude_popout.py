import tkinter as tk
import asyncio
import configparser
import os
import time
import datetime
import json
import re
import random
import webbrowser
from plyer import notification
from threading import Thread
from tkinter import scrolledtext, Listbox, Scrollbar, Tk, Frame, Label, Entry, Listbox, Menu, Scrollbar, StringVar, PhotoImage 
from .format_decoder import Attribute, decoder

class RudePopOut:
    def __init__(self, root, selected_channel, irc_client, nick_name, main_app):
        self.root = root
        self.selected_channel = selected_channel
        self.irc_client = irc_client
        self.nick_name = nick_name
        self.main_app = main_app
        self.script_directory = os.path.dirname(os.path.abspath(__file__))
        self.modes_to_strip = ''.join(self.irc_client.mode_values)

        # Load configuration from gui_config.ini
        self.load_configuration()
        self.nickname_colors = self.main_app.nickname_colors

        # Apply main_bg_color and main_fg_color to root
        self.root.configure(bg=self.main_bg_color)
        self.root.title(f"{selected_channel}")

        # Configure root window to expand elements when resized
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Topic label
        self.topic_label = tk.Label(self.root, text="Channel Topic", bg=self.topic_label_bg, fg=self.topic_label_fg)
        self.topic_label.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.topic_label.bind("<Enter>", self.show_topic_tooltip)
        self.topic_label.bind("<Leave>", self.hide_topic_tooltip)
        self.tooltip = None

        # Create a main frame for the pop-out window
        self.frame = tk.Frame(self.root, bg="black")
        self.frame.grid(row=1, column=0, columnspan=2, sticky="nsew")

        # Configure frame to expand elements when resized
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=0)

        # Main text widget (scrolled text)
        self.text_widget = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD, cursor="arrow")
        self.text_widget.grid(row=0, column=0, sticky="nsew")
        self.text_widget.configure(bg=self.widgets_bg_color, fg=self.widgets_fg_color, font=(self.font_family, self.font_size))

        # User list frame
        self.user_frame = tk.Frame(self.frame, bg="black")
        self.user_frame.grid(row=0, column=1, sticky="nsew")
        
        # Configure user frame to expand elements when resized
        self.user_frame.rowconfigure(1, weight=1)
        self.user_frame.columnconfigure(0, weight=1)

        # Label for Users
        self.user_label = tk.Label(self.user_frame, text="Users", bg=self.widgets_bg_color, fg='white')
        self.user_label.grid(row=0, column=0, sticky='ew')

        # User listbox
        self.user_listbox = Listbox(self.user_frame, height=25, width=16, bg=self.user_listbox_bg, fg=self.user_listbox_fg)
        self.user_listbox.grid(row=1, column=0, sticky='nsew')

        # User list scrollbar
        self.user_scrollbar = Scrollbar(self.user_frame, orient="vertical", command=self.user_listbox.yview)
        self.user_listbox.config(yscrollcommand=self.user_scrollbar.set)
        self.user_scrollbar.grid(row=1, column=1, sticky='ns')
        self.user_listbox.bind("<Button-3>", self.show_user_list_menu)

        # Entry widget for message input
        self.entry = tk.Entry(self.frame)
        self.entry.grid(row=1, column=0, sticky='ew', padx=10, pady=5)
        self.entry.bind('<Return>', self.send_text)
        self.entry.bind('<Tab>', self.handle_tab_complete)
        self.entry.bind('<Up>', self.handle_arrow_keys)
        self.entry.bind('<Down>', self.handle_arrow_keys)
        self.entry.configure(bg=self.input_bg, fg=self.input_fg, insertbackground=self.input_insertbackground, font=(self.font_family, self.font_size))

        # Close button (smaller size)
        self.close_button = tk.Button(self.frame, text="Pop In", command=self.close_window, width=8)
        self.close_button.grid(row=1, column=1, sticky='e', padx=(0, 10), pady=5)
        self.close_button.configure(bg=self.button_bg_color, fg=self.button_fg_color)

        # Initialize tab completion related attributes
        self.entry_history = []
        self.history_index = 0
        self.tab_complete_completions = []
        self.tab_complete_index = 0
        self.last_tab_time = 0
        self.tab_completion_timer = None
        self.tab_complete_terminator = ":"

        self.init_input_menu()
        self.init_message_menu()
        self.set_topic(selected_channel)
        self.display_last_messages(selected_channel)
        self.update_gui_user_list(selected_channel)

        # Bind the window close event & act on it
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)

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
        self.button_fg_color = config.get('WIDGETS', 'entry_fg')
        self.button_bg_color = config.get('WIDGETS', 'entry_bg')
        self.user_nickname_color = config.get('GUI', 'main_nickname_color', fallback='#39ff14')
        self.generate_nickname_colors = config.getboolean('GUI', 'generate_nickname_colors', fallback=True)
        self.font_family = config.get('GUI', 'family', fallback='Hack')
        self.font_size = config.getint('GUI', 'size', fallback=10)
        self.input_fg = config.get('WIDGETS', 'entry_fg', fallback='#C0FFEE')
        self.input_bg = config.get('WIDGETS', 'entry_bg', fallback='black')
        self.input_insertbackground = config.get('WIDGETS', 'entry_insertbackground', fallback='#C0FFEE')
        self.input_label_bg = config.get('WIDGETS', 'entry_label_bg', fallback='black')
        self.input_label_fg = config.get('WIDGETS', 'entry_label_fg', fallback='#C0FFEE')
        self.topic_label_bg = config.get('WIDGETS', 'topic_label_bg', fallback='black')
        self.topic_label_fg = config.get('WIDGETS', 'topic_label_fg', fallback='white')
        self.user_listbox_fg = config.get('WIDGETS', 'users_fg', fallback='#39ff14')
        self.user_listbox_bg = config.get('WIDGETS', 'users_bg', fallback='black')

    def whois_from_menu(self):
        selected_user_index = self.user_listbox.curselection()
        if selected_user_index:
            selected_user = self.user_listbox.get(selected_user_index)
            cleaned_nickname = selected_user.lstrip(self.modes_to_strip)
            user_input = f"/whois {cleaned_nickname}"
            asyncio.run_coroutine_threadsafe(
                self.irc_client.command_parser(user_input),
                self.irc_client.loop
            )

    def kick_user_from_channel(self):
        selected_user_index = self.user_listbox.curselection()
        if selected_user_index:
            selected_user = self.user_listbox.get(selected_user_index)
            user_input = f"/kick {selected_user} {self.selected_channel} Bye <3"
            asyncio.run_coroutine_threadsafe(
                self.irc_client.command_parser(user_input),
                self.irc_client.loop
            )

    def copy_text_user(self):
        self.user_listbox.event_generate("<<Copy>>")

    def open_query_from_menu(self):
        selected_user_index = self.user_listbox.curselection()
        if selected_user_index:
            selected_user = self.user_listbox.get(selected_user_index)
            cleaned_nickname = selected_user.lstrip(self.modes_to_strip)
            user_input = f"/query {cleaned_nickname}"
            asyncio.run_coroutine_threadsafe(
                self.irc_client.command_parser(user_input),
                self.irc_client.loop
            )
            self.main_app.open_dm_pop_out_from_window(cleaned_nickname)

    def create_user_list_menu(self):
        menu = tk.Menu(self.user_listbox, tearoff=0)
        menu.add_command(label="Open Query", command=self.open_query_from_menu)
        menu.add_command(label="Whois", command=self.whois_from_menu)
        menu.add_command(label="Kick", command=self.kick_user_from_channel)
        menu.add_command(label="Copy", command=self.copy_text_user)
        return menu

    def show_user_list_menu(self, event):
        menu = self.create_user_list_menu()
        menu.post(event.x_root, event.y_root)
        self.root.bind("<Motion>", lambda e: self.check_user_mouse_position(e, menu))

    def init_message_menu(self):
        """
        Right click menu for the main chat window.
        """
        self.message_menu = Menu(self.text_widget, tearoff=0)
        self.message_menu.add_command(label="Copy", command=self.copy_text_message)
        self.text_widget.bind("<Button-3>", self.show_message_menu)

    def show_message_menu(self, event):
        try:
            # Open the popup menu
            self.message_menu.tk_popup(event.x_root, event.y_root)
            # Bind the <Motion> event to a function that checks if the mouse is over the menu
            self.root.bind("<Motion>", self.check_message_mouse_position)
        finally:
            self.message_menu.grab_release()

    def copy_text_message(self):
        self.text_widget.event_generate("<<Copy>>")

    def get_mode_symbol(self, mode):
        """Return the symbol corresponding to the IRC mode."""
        if self.irc_client.display_user_modes:
            return self.irc_client.mode_to_symbol.get(mode, '')
        else:
            return ''

    def get_user_mode(self, user, channel):
        """Retrieve the user's mode for the given channel."""
        if self.irc_client.display_user_modes:
            channel_modes = self.irc_client.user_modes.get(channel, {})
            user_modes = channel_modes.get(user, set())
            return next(iter(user_modes), None)  # Get the first mode if available, else None
        else:
            return None

    def send_text(self, event=None):
        try:
            user_text = self.entry.get()
            if not user_text:
                return

            timestamp = datetime.datetime.now().strftime('[%H:%M:%S]')
            escaped_text = self.main_app.escape_color_codes(user_text)
            current_channel = self.selected_channel

            # Determine the server and current channel
            server = self.irc_client.server
            user_mode = self.get_user_mode(self.nick_name, self.selected_channel)
            mode_symbol = self.get_mode_symbol(user_mode) if user_mode else ''

            # Check if the text is a command
            if user_text.startswith('/'):
                self.entry.delete(0, tk.END)
                self.pop_command_parser(user_text)
            else:
                shortened_text = escaped_text[:420]
                self.entry_history.append(shortened_text)

                # Limit the entry_history to the last 10 messages
                if len(self.entry_history) > 10:
                    self.entry_history.pop(0)

                # Reset history_index to the end of entry_history
                self.history_index = len(self.entry_history)
                # Insert text in the main text widget
                self.insert_text(f"{timestamp} <{mode_symbol}{self.nick_name}> {shortened_text}\n")
                self.entry.delete(0, tk.END)

                # Update channel_messages dictionary
                if server not in self.irc_client.channel_messages:
                    self.irc_client.channel_messages[server] = {}
                if current_channel not in self.irc_client.channel_messages[server]:
                    self.irc_client.channel_messages[server][current_channel] = []

                self.irc_client.channel_messages[server][current_channel].append(f"{timestamp} <{mode_symbol}{self.nick_name}> {shortened_text}\n")

                self.log_message(self.irc_client.server_name, current_channel, self.nick_name, shortened_text, is_sent=True)

                # Send the message through the IRC client
                asyncio.run_coroutine_threadsafe(
                    self.irc_client.send_message(f"PRIVMSG {current_channel} :{shortened_text}"), 
                    self.irc_client.loop
                )

                self.highlight_nickname()
        except Exception as e:
            print(f"Exception in send_text: {e}")

    def handle_arrow_keys(self, event):
        if event.keysym == 'Up':
            self.show_previous_entry()
        elif event.keysym == 'Down':
            self.show_next_entry()

    def show_previous_entry(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self.entry_history[self.history_index])

    def show_next_entry(self):
        if self.history_index < len(self.entry_history) - 1:
            self.history_index += 1
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self.entry_history[self.history_index])
        elif self.history_index == len(self.entry_history) - 1:
            self.history_index += 1
            self.entry.delete(0, tk.END)

    def pop_command_parser(self, user_input):
        channel = self.selected_channel
        args = user_input[1:].split() if user_input.startswith('/') else []
        primary_command = args[0].lower() if args else None

        timestamp = datetime.datetime.now().strftime('[%H:%M:%S]')

        match primary_command:
            case "me":
                self.handle_action(args, channel, timestamp)
            case "whois" | "help" | "list" | "ping":
                asyncio.run_coroutine_threadsafe(
                    self.irc_client.command_parser(user_input),
                    self.irc_client.loop
                )
            case "notice":
                if len(args) < 3:
                    self.insert_text("Usage: /notice <target> <message>\n")
                    return
                notice_message = ' '.join(args)
                asyncio.run_coroutine_threadsafe(
                    self.irc_client.command_parser(user_input),
                    self.irc_client.loop
                )
                self.insert_text(f"NOTICE {channel} {notice_message}")
            case "kick":
                if len(args) < 3:
                    self.insert_text("Usage: /kick <user> <channel> [reason]\n")
                    return
                user = args[1].lstrip(self.modes_to_strip)
                channel = args[2]
                reason = ' '.join(args[3:]) if len(args) > 3 else None
                kick_message = f"Kicked {user} from {channel} for {reason}\n"
                asyncio.run_coroutine_threadsafe(
                    self.irc_client.command_parser(user_input),
                    self.irc_client.loop
                )
                self.insert_text(f"{kick_message}")
            case "invite":
                if len(args) < 3:
                    self.insert_text("Usage: /invite <user> <channel>\n")
                    return
                user = args[1]
                channel = args[2]
                invite_message = f"Invited {user} to {channel}\n"
                asyncio.run_coroutine_threadsafe(
                    self.irc_client.command_parser(user_input),
                    self.irc_client.loop
                )
                self.insert_text(invite_message)
            case "query":
                if len(args) < 2:
                    self.insert_text(f"Error: Please provide a nickname for the query command.\n")
                    return
                user = args[1]
                asyncio.run_coroutine_threadsafe(
                    self.irc_client.command_parser(user_input),
                    self.irc_client.loop
                )
                self.main_app.open_dm_pop_out_from_window(user)
            case "mode":
                if len(args) < 2:
                    self.insert_text("Error: Please provide a mode and a channel.\n")
                    self.insert_text("Usage: /mode [channel] [+|-][mode flags] [target]\n")
                    self.insert_text("Example for channel: /mode #channel_name +o username\n")
                    self.insert_text("Example for user: /mode #channel_name +o username\n")
                    return

                channel = args[1]
                mode = None
                target = None

                if len(args) > 2:
                    mode = args[2]

                if len(args) > 3:
                    target = args[3]
                asyncio.run_coroutine_threadsafe(
                    self.irc_client.set_mode(channel, mode, target),
                    self.irc_client.loop
                )

            case _:
                pass
        return

    def handle_action(self, args, channel, timestamp):
        action_message = ' '.join(args[1:])
        escaped_input = self.main_app.escape_color_codes(action_message)
        formatted_message = f"* {self.nick_name} {escaped_input}"
        asyncio.run_coroutine_threadsafe(
            self.irc_client.send_message(f"PRIVMSG {channel} :\x01ACTION {escaped_input}\x01"), 
            self.irc_client.loop
        )
        self.insert_text(f"{timestamp} {formatted_message}\n")

    def close_window(self):
        # Remove the channel and window from the popped_out_channels and pop_out_windows
        if self.selected_channel in self.main_app.popped_out_channels:
            self.main_app.popped_out_channels.remove(self.selected_channel)
        if self.selected_channel in self.main_app.pop_out_windows:
            del self.main_app.pop_out_windows[self.selected_channel]
        # Close the window if it exists
        if self.root:
            self.irc_client.update_gui_channel_list()
            asyncio.run_coroutine_threadsafe(
                self.irc_client.pop_out_return(self.selected_channel),
                self.irc_client.loop
            )
            self.root.destroy()
            self.root = None

    def destroy_window(self):
        self.root.destroy()
        self.root = None

    def update_gui_user_list(self, channel):
        # Clear existing items in user listbox
        self.user_listbox.delete(0, tk.END)
        
        # Get the list of users for the given channel
        users = self.irc_client.channel_users.get(channel, [])

        if users:
            # Populate with users for the given channel
            for user in users:
                self.user_listbox.insert(tk.END, user)
        else:
            # Handle the case when there are no users in the channel
            self.user_listbox.insert(tk.END, self.nick_name)
            self.user_listbox.insert(tk.END, self.selected_channel)

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
            # Fallback to the user list from the GUI's user listbox
            user_list = self.user_listbox.get(0, tk.END)

        # Remove @ and + symbols from nicknames
        user_list_cleaned = [nick.lstrip(self.modes_to_strip) for nick in user_list]

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

    def trim_text_widget(self):
        """Trim the text widget to only hold a maximum of 120 lines."""
        lines = self.text_widget.get("1.0", tk.END).split("\n")
        if len(lines) > 150:
            self.text_widget.config(state=tk.NORMAL)  # Enable text widget editing
            self.text_widget.delete("1.0", f"{len(lines) - 120}.0")  # Delete excess lines
            self.text_widget.config(state=tk.DISABLED)  # Disable text widget editing

    def insert_text(self, message):
        try:
            self.trim_text_widget()
            urls = self.find_urls(message)

            # Set the Text widget state to NORMAL before inserting and configuring tags
            self.text_widget.config(state=tk.NORMAL)

            formatted_text = decoder(message)
            self.tag_text(formatted_text)

            # Start tagging URLs using the non-blocking approach
            self.tag_urls(urls)
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

    def tag_urls(self, urls, index=0):
        if index < len(urls):
            url = urls[index]
            tag_name = f"url_{url}"
            self.text_widget.tag_configure(tag_name, foreground="blue", underline=1)

            start_idx = "1.0"
            while True:
                start_idx = self.text_widget.search(url, start_idx, tk.END)
                if not start_idx:
                    break
                end_idx = f"{start_idx}+{len(url)}c"
                self.text_widget.tag_add(tag_name, start_idx, end_idx)
                self.text_widget.tag_bind(tag_name, "<Button-1>", lambda event, url=url: self.open_url(event, url))
                start_idx = end_idx

            # Schedule the next URL tagging
            self.text_widget.after(1, self.tag_urls, urls, index + 1)
        else:
            # Set the Text widget state back to DISABLED after configuring tags
            self.text_widget.config(state=tk.DISABLED)
            self.insert_and_scroll()

    def find_urls(self, text):
        # A "simple" regex to detect URLs
        url_pattern = re.compile(r'(\w+://[^\s()<>]*\([^\s()<>]*\)[^\s()<>]*(?<![.,;!?])|www\.[^\s()<>]*\([^\s()<>]*\)[^\s()<>]*(?<![.,;!?])|\w+://[^\s()<>]+(?<![.,;!?])|www\.[^\s()<>]+(?<![.,;!?]))')
        return url_pattern.findall(text)

    def open_url(self, event, url):
        webbrowser.open(url)

    def init_input_menu(self):
        """
        Right click menu for the Input Widget.
        """
        self.input_menu = Menu(self.entry, tearoff=0)
        self.input_menu.add_command(label="Cut", command=self.cut_text)
        self.input_menu.add_command(label="Copy", command=self.copy_text)
        self.input_menu.add_command(label="Paste", command=self.paste_text)
        self.input_menu.add_command(label="Select All", command=self.select_all_text)

        # First set of IRC colors
        irc_colors_menu = Menu(self.input_menu, tearoff=0)
        irc_colors = [
            ("White", "00"),
            ("Black", "01"),
            ("Blue", "02"),
            ("Green", "03"),
            ("Red", "04"),
            ("Brown", "05"),
            ("Purple", "06"),
            ("Orange", "07"),
            ("Yellow", "08"),
            ("Lime", "09"),
            ("Teal", "10"),
            ("Cyan", "11"),
            ("Royal", "12"),
            ("Pink", "13"),
            ("Grey", "14"),
            ("Silver", "15"),
        ]

        for color_name, color_code in irc_colors:
            irc_colors_menu.add_command(label=color_name, command=lambda code=color_code: self.insert_irc_color(code))

        self.input_menu.add_cascade(label="IRC Color", menu=irc_colors_menu)

        # Additional IRC colors
        additional_irc_colors_menu = Menu(self.input_menu, tearoff=0)
        # Simple representation for color names
        additional_irc_colors = [(f"Color {i}", f"{i:02}") for i in range(16, 99)]

        for color_name, color_code in additional_irc_colors:
            additional_irc_colors_menu.add_command(label=color_name, command=lambda code=color_code: self.insert_irc_color(code))

        self.input_menu.add_cascade(label="Extended IRC Color", menu=additional_irc_colors_menu)

        text_format_menu = Menu(self.input_menu, tearoff=0)
        text_format_options = [
            ("Bold", "\x02"),
            ("Italic", "\x1D"),
            ("Underline", "\x1F"),
            ("Strike Through", "\x1E"),
            ("Inverse", "\x16")
        ]

        for format_name, format_code in text_format_options:
            text_format_menu.add_command(label=format_name, command=lambda code=format_code: self.insert_text_format(code))

        self.input_menu.add_cascade(label="Text Format", menu=text_format_menu)

        self.entry.bind("<Button-3>", self.show_input_menu)

    def insert_irc_color(self, color_code):
        """
        Insert IRC color code around selected text or at cursor position.
        """
        try:
            selected_text = self.entry.selection_get()
            start_index = self.entry.index(tk.SEL_FIRST)
            end_index = self.entry.index(tk.SEL_LAST)
        except Exception as e:
            selected_text = None

        if selected_text:
            self.entry.delete(start_index, end_index)
            self.entry.insert(start_index, f"\x03{color_code}{selected_text}\x03")
            self.entry.select_range(start_index, end_index + 3)
            self.entry.icursor(end_index + 4)
        else:
            self.entry.insert("insert", f"\x03{color_code}")

    def insert_text_format(self, format_code):
        """
        Insert text format code around selected text or at cursor position.
        """
        try:
            selected_text = self.entry.selection_get()
            start_index = self.entry.index(tk.SEL_FIRST)
            end_index = self.entry.index(tk.SEL_LAST)
        except Exception as e:
            selected_text = None

        if selected_text:
            self.entry.delete(start_index, end_index)
            self.entry.insert(start_index, f"{format_code}{selected_text}\x0F")
            self.entry.select_range(start_index, end_index + len(format_code) + 1)
            self.entry.icursor(end_index + len(format_code) + 1)
        else:
            self.entry.insert("insert", format_code)

    def show_input_menu(self, event):
        try:
            self.input_menu.tk_popup(event.x_root, event.y_root)
            self.root.bind("<Motion>", self.check_input_mouse_position)
        finally:
            self.input_menu.grab_release()

    def check_mouse_position(self, event, menu):
        try:
            # Get the position of the menu
            menu_x1 = menu.winfo_rootx()
            menu_y1 = menu.winfo_rooty()
            menu_x2 = menu_x1 + menu.winfo_width()
            menu_y2 = menu_y1 + menu.winfo_height()

            # Check if the mouse is outside the menu
            if not (menu_x1 <= event.x_root <= menu_x2 and menu_y1 <= event.y_root <= menu_y2):
                menu.unpost()
                self.root.unbind("<Motion>")
        except Exception as e:
            print(f"Exception in check_mouse_position: {e}")

    def check_input_mouse_position(self, event):
        self.check_mouse_position(event, self.input_menu)

    def check_message_mouse_position(self, event):
        self.check_mouse_position(event, self.message_menu)

    def check_user_mouse_position(self, event, menu):
        self.check_mouse_position(event, menu)

    def cut_text(self):
        self.entry.event_generate("<<Cut>>")

    def copy_text(self):
        self.entry.event_generate("<<Copy>>")

    def paste_text(self):
        self.entry.event_generate("<<Paste>>")

    def select_all_text(self):
        self.entry.select_range(0, tk.END)
        self.entry.icursor(tk.END)

    def display_last_messages(self, channel, num=120):
        server_name = self.irc_client.server
        if server_name:
            messages = self.irc_client.channel_messages.get(server_name, {}).get(channel, [])
        for message in messages[-num:]:
            self.insert_text(message)
            self.highlight_nickname()

    def show_topic_tooltip(self, event):
        try:
            channel_name = self.selected_channel
            server_topics = self.main_app.channel_topics.get(self.irc_client.server, {})
            topic = server_topics.get(channel_name, "N/A")
        except Exception as e:
            print(f"Could Not Get Topic {e}")
        if self.tooltip:
            self.tooltip.destroy()
        x, y, _, _ = self.topic_label.bbox("insert")
        x += self.topic_label.winfo_rootx() + 25
        y += self.topic_label.winfo_rooty() + 25
        self.tooltip = tk.Toplevel(self.topic_label)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        # Specify the wraplength in pixels (e.g., 200 pixels)
        label = tk.Label(self.tooltip, text=topic, justify='left', wraplength=800)
        label.pack()

    def hide_topic_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
        self.tooltip = None

    def set_topic(self, channel_name):
        # Retrieve the topic
        try:
            server_topics = self.main_app.channel_topics.get(self.irc_client.server, {})
            topic = server_topics.get(channel_name, channel_name)
            
            # Truncate the topic to the first 100 characters if necessary
            if len(topic) > 100:
                topic = topic[:100] + '...'
            
            self.topic_label.configure(text=f"{topic}")
        except Exception as e:
            print(f"Exception in set_topic: {e}")

    def is_app_focused(self):
        return bool(self.root.focus_displayof())

    def check_focus_and_notify(self, message):
        if not self.is_app_focused():
            try:
                self.trigger_desktop_notification(self.selected_channel, message)
            except Exception as e:
                print(f"Exception in check_focus_and_notify: {e}")

    def trigger_desktop_notification(self, channel_name=None, message_content=None, title="RudePopOut"):
        """
        Show a system desktop notification.
        """
        script_directory = os.path.dirname(os.path.abspath(__file__))
        if channel_name.startswith(self.irc_client.chantypes):
            return

        if channel_name:
            # Ensure channel_name is a string and replace problematic characters
            channel_name = str(channel_name).replace(f"{self.irc_client.chantypes}", "")
            title = f"{title}"
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
                timeout=3,  
            )
        except Exception as e:
            print(f"Desktop notification error: {e}")