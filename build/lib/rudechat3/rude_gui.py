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

from .rude_client import RudeChatClient
from .configure_window import ConfigWindow
from .shared_imports import *

class RudeGui:
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
        self.nickname_colors = self.load_nickname_colors()
        self.clients = {}
        self.channel_topics = {}
        self.entry_history = []
        self.history_index = 0

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
        self.text_widget = ScrolledText(self.frame, wrap='word', bg="black", cursor="arrow", fg="#C0FFEE")
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
        self.user_listbox.bind("<Button-3>", self.show_user_list_menu)

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
        self.channel_listbox.bind("<Button-3>", self.show_channel_list_menu)

        # Server frame
        self.server_frame = tk.Frame(self.master, height=100, bg="black")
        self.server_frame.grid(row=2, column=0, columnspan=2, sticky='ew')

        # Configure column to expand
        self.server_frame.grid_columnconfigure(0, weight=1)

        self.server_text_widget = ScrolledText(self.server_frame, wrap='word', height=5, bg="black", cursor="arrow", fg="#7882ff")
        self.server_text_widget.grid(row=0, column=0, sticky='nsew')

        # Entry widget
        self.entry_widget = tk.Entry(self.master)
        self.entry_widget.grid(row=3, column=1, sticky='ew')
        self.entry_widget.bind('<Tab>', self.handle_tab_complete)
        self.entry_widget.bind('<Up>', self.handle_arrow_keys)
        self.entry_widget.bind('<Down>', self.handle_arrow_keys)

        # Label for nickname and channel
        self.current_nick_channel = tk.StringVar(value="Nickname | #Channel" + " &>")
        self.nick_channel_label = tk.Label(self.master, textvariable=self.current_nick_channel, bg="black", fg="white", padx=5, pady=1)
        self.nick_channel_label.grid(row=3, column=0, sticky='w')

        # Initialize the RudeChatClient and set the GUI reference
        self.irc_client = RudeChatClient(self.text_widget, self.server_text_widget, self.entry_widget, self.master, self)
        self.init_input_menu()
        self.init_message_menu()
        self.init_server_menu()

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

        self.master.after(0, self.bind_return_key)

    async def remove_server_from_dropdown(self):
        current_server = self.server_var.get()
        if current_server in self.server_dropdown['values']:
            servers = list(self.server_dropdown['values'])
            servers.remove(current_server)
            self.server_dropdown['values'] = tuple(servers)

        # Set the first available server as the current one
        if self.server_dropdown['values']:
            self.server_var.set(self.server_dropdown['values'][0])
            self.on_server_change(None)
        else:
            self.server_var.set("")  # No servers left, clear the current selection

        self.gui.update_nick_channel_label()

    def load_nickname_colors(self):
        try:
            with open('nickname_colors.json', 'r') as file:
                nickname_colors = json.load(file)
            return nickname_colors
        except FileNotFoundError:
            print("Nickname colors file not found. Returning an empty dictionary.")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in nickname colors file: {e}. Returning an empty dictionary.")
            return {}
        except Exception as e:
            print(f"An unexpected error occurred while loading nickname colors: {e}. Returning an empty dictionary.")
            return {}

    def save_nickname_colors(self):
        try:
            with open('nickname_colors.json', 'w') as file:
                json.dump(self.nickname_colors, file)
        except Exception as e:
            print(f"An unexpected error occurred while saving nickname colors: {e}. Unable to save nickname colors.")

    def init_input_menu(self):
        """
        Right click menu.
        """
        self.input_menu = Menu(self.entry_widget, tearoff=0)
        self.input_menu.add_command(label="Cut", command=self.cut_text)
        self.input_menu.add_command(label="Copy", command=self.copy_text)
        self.input_menu.add_command(label="Paste", command=self.paste_text)
        self.input_menu.add_command(label="Select All", command=self.select_all_text)

        self.entry_widget.bind("<Button-3>", self.show_input_menu)

    def show_input_menu(self, event):
        try:
            self.input_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.input_menu.grab_release()

    def init_message_menu(self):
        """
        Right click menu for the main chat window.
        """
        self.message_menu = Menu(self.text_widget, tearoff=0)
        self.message_menu.add_command(label="Copy", command=self.copy_text_message)
        self.message_menu.add_command(label="Reset Colors", command=self.reset_nick_colors)
        self.message_menu.add_command(label="Save Colors", command=self.save_nickname_colors)
        self.message_menu.add_command(label="Reload Macros", command=self.irc_client.reload_ascii_macros)
        self.message_menu.add_command(label="Clear", command=self.clear_chat_window)
        self.message_menu.add_command(label="Config", command=self.open_config_window)
        
        self.text_widget.bind("<Button-3>", self.show_message_menu)
    
    def open_config_window(self):
        root = tk.Tk()
        root.title("Configuration Window")

        files = os.listdir()
        config_files = [f for f in files if f.startswith("conf.") and f.endswith(".rude")]
        config_files.sort()

        if not config_files:
            messagebox.showwarning("Warning", "No configuration files found.")
            root.destroy()
            return

        config_window = ConfigWindow(root, config_files[0])

        def on_config_change(event):
            selected_config_file = selected_config_file_var.get()
            config_window.config_file = selected_config_file
            config_window.config.read(selected_config_file)
            config_window.create_widgets()

        # Menu to choose configuration file
        selected_config_file_var = tk.StringVar(root, config_files[0])
        config_menu = ttk.Combobox(root, textvariable=selected_config_file_var, values=config_files)
        config_menu.pack(pady=10)

        config_menu.bind("<<ComboboxSelected>>", on_config_change)

        save_button = ttk.Button(root, text="Save", command=config_window.save_config)
        save_button.pack(pady=10)

        root.mainloop()

    def show_message_menu(self, event):
        try:
            self.message_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.message_menu.grab_release()

    def init_server_menu(self):
        """
        Right click menu for the server window.
        """
        self.server_menu = Menu(self.server_text_widget, tearoff=0)
        self.server_menu.add_command(label="Copy", command=self.copy_text_server)

        self.server_text_widget.bind("<Button-3>", self.show_server_menu)

    def show_server_menu(self, event):
        try:
            self.server_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.server_menu.grab_release()

    def create_user_list_menu(self):
        menu = tk.Menu(self.user_listbox, tearoff=0)
        menu.add_command(label="Open Query", command=self.open_query_from_menu)
        menu.add_command(label="Copy", command=self.copy_text_user)
        menu.add_command(label="Whois", command=self.whois_from_menu)
        menu.add_command(label="Kick", command=self.kick_user_from_channel)
        return menu

    def show_user_list_menu(self, event):
        menu = self.create_user_list_menu()
        menu.post(event.x_root, event.y_root)

    def create_channel_list_menu(self):
        menu = tk.Menu(self.channel_listbox, tearoff=0)
        
        # Assume self.channel_listbox is a list of channel names or DM nicknames
        selected_channel_index = self.channel_listbox.curselection()
        if selected_channel_index:
            selected_channel = self.channel_listbox.get(selected_channel_index)
            if '#' in selected_channel:
                menu.add_command(label="Leave Channel", command=self.leave_channel_from_menu)
            else:
                menu.add_command(label="Close Query", command=self.close_query_from_menu)
        
        return menu

    def show_channel_list_menu(self, event):
        menu = self.create_channel_list_menu()
        menu.post(event.x_root, event.y_root)

    def copy_text_user(self):
        self.user_listbox.event_generate("<<Copy>>")

    def cut_text(self):
        self.entry_widget.event_generate("<<Cut>>")

    def copy_text(self):
        self.entry_widget.event_generate("<<Copy>>")

    def copy_text_message(self):
        self.text_widget.event_generate("<<Copy>>")

    def copy_text_server(self):
        self.server_text_widget.event_generate("<<Copy>>")

    def paste_text(self):
        self.entry_widget.event_generate("<<Paste>>")

    def select_all_text(self):
        self.entry_widget.select_range(0, tk.END)
        self.entry_widget.icursor(tk.END)

    def kick_user_from_channel(self):
        selected_user_index = self.user_listbox.curselection()
        channel = self.irc_client.current_channel
        if selected_user_index:
            selected_user = self.user_listbox.get(selected_user_index)
            loop = asyncio.get_event_loop()
            loop.create_task(self.irc_client.handle_kick_command(["/kick", selected_user, channel, "Bye <3"]))

    def open_query_from_menu(self):
        selected_user_index = self.user_listbox.curselection()
        if selected_user_index:
            selected_user = self.user_listbox.get(selected_user_index)
            self.irc_client.handle_query_command(["/query", selected_user], "<3 ")

    def close_query_from_menu(self):
        selected_channel_index = self.channel_listbox.curselection()
        if selected_channel_index:
            selected_channel = self.channel_listbox.get(selected_channel_index)
            self.irc_client.handle_cq_command(["/cq", selected_channel], "</3 ")

    def leave_channel_from_menu(self):
        selected_channel_index = self.channel_listbox.curselection()
        if selected_channel_index:
            selected_channel = self.channel_listbox.get(selected_channel_index)
            if '#' in selected_channel:
                loop = asyncio.get_event_loop()
                loop.create_task(self.irc_client.leave_channel(selected_channel))

    def whois_from_menu(self):
        selected_user_index = self.user_listbox.curselection()
        if selected_user_index:
            selected_user = self.user_listbox.get(selected_user_index)
            loop = asyncio.get_event_loop()
            loop.create_task(self.irc_client.whois(selected_user))

    def reset_nick_colors(self):
        self.nickname_colors = self.load_nickname_colors()
        self.highlight_nickname()

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
        # Highlight URLs in blue and underline
        urls = self.find_urls(message)

        # Set the Text widget state to NORMAL before inserting and configuring tags
        self.text_widget.config(state=tk.NORMAL)

        # Insert the message without tags initially
        self.text_widget.insert(tk.END, message)

        # Batch configure tags for all URLs
        for url in urls:
            tag_name = f"url_{url}"
            self.text_widget.tag_configure(tag_name, foreground="blue", underline=1)

        # Apply tags and bind events in a single pass
        for url in urls:
            start_idx = "1.0"
            while True:
                start_idx = self.text_widget.search(url, start_idx, tk.END, tag_name)
                if not start_idx:
                    break
                end_idx = f"{start_idx}+{len(url)}c"
                tag_name = f"url_{url}"
                self.text_widget.tag_add(tag_name, start_idx, end_idx)
                self.text_widget.tag_bind(tag_name, "<Button-1>", lambda event, url=url: self.open_url(event, url))
                start_idx = end_idx

        # Set the Text widget state back to DISABLED after configuring tags
        self.text_widget.config(state=tk.DISABLED)
        self.insert_and_scroll()

    def find_urls(self, text):
        # A simple regex to detect URLs
        url_pattern = re.compile(r'(\w+://\S+|www\.\S+)')
        return url_pattern.findall(text)

    def open_url(self, event, url):
        import webbrowser
        webbrowser.open(url)

    def insert_server_widget(self, message):
        self.server_text_widget.config(state=tk.NORMAL)
        self.server_text_widget.insert(tk.END, message)
        self.server_text_widget.config(state=tk.DISABLED)
        self.insert_and_scroll()

    async def send_quit_to_all_clients(self):
        for irc_client in self.clients.values():
            await asyncio.sleep(1)
            await irc_client.send_message('QUIT')

    def add_client(self, server_name, irc_client):
        self.clients[server_name] = irc_client
        current_servers = list(self.server_dropdown['values'])
        current_servers.append(server_name)
        self.server_dropdown['values'] = current_servers
        self.server_var.set(server_name)  # Set the current server
        self.channel_lists[server_name] = irc_client.joined_channels

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
        irc_client = RudeChatClient(self.text_widget, self.server_text_widget, self.entry_widget, self.master, self)
        await irc_client.read_config(config_file)
        await irc_client.connect()

        # Use the server_name if it is set in the configuration, else use fallback_server_name
        server_name = irc_client.server_name if irc_client.server_name else fallback_server_name
        
        self.add_client(server_name, irc_client)
        asyncio.create_task(irc_client.keep_alive())
        asyncio.create_task(irc_client.handle_incoming_message())

        self.bind_return_key()

    def bind_return_key(self):
        loop = asyncio.get_event_loop()
        self.entry_widget.bind('<Return>', lambda event: loop.create_task(self.on_enter_key(event)))

    async def on_enter_key(self, event):
        user_input = self.entry_widget.get()

        # Save the entered message to entry_history
        if user_input:
            self.entry_history.append(user_input)

            # Limit the entry_history to the last 10 messages
            if len(self.entry_history) > 10:
                self.entry_history.pop(0)

            # Reset history_index to the end of entry_history
            self.history_index = len(self.entry_history)

        self.entry_widget.delete(0, tk.END)
        await self.irc_client.command_parser(user_input)
        self.text_widget.see(tk.END)

    def handle_arrow_keys(self, event):
        if event.keysym == 'Up':
            self.show_previous_entry()
        elif event.keysym == 'Down':
            self.show_next_entry()

    def show_previous_entry(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.entry_widget.delete(0, tk.END)
            self.entry_widget.insert(0, self.entry_history[self.history_index])

    def show_next_entry(self):
        if self.history_index < len(self.entry_history) - 1:
            self.history_index += 1
            self.entry_widget.delete(0, tk.END)
            self.entry_widget.insert(0, self.entry_history[self.history_index])
        elif self.history_index == len(self.entry_history) - 1:
            self.history_index += 1
            self.entry_widget.delete(0, tk.END)

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

        server = self.irc_client.server  # Assume the server is saved in the irc_client object

        # Clear the text window
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.config(state=tk.DISABLED)

        # First, check if it's a DM
        if server in self.irc_client.channel_messages and \
           channel_name in self.irc_client.channel_messages[server]:

            # Set current channel to the DM
            self.irc_client.current_channel = channel_name
            self.update_nick_channel_label()

            # Display the last messages for the current DM
            self.irc_client.display_last_messages(channel_name, server_name=server)
            self.insert_and_scroll()
            self.highlight_nickname()

            # No topic for DMs
            self.current_topic.set(f"{channel_name}")

        # Then, check if it's a channel
        elif channel_name in self.irc_client.joined_channels:
            self.irc_client.current_channel = channel_name
            self.update_nick_channel_label()

            # Update topic label
            current_topic = self.channel_topics.get(channel_name, "N/A")
            self.current_topic.set(f"{current_topic}")

            # Display the last messages for the current channel
            self.irc_client.display_last_messages(self.irc_client.current_channel)
            self.highlight_nickname()

            self.irc_client.update_gui_user_list(channel_name)
            self.insert_and_scroll()

        else:
            self.insert_text_widget(f"Not a member of channel or unknown DM {channel_name}\r\n")

    def insert_and_scroll(self):
        self.text_widget.see(tk.END)
        self.server_text_widget.see(tk.END)

    def clear_chat_window(self):
        current_channel = self.irc_client.current_channel

        if current_channel:
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.config(state=tk.DISABLED)
            self.irc_client.channel_messages[current_channel] = []

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
                if nickname_with_brackets not in self.nickname_colors:
                    self.nickname_colors[nickname_with_brackets] = self.generate_random_color()
                nickname_color = self.nickname_colors[nickname_with_brackets]

                # If it's the main user's nickname, set color to green
                if nickname_with_brackets == f"<{self.irc_client.nickname}>":
                    nickname_color = "#39ff14"

                self.text_widget.tag_configure(f"nickname_{nickname_with_brackets}", foreground=nickname_color)
                self.text_widget.tag_add(f"nickname_{nickname_with_brackets}", start_idx, end_idx)
                start_idx = end_idx
            else:
                start_idx = f"{start_idx}+1c"

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