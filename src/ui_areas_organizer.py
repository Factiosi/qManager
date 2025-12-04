from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QGroupBox, QStyle
)

from src.pdf_organizer import organize_pdfs
from src.core_worker import WorkerThread

class OrganizerArea(QWidget):
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
        
        self.input_field.setToolTip("Выберите папку с PDF файлами для организации")
        self.output_field.setToolTip("Выберите папку для сохранения организованных файлов")
    
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

    def organize_pdf(self):
        """Начать процесс организации"""
        if not self.check_inputs():
            return
            
        input_folder = self.input_field.text()
        output_folder = self.output_field.text()
        excel_mode = self.main_window.settings.get('excel_mode', 'logos')
        merge_mode = self.main_window.settings.get('merge_mode', 'order')
        
        # Получаем настройки фильтрации
        filter_mode = self.main_window.settings.get('filter_mode', 'unlimited')
        filter_date_from_str = self.main_window.settings.get('filter_date_from')
        filter_date_to_str = self.main_window.settings.get('filter_date_to')
        
        # Преобразуем строки дат в datetime объекты
        filter_date_from = None
        filter_date_to = None
        if filter_mode == 'period':
            from datetime import datetime
            if filter_date_from_str:
                try:
                    filter_date_from = datetime.strptime(filter_date_from_str, "%Y-%m-%d")
                except:
                    filter_date_from = None
            if filter_date_to_str:
                try:
                    filter_date_to = datetime.strptime(filter_date_to_str, "%Y-%m-%d")
                except:
                    filter_date_to = None
        
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
            organize_pdfs,
            input_folder,
            output_folder,
            excel_path,
            mode=excel_mode,
            merge_mode=merge_mode,
            filter_mode=filter_mode,
            filter_date_from=filter_date_from,
            filter_date_to=filter_date_to
        )
        # Подключаем сигналы
        self.main_window.worker.progress_signal.connect(self.main_window.update_progress)
        self.main_window.worker.message_signal.connect(self.main_window.log_message)
        self.main_window.worker.error_signal.connect(self.main_window.log_message)
        self.main_window.worker.finished.connect(lambda: self.main_window.set_worker_state(False))
        # Сбрасываем прогресс-бар при завершении
        self.main_window.worker.finished.connect(lambda: self.main_window.progress_bar.setValue(0))
        # Сбрасываем прогресс-бар при ошибке
        self.main_window.worker.error_signal.connect(lambda: self.main_window.progress_bar.setValue(0))
        
        # Запускаем
        self.main_window.set_worker_state(True)
        self.main_window.worker.start()
        
        # Сохраняем настройки
        self.main_window.settings.update(self.get_settings())

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
