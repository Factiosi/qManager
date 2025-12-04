from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QGroupBox, QStyle
)

from src.pdf_renamer import process_pdfs
from src.core_worker import WorkerThread

class RenamerArea(QWidget):
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
        self.excel_container = excel_container  # Сохраняем ссылку на контейнер
        self.excel_form_row_index = form_layout.rowCount() - 1  # Индекс строки в форме
        self.form_layout = form_layout  # Сохраняем ссылку на форму

        layout.addLayout(form_layout)
        layout.addStretch()

        # Обновляем видимость поля Excel в зависимости от режима
        # Используем QTimer для отложенного подключения, чтобы settings_area был создан
        from PySide6.QtCore import QTimer
        QTimer.singleShot(200, lambda: self.update_excel_field_visibility())
        QTimer.singleShot(300, self.connect_settings_changes)
        
        self.input_field.setToolTip("Выберите папку с PDF файлами для переименования")
        self.output_field.setToolTip("Выберите папку для сохранения переименованных файлов")
    
    def update_excel_field_visibility(self):
        """Обновляет видимость поля Excel в зависимости от режима таблиц"""
        excel_mode = self.main_window.settings.get('excel_mode', 'logos')
        if excel_mode == 'sheets':
            # Скрываем поле Excel для режима Google Sheets
            if hasattr(self, 'excel_container'):
                self.excel_container.setVisible(False)
            if hasattr(self, 'excel_field'):
                self.excel_field.setVisible(False)
            # Скрываем метку через форму
            if hasattr(self, 'form_layout') and hasattr(self, 'excel_form_row_index'):
                try:
                    item = self.form_layout.itemAt(self.excel_form_row_index, QFormLayout.LabelRole)
                    if item and item.widget():
                        item.widget().setVisible(False)
                except Exception:
                    pass
        else:
            if hasattr(self, 'excel_container'):
                self.excel_container.setVisible(True)
            if hasattr(self, 'excel_field'):
                self.excel_field.setVisible(True)
            # Показываем метку через форму
            if hasattr(self, 'form_layout') and hasattr(self, 'excel_form_row_index'):
                try:
                    item = self.form_layout.itemAt(self.excel_form_row_index, QFormLayout.LabelRole)
                    if item and item.widget():
                        item.widget().setVisible(True)
                except Exception:
                    pass
    
    def connect_settings_changes(self):
        """Подключает обработчик изменений режима таблиц"""
        if hasattr(self.main_window, 'settings_area'):
            try:
                self.main_window.settings_area.excel_mode_combo.currentTextChanged.connect(
                    lambda: self.update_excel_field_visibility()
                )
            except Exception:
                pass

    def rename_pdf(self):
        """
        Начать процесс переименования PDF файлов
        """
        if not self.check_inputs():
            return
            
        input_dir = self.input_field.text()
        output_dir = self.output_field.text()
        excel_mode = self.main_window.settings.get('excel_mode', 'logos')
        
        # Для режима Google Sheets передаем None вместо пути к Excel
        if excel_mode == 'sheets':
            excel_path = None
        else:
            excel_path = self.excel_field.text()

        # Останавливаем предыдущий worker если он запущен
        if self.main_window.worker and self.main_window.worker.isRunning():
            self.main_window.stop_worker()
            
        self.main_window.worker = WorkerThread()
        self.main_window.worker.set_target(
            process_pdfs,
            input_folder=input_dir,
            output_folder=output_dir,
            excel_path=excel_path,
            mode=excel_mode
        )
        self.main_window.worker.progress_signal.connect(self.main_window.update_progress)
        self.main_window.worker.message_signal.connect(self.main_window.log_message)
        self.main_window.worker.error_signal.connect(self.main_window.log_message)
        self.main_window.worker.finished.connect(lambda: self.main_window.set_worker_state(False))
        # Сбрасываем прогресс-бар при завершении
        self.main_window.worker.finished.connect(lambda: self.main_window.progress_bar.setValue(0))
        # Сбрасываем прогресс-бар при ошибке
        self.main_window.worker.error_signal.connect(lambda: self.main_window.progress_bar.setValue(0))
        self.main_window.worker.start()
        self.main_window.set_worker_state(True)

    def check_inputs(self) -> bool:
        """Проверка наличия всех необходимых входных данных"""
        if not self.input_field.text():
            self.main_window.log_message("Ошибка: Не выбрана входная папка")
            return False
            
        if not self.output_field.text():
            self.main_window.log_message("Ошибка: Не выбрана выходная папка")
            return False
            
        # Для режима Google Sheets не требуем Excel файл
        excel_mode = self.main_window.settings.get('excel_mode', 'logos')
        if excel_mode != 'sheets' and not self.excel_field.text():
            self.main_window.log_message("Ошибка: Не выбран Excel файл")
            return False
            
        return True

    def get_settings(self) -> dict:
        """Получить текущие настройки для сохранения"""
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
