#!/usr/bin/env python3
"""The main chat view: a text browser that opens clicked links in the system browser."""
from rudechat4.shared_imports import *
from rudechat4.global_variables import *

class RudeTextBrowser(QTextBrowser):
"""Read-only chat display.

    Link navigation is turned off inside the widget. A left click on a link
    is handed to ``webbrowser.open`` instead, and only the left mouse button
    is passed on for double clicks and releases.
"""
    def __init__(self, parent=None):
    """Disable Qt's own link opening."""
        super().__init__(parent)
        self.setOpenLinks(False)

    def get_anchor_at(self, pos):
    """Return the link URL under a point.

        Args:
            pos: Position in widget coordinates.

        Returns:
            The href string, or None if the point isn't on a link.
    """
        cursor = self.cursorForPosition(pos)
        char_format = cursor.charFormat()
        if char_format.isAnchor():
            return char_format.anchorHref()

    def is_anchor_at(self, pos):
    """Return True if the point is over a link."""
        cursor = self.cursorForPosition(pos)
        return cursor.charFormat().isAnchor()

    def reset_cursor_position(self):
    """Reset the cursor to the bottom-right position."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        self.setTextCursor(cursor)

    def copy(self):
    """Copy the selection, then move the cursor back to the end of the last block."""
        super().copy()
        self.reset_cursor_position()

    def contextMenuEvent(self, event):
    """Show the standard context menu and reset the cursor after Copy."""
        menu = self.createStandardContextMenu()
        copy_action = menu.actions()[0] if menu.actions() else None
        if copy_action:
            copy_action.triggered.connect(self.reset_cursor_position)
        menu.exec(event.globalPos())

    def keyPressEvent(self, event: QKeyEvent):
    """Pass key presses to the base class unchanged."""
        super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
    """Handle double clicks from the left button only."""
        if event.button() == Qt.MouseButton.LeftButton:
            super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
    """Handle mouse releases from the left button only."""
        if event.button() == Qt.MouseButton.LeftButton:
            super().mouseReleaseEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
    """Open a link in the system browser on left click, then pass the event on."""
        if event.button() == Qt.MouseButton.LeftButton and self.is_anchor_at(event.pos()):
            url = self.get_anchor_at(event.pos())
            if url:
                webbrowser.open(url)
        super().mousePressEvent(event)