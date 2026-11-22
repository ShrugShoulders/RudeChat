#!/usr/bin/env python3
"""The input box, with keyboard shortcuts and menus for IRC colour and formatting codes."""
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

class RudeMessageEntry(QLineEdit):
"""Single-line input box for chat messages and slash commands.

    Formatting only applies to selected text. The selection is wrapped in the
    matching IRC control codes and the cursor moves to the end of it.
"""
    def __init__(self, parent=None):
    """Create the entry and register the formatting shortcuts."""
        super().__init__(parent)
        self.add_shortcuts()

    def add_shortcuts(self):
    """Register Ctrl shortcuts for IRC formatting.

        Bold is Ctrl+B, italic Ctrl+I, strike-through Ctrl+S and inverse
        Ctrl+/. Underline is Ctrl+U on macOS and Windows and Ctrl+N elsewhere.
    """
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
    """Extend the standard menu with Colors (grouped by ten) and Formatting submenus."""
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
    """Wrap the selected text in an IRC colour code.

        Args:
            color_code: Two-digit IRC colour code, as in ``IRC_COLORS``.
    """
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
    """Wrap the selected text in an IRC formatting code, ending with a reset.

        Args:
            format_code: One control character from ``IRC_FORMAT``, such as
                the bold code (0x02).
    """
        selected_text = self.selectedText()

        if selected_text:
            formatted = f"{format_code}{selected_text}\x0F"
            current_text = self.text()
            start = self.selectionStart()
            end = start + len(selected_text)
            new_text = current_text[:start] + formatted + current_text[end:]
            self.setText(new_text)
            self.setCursorPosition(start + len(formatted))