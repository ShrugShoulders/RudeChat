#!/usr/bin/env python
from shared_imports import *
class ChannelListWindow(tk.Toplevel):
    def __init__(self, file_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Channel List")
        self.geometry("790x400")
        self.is_destroyed = False
        self.total_channels = 0

        self.create_widgets()
        self.start_download_thread(file_path)

    def create_widgets(self):
        self.tree = ttk.Treeview(self, columns=("Channel", "Users", "Topic"), show='headings')
        self.tree.heading("Channel", text="Channel")
        self.tree.heading("Users", text="Users")
        self.tree.heading("Topic", text="Topic")

        self.close_button = ttk.Button(self, text="Close", command=self.destroy)
        self.close_button.grid(row=1, column=0, columnspan=2, pady=10, padx=10, sticky="ew")

        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Progress bar
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", mode="determinate")
        self.progress_bar.grid(row=2, column=0, columnspan=2, pady=10, padx=10, sticky="ew")

    def start_download_thread(self, file_path):
        self.total_channels = sum(1 for _ in open(file_path, 'r', encoding='utf-8'))
        download_thread = threading.Thread(target=self.read_and_insert_data, args=(file_path,), daemon=True)
        download_thread.start()

    def read_and_insert_data(self, file_path):
        processed_channels = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, start=1):
                    parts = line.strip().split(", ")
                    if len(parts) < 3:
                        print(f"Skipping malformed line at Line {line_num}: {line}")
                        continue
                    try:
                        channel_name = parts[0].split(": ")[1]
                        user_count = parts[1].split(": ")[1]
                        topic = parts[2].split(": ")[1] if len(parts[2].split(": ")) > 1 else "No topic"
                        if channel_name == "*":
                            channel_name = "Hidden"
                    except Exception as e:
                        print(f"Error processing line {line_num} due to {e}: {line}")
                        continue

                    if not self.is_destroyed:
                        self.after(0, lambda cn=channel_name, uc=user_count, t=topic: self.tree.insert("", "end", values=(cn, uc, t)))
                        processed_channels += 1
                        progress = (processed_channels / self.total_channels) * 100
                        self.after(0, lambda p=progress: self.progress_bar.configure(value=p))
        except Exception as e:
            print(f"Error reading the file {file_path} due to {e}")

    def destroy(self):
        self.is_destroyed = True
        super().destroy()
