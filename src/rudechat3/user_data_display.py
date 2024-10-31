import tkinter as tk

class RudeToolTip:
    def __init__(self, widget, gui):
        self.widget = widget
        self.tooltip_window = None
        self.gui = gui

    def show_tooltip(self, text, x, y):
        # Destroy previous tooltip to ensure it updates
        self.hide_tooltip()

        # Shift tooltip to appear more on the left
        x = x + self.widget.winfo_rootx() - 100
        y = y + self.widget.winfo_rooty() + 25

        # Create a Toplevel window as a tooltip
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        # Add tooltip label with wrap and alignment
        label = tk.Label(self.tooltip_window, text=text, foreground=self.gui.main_fg_color, background=self.gui.master_bg, borderwidth=1, relief="solid", justify='left', wraplength=200)
        label.pack()

    def hide_tooltip(self):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None