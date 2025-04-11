from rudechat4.shared_imports import *

class RudeTextBrowser(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpenLinks(False)

    def get_anchor_at(self, pos):
        cursor = self.cursorForPosition(pos)
        char_format = cursor.charFormat()
        if char_format.isAnchor():
            return char_format.anchorHref()

    def is_anchor_at(self, pos):
        cursor = self.cursorForPosition(pos)
        return cursor.charFormat().isAnchor()

    def reset_cursor_position(self):
        """Reset the cursor to the bottom-right position."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        self.setTextCursor(cursor)

    def copy(self):
        super().copy()
        self.reset_cursor_position()

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        copy_action = menu.actions()[0] if menu.actions() else None
        if copy_action:
            copy_action.triggered.connect(self.reset_cursor_position)
        menu.exec(event.globalPos())

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            super().mouseReleaseEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.is_anchor_at(event.pos()):
            url = self.get_anchor_at(event.pos())
            if url:
                webbrowser.open(url)
        super().mousePressEvent(event)