from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QFormLayout, QLabel


class PlaywrightArea(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
        )
        group = QGroupBox("Playwright")
        form = QFormLayout()
        form.addRow(QLabel("Здесь появятся инструменты Playwright (в разработке)."))
        group.setLayout(form)
        layout.addWidget(group)
        layout.addStretch()

    def get_action(self):
        return {
            "text": "",
            "icon": None,
            "handler": None
        }

