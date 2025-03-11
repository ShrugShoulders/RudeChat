import tkinter as tk

class RudeToolTip:
    def __init__(self, widget, gui, app_size):
        self.widget = widget
        self.tooltip_window = None
        self.gui = gui
        self.app_size = app_size
        self.def_x = 100
        self.def_y = 25
        self.def_wordwrap = 200
        self.set_size_variables()

    def show_tooltip(self, text, x, y):
        # Destroy previous tooltip to ensure it updates
        self.hide_tooltip()

        # Shift tooltip to appear more on the left
        x = x + self.widget.winfo_rootx() - self.def_x
        y = y + self.widget.winfo_rooty() + self.def_y

        # Create a Toplevel window as a tooltip
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        # Add tooltip label with wrap and alignment
        label = tk.Label(self.tooltip_window, text=text, foreground=self.gui.main_fg_color, background=self.gui.master_bg, borderwidth=1, relief="solid", justify='left', wraplength=self.def_wordwrap)
        label.pack()

    def set_size_variables(self):
        if self.app_size == "2200x1800":
            self.def_x = 200
            self.def_y = 50
            self.def_wordwrap = 400
        elif self.app_size == "1920x1080":
            self.def_x = 100
            self.def_y = 25
            self.def_wordwrap = 200
        else:
            self.def_x = 100
            self.def_y = 25
            self.def_wordwrap = 200

    def hide_tooltip(self):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None