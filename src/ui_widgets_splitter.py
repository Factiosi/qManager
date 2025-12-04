from PySide6.QtWidgets import QSplitter, QSplitterHandle
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QIcon


class IconSplitterHandle(QSplitterHandle):
    def __init__(self, orientation, parent, icon: QIcon | None = None, size_px: int = 18):
        super().__init__(orientation, parent)
        self._icon = icon or QIcon()
        self._size = size_px

    def setIcon(self, icon: QIcon):
        self._icon = icon or QIcon()
        self.update()

    def sizeHint(self):
        parent = self.parentWidget()
        if not parent:
            return QSize(self._size, self._size)
        if self.orientation() == Qt.Vertical:
            return QSize(parent.width(), self._size)
        return QSize(self._size, parent.height())

    def paintEvent(self, event):
        # Проверяем, что виджет готов к рисованию
        if self.width() <= 0 or self.height() <= 0:
            return
        
        painter = QPainter()
        if not painter.begin(self):
            return
        
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            if not self._icon.isNull():
                pm = self._icon.pixmap(self._size, self._size)
                if pm and not pm.isNull():
                    x = (self.width() - pm.width()) // 2
                    y = (self.height() - pm.height()) // 2
                    painter.drawPixmap(x, y, pm)
        finally:
            painter.end()


class IconSplitter(QSplitter):
    def __init__(self, orientation=Qt.Vertical, parent=None, icon: QIcon | None = None, size_px: int = 18):
        super().__init__(orientation, parent)
        self._icon = icon or QIcon()
        self._size_px = size_px
        self.setHandleWidth(size_px)  # толщина равна размеру иконки

    def setHandleIcon(self, icon: QIcon):
        self._icon = icon or QIcon()
        h = self.handle(1)
        if isinstance(h, IconSplitterHandle):
            h.setIcon(self._icon)

    def createHandle(self):
        return IconSplitterHandle(self.orientation(), self, self._icon, self._size_px)

