from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QDoubleSpinBox, QFormLayout
)
from PySide6.QtCore import Qt, QTimer

from src.pdf_splitter import split_pdf_by_green_pages, get_poppler_path
from src.core_worker import WorkerThread

class SplitterArea(QWidget):
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

        form_layout = QFormLayout()
        form_layout.setContentsMargins(
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
        )
        form_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        input_container, self.input_field = self.main_window.create_browse_row(
            "Выберите PDF файл...",
            file_mode=True,
            file_filter="PDF Files (*.pdf)"
        )
        self.input_field.setText(self.main_window.settings.get('splitter_input', ''))
        form_layout.addRow("Входной файл (PDF):", input_container)

        output_container, self.output_field = self.main_window.create_browse_row(
            "Выберите папку для сохранения...",
            file_mode=False
        )
        self.output_field.setText(self.main_window.settings.get('splitter_output', ''))
        form_layout.addRow("Выходная папка:", output_container)

        threshold_container = QWidget()
        threshold_layout = QHBoxLayout(threshold_container)
        threshold_layout.setContentsMargins(0, 0, 0, 0)
        threshold_layout.setSpacing(self.main_window.MARGIN_SMALL)

        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.1, 5.0)
        self.threshold_spin.setValue(self.main_window.settings.get('threshold', 2.3))
        self.threshold_spin.setSingleStep(0.1)
        self.threshold_spin.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.threshold_spin.setAlignment(Qt.AlignCenter)
        self.threshold_spin.setFixedHeight(self.main_window.BUTTON_HEIGHT)

        from src.ui_windows_main_window import load_icon
        minus_btn = self.main_window.create_button(
            "", load_icon("minus-square"),
            lambda: self.threshold_spin.setValue(self.threshold_spin.value() - 0.1),
            icon_only=True
        )
        minus_btn.setProperty("secondary", "true")
        self.main_window.register_themed_btn(minus_btn, "minus-square")

        plus_btn = self.main_window.create_button(
            "", load_icon("plus-square"),
            lambda: self.threshold_spin.setValue(self.threshold_spin.value() + 0.1),
            icon_only=True
        )
        plus_btn.setProperty("secondary", "true")
        self.main_window.register_themed_btn(plus_btn, "plus-square")

        threshold_layout.addWidget(minus_btn)
        threshold_layout.addWidget(self.threshold_spin)
        threshold_layout.addWidget(plus_btn)
        threshold_layout.addStretch()

        form_layout.addRow("Порог зелёной страницы:", threshold_container)
        layout.addLayout(form_layout)
        layout.addStretch()

    def get_settings(self) -> dict:
        return {
            'splitter_input': self.input_field.text(),
            'splitter_output': self.output_field.text(),
            'threshold': self.threshold_spin.value()
        }

    def split_pdf(self):
        input_path = self.input_field.text()
        output_dir = self.output_field.text()
        threshold = self.threshold_spin.value()

        if not input_path or not output_dir:
            self.main_window.log_message("Выберите входной файл и выходную папку")
            return

        if self.main_window.worker and self.main_window.worker.isRunning():
            self.main_window.stop_worker()

        self.main_window.worker = WorkerThread()
        self.main_window.worker.set_target(
            split_pdf_by_green_pages,
            input_path, output_dir, get_poppler_path(), threshold
        )

        self.main_window.worker.progress_signal.connect(self.main_window.update_progress)
        self.main_window.worker.message_signal.connect(self.main_window.log_message)
        self.main_window.worker.error_signal.connect(self.main_window.log_message)
        self.main_window.worker.finished.connect(lambda: self.main_window.set_worker_state(False))
        self.main_window.worker.finished.connect(self.main_window.reset_progress_bar)
        self.main_window.worker.error_signal.connect(self.main_window.reset_progress_bar)

        def on_split_finished():
            if self.main_window.settings.get('auto_run_renamer', False):
                self.main_window.tabs.setCurrentWidget(self.main_window.renamer_area)
                self.main_window.renamer_area.input_field.setText(output_dir)
                if not self.main_window.renamer_area.output_field.text():
                    self.main_window.renamer_area.output_field.setText(output_dir)
                QTimer.singleShot(500, lambda: self.main_window.renamer_area.rename_pdf())

        self.main_window.worker.finished.connect(on_split_finished)

        self.main_window.set_worker_state(True)
        self.main_window.worker.start()
        self.main_window.settings.update(self.get_settings())

    def get_action(self):
        return {
            "text": "Разделить PDF",
            "icon": None,
            "handler": self.split_pdf
        }
