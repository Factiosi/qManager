from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QGroupBox, QStyle
)
from PySide6.QtCore import Qt

from src.pdf_organizer import organize_pdfs
from src.core_worker import WorkerThread
from src.ui_mixins_excel_mode import ExcelModeMixin

class OrganizerArea(QWidget, ExcelModeMixin):
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
        self.input_field.setText(self.main_window.settings.get('organizer_input', ''))
        form_layout.addRow("Входная папка:", input_container)

        output_container, self.output_field = self.main_window.create_browse_row(
            "Выберите папку для сохранения...",
            file_mode=False
        )
        self.output_field.setText(self.main_window.settings.get('organizer_output', ''))
        form_layout.addRow("Выходная папка:", output_container)

        excel_container, self.excel_field = self.main_window.create_browse_row(
            "Выберите Excel файл...",
            file_mode=True,
            file_filter="Excel Files (*.xlsx *.xls)"
        )
        self.excel_field.setText(self.main_window.settings.get('organizer_excel_file', ''))
        form_layout.addRow("Excel файл:", excel_container)
        self.excel_container = excel_container
        self.excel_form_row_index = form_layout.rowCount() - 1
        self.form_layout = form_layout

        layout.addLayout(form_layout)
        layout.addStretch()
        
        self.setup_excel_field_visibility()
        
        self.input_field.setToolTip("Выберите папку с PDF файлами для организации")
        self.output_field.setToolTip("Выберите папку для сохранения организованных файлов")

    def organize_pdf(self):
        if not self.check_inputs():
            return

        from datetime import datetime
        input_folder = self.input_field.text()
        output_folder = self.output_field.text()
        excel_mode = self.main_window.settings.get('excel_mode', 'logos')
        merge_mode = self.main_window.settings.get('merge_mode', 'order')
        filter_mode = self.main_window.settings.get('filter_mode', 'unlimited')
        excel_path = None if excel_mode == 'sheets' else self.excel_field.text()

        filter_date_from = None
        filter_date_to = None
        if filter_mode == 'period':
            for key, attr in [('filter_date_from', 'filter_date_from'), ('filter_date_to', 'filter_date_to')]:
                val = self.main_window.settings.get(key)
                if val:
                    try:
                        parsed = datetime.strptime(val, "%Y-%m-%d")
                        if attr == 'filter_date_from':
                            filter_date_from = parsed
                        else:
                            filter_date_to = parsed
                    except ValueError:
                        pass

        if self.main_window.worker and self.main_window.worker.isRunning():
            self.main_window.stop_worker()

        self.main_window.worker = WorkerThread()
        self.main_window.worker.set_target(
            organize_pdfs,
            input_folder, output_folder, excel_path,
            mode=excel_mode,
            merge_mode=merge_mode,
            filter_mode=filter_mode,
            filter_date_from=filter_date_from,
            filter_date_to=filter_date_to,
            debug_mode=self.main_window.settings.get('debug_mode', False)
        )
        self.main_window.worker.progress_signal.connect(self.main_window.update_progress)
        self.main_window.worker.message_signal.connect(self.main_window.log_message)
        self.main_window.worker.error_signal.connect(self.main_window.log_message)
        self.main_window.worker.finished.connect(lambda: self.main_window.set_worker_state(False))
        self.main_window.worker.finished.connect(self.main_window.reset_progress_bar)
        self.main_window.worker.error_signal.connect(self.main_window.reset_progress_bar)

        self.main_window.set_worker_state(True)
        self.main_window.worker.start()
        self.main_window.settings.update(self.get_settings())

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
            'organizer_input': self.input_field.text(),
            'organizer_output': self.output_field.text(),
            'organizer_excel_file': self.excel_field.text()
        }

    def get_action(self):
        return {
            "text": "Организовать PDF",
            "icon": None,
            "handler": self.organize_pdf
        }
