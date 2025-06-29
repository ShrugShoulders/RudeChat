#!/usr/bin/env python3
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

class RudeMessageEntry(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.add_shortcuts()

    def add_shortcuts(self):
        platform = sys.platform
        is_mac = platform == "darwin"
        is_windows = platform.startswith("win")

        # Add shortcuts
        QShortcut(QKeySequence("Ctrl+B"), self, activated=lambda: self.apply_irc_format("\x02"))  # Bold
        QShortcut(QKeySequence("Ctrl+I"), self, activated=lambda: self.apply_irc_format("\x1D"))  # Italic

        # Underline → Ctrl+U for Windows + Mac, Ctrl+- otherwise
        underline_key = "Ctrl+U" if is_mac or is_windows else "Ctrl+N"
        QShortcut(QKeySequence(underline_key), self, activated=lambda: self.apply_irc_format("\x1F"))

        QShortcut(QKeySequence("Ctrl+S"), self, activated=lambda: self.apply_irc_format("\x1E"))  # Strike Through
        QShortcut(QKeySequence("Ctrl+/"), self, activated=lambda: self.apply_irc_format("\x16"))  # Inverse

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()

        color_menu = menu.addMenu("Colors")
        format_menu = menu.addMenu("Formatting")

        # Group them by 10s
        grouped_colors = {}
        for name, code in IRC_COLORS.items():
            group_label = f"{(int(code) // 10) * 10:02d}–{(int(code) // 10) * 10 + 9:02d}"
            grouped_colors.setdefault(group_label, []).append((name, code))

        for group, items in grouped_colors.items():
            group_menu = color_menu.addMenu(group)
            for name, code in items:
                action = QAction(name, self)
                action.triggered.connect(lambda checked, c=code: self.apply_irc_color(c))
                group_menu.addAction(action)

        for label, code in IRC_FORMAT:
            action = QAction(label, self)
            action.triggered.connect(lambda checked, c=code: self.apply_irc_format(c))
            format_menu.addAction(action)

        menu.exec(event.globalPos())

    def apply_irc_color(self, color_code):
        cursor = self.cursorPosition()
        selected_text = self.selectedText()

        if selected_text:
            color_tagged = f"\x03{color_code}{selected_text}\x03"
            current_text = self.text()
            start = self.selectionStart()
            end = start + len(selected_text)
            new_text = current_text[:start] + color_tagged + current_text[end:]
            self.setText(new_text)
            self.setCursorPosition(start + len(color_tagged))

    def apply_irc_format(self, format_code):
        selected_text = self.selectedText()

        if selected_text:
            formatted = f"{format_code}{selected_text}\x0F"
            current_text = self.text()
            start = self.selectionStart()
            end = start + len(selected_text)
            new_text = current_text[:start] + formatted + current_text[end:]
            self.setText(new_text)
            self.setCursorPosition(start + len(formatted))