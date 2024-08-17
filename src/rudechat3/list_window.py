#!/usr/bin/env python
from rudechat3.shared_imports import *

class ChannelListWindow(tk.Toplevel):
    def __init__(self, client, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Channel List")
        self.geometry("790x400")

        self.client = client  # The AsyncIRCClient instance
        self.is_destroyed = False  # To check if the window has been destroyed
        self.sort_order = "ascending"  # Default sort order for users

        self.create_widgets()

        # Start the periodic UI update
        self.after(100, self.update_ui_periodically)

        # Start populating the channel list
        asyncio.create_task(self.populate_channel_list())

    def create_widgets(self):
        self.search_label = ttk.Label(self, text="Search Channel/Topic:")
        self.search_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.search_entry = ttk.Entry(self)
        self.search_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self.handle_search)  # Bind the search function

        self.tree = ttk.Treeview(self, columns=("Channel", "Users", "Topic"), show='headings')
        self.tree.heading("Channel", text="Channel")
        self.tree.heading("Users", text="Users", command=self.sort_by_users)
        self.tree.heading("Topic", text="Topic")

        self.tree.grid(row=1, column=0, columnspan=2, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=1, column=2, sticky="ns")

        self.close_button = ttk.Button(self, text="Close", command=self.destroy)
        self.close_button.grid(row=2, column=0, columnspan=2, pady=10, padx=10, sticky="ew")

        # Make the Treeview and scrollbar resizable
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def sort_by_users(self):
        # Toggle the sort order
        self.sort_order = "descending" if self.sort_order == "ascending" else "ascending"
        
        # Get the list of channels
        channels = [(self.tree.item(child)["values"][0], int(self.tree.item(child)["values"][1]), self.tree.item(child)["values"][2])
                    for child in self.tree.get_children()]
        
        # Sort the channels by user count
        channels.sort(key=lambda x: x[1], reverse=self.sort_order == "descending")
        
        # Clear the existing entries
        self.tree.delete(*self.tree.get_children())
        
        # Repopulate the Treeview with sorted data
        for channel in channels:
            self.tree.insert("", tk.END, values=(channel[0], channel[1], channel[2]))

    async def populate_channel_list(self):
        processed_channel_names = set()  # To keep track of channels already processed

        while True:
            if self.is_destroyed:
                break  # Stop populating if the window is destroyed

            # Populate the list with new channels
            for channel, info in self.client.download_channel_list.items():
                if channel not in processed_channel_names:
                    # Insert the new channel into the Treeview
                    self.tree.insert("", tk.END, values=(channel, info['user_count'], info['topic']))

                    # Mark this channel as processed
                    processed_channel_names.add(channel)

            await asyncio.sleep(0.1)  # Allow time for more channels to be added

    def update_ui_periodically(self):
        if self.is_destroyed:
            return

        self.after(100, self.update_ui_periodically)

    def handle_search(self, event=None):
        search_text = self.search_entry.get().lower()
        # Remove previous search results
        self.tree.delete(*self.tree.get_children())
        # Populate the list with channels matching the search text, considering current sort order
        channels = [(channel, info['user_count'], info['topic']) for channel, info in self.client.download_channel_list.items()
                    if search_text in channel.lower() or search_text in info['topic'].lower()]
        
        # Sort channels based on the current sort order
        channels.sort(key=lambda x: x[1], reverse=self.sort_order == "descending")
        
        for channel in channels:
            self.tree.insert("", tk.END, values=(channel[0], channel[1], channel[2]))

    async def update_channel_info(self, channel_name, user_count, topic):
        self.tree.insert("", tk.END, values=(channel_name, user_count, topic))

    def destroy(self):
        self.is_destroyed = True
        super().destroy()
