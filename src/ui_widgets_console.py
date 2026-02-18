from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QPlainTextEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon


class LogConsole(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.addStretch(1)
        self.clear_btn = QPushButton("Очистить")
        self.clear_btn.setProperty("small", "true")
        self.clear_btn.setProperty("secondary", "true")
        self.clear_btn.clicked.connect(self.clear)
        header.addWidget(self.clear_btn, alignment=Qt.AlignRight)
        layout.addLayout(header)

        self.view = QPlainTextEdit()
        self.view.setReadOnly(True)
        self.view.setObjectName("logView")
        layout.addWidget(self.view, stretch=1)

    def append_line(self, text: str):
        self.view.appendPlainText(text)

    def clear(self):
        self.view.clear()

    def set_min_height(self, h: int):
        self.view.setMinimumHeight(h)

    def set_grip_icon(self, icon: QIcon):
        pass

