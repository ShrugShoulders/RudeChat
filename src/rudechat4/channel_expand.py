from rudechat4.shared_imports import *

class ChannelExp:
    def __init__(self, parent, channels, entry_bg_color, entry_fg_color):
        self.channels = channels
        self.root = parent
        self.window = tk.Toplevel(self.root)
        self.window.configure(bg=entry_bg_color)
        self.window.title("Channel Edit Example: #channel,#channel,#channel")
        self.entry_bg_color = entry_bg_color
        self.entry_fg_color = entry_fg_color
        self.create_window()

    def create_window(self):
        # Long text entry field
        channel_len = len(self.channels)
        self.text_entry = tk.Entry(self.window, width=channel_len, bg=self.entry_bg_color, fg=self.entry_fg_color, insertbackground="white")
        self.text_entry.insert(0, self.channels)  # Set initial values
        self.text_entry.pack(padx=10, pady=10, fill="both", expand=True)

        # Submit button
        submit_button = tk.Button(self.window, text="Submit", command=self.close_window, bg=self.entry_bg_color, fg=self.entry_fg_color)
        submit_button.pack(pady=10)

    def close_window(self):
        self.channels = self.text_entry.get()
        self.window.destroy()

    def get_channels(self):
        self.window.wait_window(self.window)
        return self.channels