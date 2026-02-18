from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QGroupBox, QStyle
)
from PySide6.QtCore import Qt

from src.pdf_renamer import process_pdfs
from src.core_worker import WorkerThread
from src.ui_mixins_excel_mode import ExcelModeMixin

class RenamerArea(QWidget, ExcelModeMixin):
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
            "Выберите входную папку...",
            file_mode=False
        )
        self.input_field.setText(self.main_window.settings.get('renamer_input', ''))
        form_layout.addRow("Входная папка:", input_container)

        
        output_container, self.output_field = self.main_window.create_browse_row(
            "Выберите папку для сохранения...",
            file_mode=False
        )
        self.output_field.setText(self.main_window.settings.get('renamer_output', ''))
        form_layout.addRow("Выходная папка:", output_container)

        
        excel_container, self.excel_field = self.main_window.create_browse_row(
            "Выберите Excel файл...",
            file_mode=True,
            file_filter="Excel Files (*.xlsx *.xls)"
        )
        self.excel_field.setText(self.main_window.settings.get('excel_file', ''))
        form_layout.addRow("Excel файл:", excel_container)
        self.excel_container = excel_container
        self.excel_form_row_index = form_layout.rowCount() - 1
        self.form_layout = form_layout

        layout.addLayout(form_layout)
        layout.addStretch()

        self.setup_excel_field_visibility()
        
        self.input_field.setToolTip("Выберите папку с PDF файлами для переименования")
        self.output_field.setToolTip("Выберите папку для сохранения переименованных файлов")

    def rename_pdf(self):
        if not self.check_inputs():
            return

        input_dir = self.input_field.text()
        output_dir = self.output_field.text()
        excel_mode = self.main_window.settings.get('excel_mode', 'logos')
        excel_path = None if excel_mode == 'sheets' else self.excel_field.text()

        if self.main_window.worker and self.main_window.worker.isRunning():
            self.main_window.stop_worker()
            
        self.main_window.worker = WorkerThread()
        ocr_binarization = self.main_window.settings.get('ocr_binarization', False)
        
        self.main_window.worker.set_target(
            process_pdfs,
            input_folder=input_dir,
            output_folder=output_dir,
            excel_path=excel_path,
            mode=excel_mode,
            ocr_binarization=ocr_binarization,
            debug_mode=self.main_window.settings.get('debug_mode', False)
        )
        self.main_window.worker.progress_signal.connect(self.main_window.update_progress)
        self.main_window.worker.message_signal.connect(self.main_window.log_message)
        self.main_window.worker.error_signal.connect(self.main_window.log_message)
        self.main_window.worker.finished.connect(lambda: self.main_window.set_worker_state(False))
        self.main_window.worker.finished.connect(self.main_window.reset_progress_bar)
        self.main_window.worker.error_signal.connect(self.main_window.reset_progress_bar)
        
        self.main_window.worker.start()
        self.main_window.set_worker_state(True)

    def check_inputs(self) -> bool:
        if not self.input_field.text():
            self.main_window.log_message("Ошибка: Не выбрана входная папка")
            return False
        if not self.output_field.text():
            self.main_window.log_message("Ошибка: Не выбрана выходная папка")
            return False
        excel_mode = self.main_window.settings.get('excel_mode', 'logos')
        if excel_mode != 'sheets' and not self.excel_field.text():
            self.main_window.log_message("Ошибка: Не выбран Excel файл")
            return False
        return True

    def get_settings(self) -> dict:
        return {
            'renamer_input': self.input_field.text(),
            'renamer_output': self.output_field.text(),
            'excel_file': self.excel_field.text()
        }

    def get_action(self):
        return {
            "text": "Переименовать PDF",
            "icon": None,
            "handler": self.rename_pdf
        }
