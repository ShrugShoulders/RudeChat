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

from shared_imports import *

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

        self.after(100, self.update_ui_periodically)

    async def update_channel_info(self, channel_name, user_count, topic):
        self.tree.insert("", tk.END, values=(channel_name, user_count, topic))

    async def stop_progress_bar(self):
        if not self.is_destroyed:
            self.progress_bar.stop()

    def destroy(self):
        self.is_destroyed = True
        super().destroy()