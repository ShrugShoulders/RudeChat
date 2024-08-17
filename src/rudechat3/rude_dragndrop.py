import tkinter as tk
from .shared_imports import *

class DragDropListbox(tk.Listbox):
    def __init__(self, master, update_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.update_callback = update_callback
        self.drag_in_progress = False
        self.motion_timer = None
        
        self.bind('<Button-1>', self.on_button_press)
        self.bind('<B1-Motion>', self.on_motion)
        
        self._drag_data = {"x": 0, "y": 0, "item": None}

    def on_button_press(self, event):
        '''Record the item and its position'''
        self._drag_data["item"] = self.nearest(event.y)
        self._drag_data["y"] = event.y

    def on_motion(self, event):
        '''Handle dragging of an item'''
        if not self.drag_in_progress:
            self.start_drag(event)
        
        y = event.y
        index = self.nearest(y)
        
        if index < self._drag_data["item"] and y < self._drag_data["y"]:
            self._drag_data["item"] -= 1
            self.move_item(self._drag_data["item"] + 1, self._drag_data["item"])
            self._drag_data["y"] = y
        elif index > self._drag_data["item"] and y > self._drag_data["y"]:
            self._drag_data["item"] += 1
            self.move_item(self._drag_data["item"] - 1, self._drag_data["item"])
            self._drag_data["y"] = y
        
        # Reset the motion timer
        self.reset_motion_timer()

    def start_drag(self, event):
        '''Set drag in progress'''
        self.drag_in_progress = True

    def stop_drag(self, event):
        '''Reset drag flag'''
        self.drag_in_progress = False

    def move_item(self, from_idx, to_idx):
        '''Move item from one index to another'''
        item = self.get(from_idx)
        self.delete(from_idx)
        self.insert(to_idx, item)

    def reset_motion_timer(self):
        '''Reset motion timer to delay update callback'''
        if self.motion_timer:
            self.after_cancel(self.motion_timer)
            self.motion_timer = None

        # Schedule update callback after delay if no motion detected
        self.motion_timer = self.after(200, self.call_update_callback)

    def call_update_callback(self):
        '''Call the update callback'''
        if self.update_callback:
            self.update_callback()
