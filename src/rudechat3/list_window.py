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

from .shared_imports import *

class ChannelListWindow(tk.Toplevel):
    def __init__(self, client, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Channel List")
        self.geometry("790x400")

        self.client = client
        self.is_destroyed = False
        self.sort_order = "ascending"

        self.create_widgets()
        
        self.after(100, self.update_ui_periodically)

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

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def sort_by_users(self):
        self.sort_order = "descending" if self.sort_order == "ascending" else "ascending"
        
        channels = [(self.tree.item(child)["values"][0], int(self.tree.item(child)["values"][1]), self.tree.item(child)["values"][2])
                    for child in self.tree.get_children()]
        
        channels.sort(key=lambda x: x[1], reverse=self.sort_order == "descending")
        
        self.tree.delete(*self.tree.get_children())
        
        for channel in channels:
            self.tree.insert("", tk.END, values=(channel[0], channel[1], channel[2]))

    async def populate_channel_list(self):
        processed_channel_names = set()

        while True:
            if self.is_destroyed:
                break  

            for channel, info in self.client.download_channel_list.items():
                if channel not in processed_channel_names:
                    self.tree.insert("", tk.END, values=(channel, info['user_count'], info['topic']))

                    processed_channel_names.add(channel)

            await asyncio.sleep(0.1) 

    def update_ui_periodically(self):
        if self.is_destroyed:
            return

        self.after(100, self.update_ui_periodically)

    def handle_search(self, event=None):
        search_text = self.search_entry.get().lower()
        self.tree.delete(*self.tree.get_children())
        channels = [(channel, info['user_count'], info['topic']) for channel, info in self.client.download_channel_list.items()
                    if search_text in channel.lower() or search_text in info['topic'].lower()]
        
        channels.sort(key=lambda x: x[1], reverse=self.sort_order == "descending")
        
        for channel in channels:
            self.tree.insert("", tk.END, values=(channel[0], channel[1], channel[2]))

    async def update_channel_info(self, channel_name, user_count, topic):
        self.tree.insert("", tk.END, values=(channel_name, user_count, topic))

    def destroy(self):
        self.is_destroyed = True
        super().destroy()
