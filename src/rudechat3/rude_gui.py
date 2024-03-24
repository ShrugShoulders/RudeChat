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
from .rude_colours import RudeColours
from .format_decoder import Attribute, decoder
from .shared_imports import *

class RudeGui:
    def __init__(self, master):
        self.master = master
        self.master.title("RudeChat")
        self.master.geometry("1064x900")
        self.master.configure(bg="black")
        self.script_directory = os.path.dirname(os.path.abspath(__file__))
        if sys.platform.startswith('win'):
            icon_path = os.path.join(self.script_directory, "rude.ico")
            self.master.iconbitmap(icon_path)
        else:
            icon_path = os.path.join(self.script_directory, "rude.png")  # Assuming you have a PNG version
            img = PhotoImage(file=icon_path)
            self.master.iconphoto(True, img)

        self.irc_colors = {
            '00': '#000000', '01': '#ffffff', '02': '#0000AA', '03': '#00AA00',
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

        # Topic label
        self.current_topic = tk.StringVar(value="Topic: ")
        self.topic_label = tk.Label(self.server_topic_frame, textvariable=self.current_topic, bg="black", fg="white", padx=5, pady=1)
        self.topic_label.grid(row=1, column=0, sticky='w')
        self.topic_label.bind("<Enter>", self.show_topic_tooltip)
        self.topic_label.bind("<Leave>", self.hide_topic_tooltip)
        self.tooltip = None

        # Main text widget
        self.text_widget = ScrolledText(self.frame, wrap='word', bg="black", cursor="arrow", fg="#C0FFEE", font=("Hack", 10))
        self.text_widget.grid(row=0, column=0, sticky="nsew")
        self.show_startup_art()

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

        # Label for Servers
        self.servers_label = tk.Label(self.channel_frame, text="Servers: --s", bg="black", fg="white")
        self.servers_label.grid(row=0, column=0, sticky='ew')  # Make sure label is above the server_listbox

        # Server selection
        self.server_var = tk.StringVar(self.master)
        self.server_listbox = tk.Listbox(self.channel_frame, selectmode=tk.SINGLE, width=16, height=4, bg="black", fg="white")
        self.server_listbox.grid(row=1, column=0, sticky='w')  # Adjust column to display server_listbox

        # Server listbox scrollbar
        self.server_scrollbar = tk.Scrollbar(self.channel_frame, orient="vertical", command=self.server_listbox.yview)
        self.server_listbox.config(yscrollcommand=self.server_scrollbar.set)
        self.server_scrollbar.grid(row=1, column=1, sticky='ns')

        self.server_listbox.bind('<<ListboxSelect>>', self.on_server_change)

        self.channel_label = tk.Label(self.channel_frame, text="Channels", bg="black", fg="white")
        self.channel_label.grid(row=2, column=0, sticky='ew')  # Make sure label is below the server_listbox

        self.channel_listbox = tk.Listbox(self.channel_frame, height=17, width=16, bg="black", fg="white")
        self.channel_scrollbar = tk.Scrollbar(self.channel_frame, orient="vertical", command=self.channel_listbox.yview)
        self.channel_listbox.config(yscrollcommand=self.channel_scrollbar.set)
        self.channel_listbox.grid(row=3, column=0, sticky='nsew')  # Adjust row to display channel_listbox
        self.channel_scrollbar.grid(row=3, column=1, sticky='ns')
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
        self.entry_widget = tk.Entry(self.master, bg="black", fg="#C0FFEE", insertbackground="#C0FFEE", font=("Hack", 10))
        self.entry_widget.grid(row=3, column=1, sticky='ew', columnspan=1)  # Adjust column span to cover only one column
        self.entry_widget.bind('<Tab>', self.handle_tab_complete)
        self.entry_widget.bind('<Up>', self.handle_arrow_keys)
        self.entry_widget.bind('<Down>', self.handle_arrow_keys)

        # Label for nickname and channel
        self.current_nick_channel = tk.StringVar(value="Nickname | #Channel" + " &>")
        self.nick_channel_label = tk.Label(self.master, textvariable=self.current_nick_channel, bg="black", fg="#C0FFEE", padx=5, pady=1, font=("Hack", 10))
        self.nick_channel_label.grid(row=3, column=0, sticky='w')

        self.text_widget.tag_configure('bold', font=('Hack', 10, 'bold'))
        self.text_widget.tag_configure('italic', font=('Hack', 10, 'italic'))
        self.text_widget.tag_configure('underline', underline=True)

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

    def show_startup_art(self):
        splash_directory = os.path.join(self.script_directory, "Splash")

        try:
            # List all .txt files in the Splash directory
            txt_files = [f for f in os.listdir(splash_directory) if f.endswith(".txt")]

            if not txt_files:
                raise FileNotFoundError("No .txt files found in the Splash directory")

            # Choose a random .txt file
            random_art_file = random.choice(txt_files)
            art_path = os.path.join(splash_directory, random_art_file)

            with open(art_path, "r", encoding='utf-8') as art_file:
                art_content = art_file.read()

                # Escape color codes in the art content
                escaped_art_content = self.escape_color_codes(art_content)

                self.insert_text_widget(escaped_art_content)
        except FileNotFoundError as e:
            print(f"Error displaying startup art: {e}")

    def scroll_channel_list(self):
        # This method scrolls the Listbox to the bottom
        self.channel_listbox.yview(tk.END)

    def escape_color_codes(self, line):
        # Escape color codes in the string
        escaped_line = re.sub(r'\\x([0-9a-fA-F]{2})', lambda match: bytes.fromhex(match.group(1)).decode('utf-8'), line)
        
        return escaped_line

    async def remove_server_from_listbox(self, server_name=None):
        if server_name is None:
            server_name = self.server_var.get()

        # Check if the server_name is in the Listbox
        if server_name in self.server_listbox.get(0, tk.END):
            # Remove the server_name from the Listbox
            index = self.server_listbox.get(0, tk.END).index(server_name)
            self.server_listbox.delete(index)

        # Set the first available server as the current one
        if self.server_listbox.size() > 0:
            self.server_var.set(self.server_listbox.get(0))
            self.server_listbox.select_set(0)
        else:
            self.server_var.set("")  # No servers left, clear the current selection

        self.gui.update_nick_channel_label()

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

    def save_nickname_colors(self):
        nickname_colors_path = os.path.join(self.script_directory, 'nickname_colours.json')

        try:
            with open(nickname_colors_path, 'w') as file:
                json.dump(self.nickname_colors, file, indent=2)
        except Exception as e:
            print(f"An unexpected error occurred while saving nickname colors: {e}. Unable to save nickname colors.")

    def init_input_menu(self):
        """
        Right click menu for the Input Widget.
        """
        self.input_menu = Menu(self.entry_widget, tearoff=0)
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

        self.entry_widget.bind("<Button-3>", self.show_input_menu)

    def insert_text_format(self, format_code):
        """
        Insert text format code around selected text or at cursor position.
        """
        selected_text = self.entry_widget.selection_get()
        if selected_text:
            start_index = self.entry_widget.index(tk.SEL_FIRST)
            end_index = self.entry_widget.index(tk.SEL_LAST)
            self.entry_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.entry_widget.insert("insert", f"{format_code}{selected_text}\x0F")
            self.entry_widget.select_range(start_index, end_index + len(format_code)*2)
            self.entry_widget.icursor(end_index + len(format_code) + 1)
        else:
            self.entry_widget.insert("insert", format_code)

    def insert_irc_color(self, color_code):
        """
        Insert IRC color code around selected text or at cursor position.
        """
        selected_text = self.entry_widget.selection_get()
        if selected_text:
            start_index = self.entry_widget.index(tk.SEL_FIRST)
            end_index = self.entry_widget.index(tk.SEL_LAST)
            self.entry_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.entry_widget.insert("insert", f"\x03{color_code}{selected_text}\x03")
            self.entry_widget.select_range(start_index, end_index + 3)
            self.entry_widget.icursor(end_index + 4)
        else:
            self.entry_widget.insert("insert", f"\x03{color_code}")

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
        self.message_menu.add_command(label="Color Selector", command=self.open_color_selector)
        self.message_menu.add_command(label="Reload Macros", command=self.reload_macros)
        self.message_menu.add_command(label="Clear", command=self.clear_chat_window)
        self.message_menu.add_command(label="Config", command=self.open_config_window)
        
        self.text_widget.bind("<Button-3>", self.show_message_menu)

    def open_color_selector(self):
        root = tk.Toplevel(self.master)  # Use Toplevel instead of Tk for a new window
        app = RudeColours(root)
        root.geometry("400x300")  # Set the initial size of the window
        root.transient(self.master)  # Set the main window as the transient master
        root.mainloop()

    def reload_macros(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.irc_client.update_available_macros())
    
    def open_config_window(self):
        root = tk.Tk()
        root.title("Configuration Window")

        files = os.listdir(self.script_directory)
        config_files = [f for f in files if f.startswith("conf.") and f.endswith(".rude")]
        config_files.sort()

        if not config_files:
            messagebox.showwarning("Warning", "No configuration files found.")
            root.destroy()
            return

        config_window = ConfigWindow(root, os.path.join(self.script_directory, config_files[0]))

        def on_config_change(event):
            selected_config_file = selected_config_file_var.get()
            config_window.config_file = os.path.join(self.script_directory, selected_config_file)
            config_window.config.read(config_window.config_file)
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
            cleaned_nickname = selected_user.lstrip('~&@%+')
            loop = asyncio.get_event_loop()
            loop.create_task(self.irc_client.whois(cleaned_nickname))

    def reset_nick_colors(self):
        self.nickname_colors = self.load_nickname_colors()
        self.highlight_nickname()

    def add_server_to_listbox(self, server_name):
        # Get the current list of servers from the Listbox
        current_servers = list(self.server_listbox.get(0, tk.END))
        
        # Add the new server_name to the list if it's not already there
        if server_name not in current_servers:
            current_servers.append(server_name)
            
        # Update the Listbox with the new list of servers
        self.server_listbox.delete(0, tk.END)  # Clear the existing items
        for server in current_servers:
            self.server_listbox.insert(tk.END, server)

    def show_topic_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
        x, y, _, _ = self.topic_label.bbox("insert")
        x += self.topic_label.winfo_rootx() + 25
        y += self.topic_label.winfo_rooty() + 25
        self.tooltip = tk.Toplevel(self.topic_label)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        # Specify the wraplength in pixels (e.g., 200 pixels)
        label = tk.Label(self.tooltip, text=self.current_topic.get(), justify='left', wraplength=800)
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

        formatted_text = decoder(message)

        # Run URL tagging in a separate thread
        url_thread = Thread(target=self.tag_urls_async, args=(urls,))
        url_thread.start()

        self.tag_text(formatted_text)

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
            tag_config['font'] = ('Hack', 10, 'bold')
        if any(attr.italic for attr in attributes):
            tag_config['font'] = ('Hack', 10, 'italic')
        if any(attr.underline for attr in attributes):
            tag_config['underline'] = True
        if any(attr.strikethrough for attr in attributes):
            tag_config['overstrike'] = True
        if attributes and attributes[0].colour != 0:
            irc_color_code = f"{attributes[0].colour:02d}"
            hex_color = self.irc_colors.get(irc_color_code, 'white')
            tag_config['foreground'] = hex_color
        if attributes and attributes[0].background != 0:
            irc_background_code = f"{attributes[0].background:02d}"
            hex_background = self.irc_colors.get(irc_background_code, 'black')
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
        # A simple regex to detect URLs
        url_pattern = re.compile(r'(\w+://[^\s()<>]+|www\.[^\s()<>]+)')
        return url_pattern.findall(text)

    def open_url(self, event, url):
        import webbrowser
        webbrowser.open(url)

    def insert_server_widget(self, message):
        self.server_text_widget.config(state=tk.NORMAL)
        self.server_text_widget.insert(tk.END, message)
        self.server_text_widget.config(state=tk.DISABLED)
        self.insert_and_scroll()

    async def send_quit_to_all_clients(self, quit_message=None):
        for irc_client in self.clients.values():
            await self.irc_client.save_channel_messages()
            quit_cmd = f'QUIT :{quit_message}' if quit_message else 'QUIT :RudeChat3 https://github.com/ShrugShoulders/RudeChat'
            await self.irc_client.send_message(quit_cmd)

    def add_client(self, server_name, irc_client):
        self.clients[server_name] = irc_client

        # Get the current list of servers from the Listbox
        current_servers = list(self.server_listbox.get(0, tk.END))

        # Add the new server_name to the list if it's not already there
        if server_name not in current_servers:
            current_servers.append(server_name)

        # Update the Listbox with the new list of servers
        self.server_listbox.delete(0, tk.END)  # Clear the existing items
        for server in current_servers:
            self.server_listbox.insert(tk.END, server)

        self.server_var.set(server_name)  # Set the current server
        self.server_listbox.select_set(0)
        self.channel_lists[server_name] = irc_client.joined_channels

    def on_server_change(self, event):
        selected_server_index = self.server_listbox.curselection()
        
        if selected_server_index:
            selected_server = self.server_listbox.get(selected_server_index)  # Get the selected server from the listbox
            self.irc_client.current_server = selected_server
            self.irc_client = self.clients.get(selected_server, None)
            
            if self.irc_client:
                # Set the server name in the RudeChatClient instance
                self.irc_client.set_server_name(selected_server)
                
                # Set the GUI reference and update the GUI components
                self.irc_client.set_gui(self)
                self.irc_client.update_gui_channel_list()
                
                # Update the user list in GUI
                selected_channel = self.irc_client.current_channel
                if selected_channel:
                    self.irc_client.update_gui_user_list(selected_channel)

                # Set the background color of the selected server to black
                self.server_listbox.itemconfig(selected_server_index, {'bg': 'black', 'fg': 'white'})

    async def init_client_with_config(self, config_file, fallback_server_name):
        try:
            irc_client = RudeChatClient(self.text_widget, self.server_text_widget, self.entry_widget, self.master, self)
            asyncio.create_task(irc_client.load_ascii_art_macros())
            await irc_client.read_config(config_file)
            await irc_client.connect(config_file)

            # Use the server_name if it is set in the configuration, else use fallback_server_name
            server_name = irc_client.server_name if irc_client.server_name else fallback_server_name
            
            self.add_client(server_name, irc_client)
            asyncio.create_task(irc_client.keep_alive())
            #asyncio.create_task(irc_client.refresher())
            asyncio.create_task(irc_client.handle_incoming_message(config_file))

            self.bind_return_key()
        except Exception as e:
            print(f"Error in init_client_with_config: {e}")

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

            # Remove the clicked channel from highlighted_channels dictionary
            if self.irc_client.server_name in self.irc_client.highlighted_channels:
                server_highlighted_channels = self.irc_client.highlighted_channels[self.irc_client.server_name]
                if clicked_channel in server_highlighted_channels:
                    del server_highlighted_channels[clicked_channel]

    async def switch_channel(self, channel_name):
        server = self.irc_client.server  # Assume the server is saved in the irc_client object

        # Clear the text window
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.config(state=tk.DISABLED)

        # Print the current channel topics dictionary

        is_channel = any(channel_name.startswith(prefix) for prefix in self.irc_client.chantypes)

        if is_channel:
            # It's a channel
            if server in self.irc_client.channel_messages and \
                    channel_name in self.irc_client.channel_messages[server]:

                self.irc_client.current_channel = channel_name
                self.update_nick_channel_label()

                # Update topic label
                current_topic = self.channel_topics.get(self.irc_client.server, {}).get(channel_name, "N/A")
                self.current_topic.set(f"{current_topic}")

                # Display the last messages for the current channel
                self.irc_client.display_last_messages(channel_name, server_name=server)
                self.highlight_nickname()

                self.irc_client.update_gui_user_list(channel_name)
                self.insert_and_scroll()

            else:
                self.insert_text_widget(f"Not a member of channel {channel_name}\n")

        else:
            # It's a DM
            self.user_listbox.delete(0, tk.END)

            # Set current channel to the DM
            self.irc_client.current_channel = channel_name
            self.update_nick_channel_label()

            # Display the last messages for the current DM
            self.irc_client.display_last_messages(channel_name, server_name=server)
            self.insert_and_scroll()
            self.highlight_nickname()

            # No topic for DMs
            self.current_topic.set(f"{channel_name}")

    def insert_and_scroll(self):
        self.text_widget.see(tk.END)
        self.server_text_widget.see(tk.END)

    def clear_chat_window(self):
        current_channel = self.irc_client.current_channel

        if current_channel:
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.config(state=tk.DISABLED)
            self.irc_client.channel_messages[self.irc_client.server][current_channel] = []

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

    def update_ping_label(self, ping_time):
        ping_text = f'Servers: PT{ping_time}'
        self.servers_label.config(text=ping_text)

    def update_users_label(self, away=False):
        if away == True:
            away_text = f"You're Away"
            self.user_label.config(text=away_text, fg="red")
        elif away == False:
            back_text = f"Users"
            self.user_label.config(text=back_text, fg="white")

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
        user_list_cleaned = [nick.lstrip('~&@%+') for nick in user_list]

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
