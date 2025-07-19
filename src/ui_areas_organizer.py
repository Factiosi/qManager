from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QLineEdit, QPushButton, QFormLayout,
                              QGroupBox, QStyle, QComboBox)

from src.pdf_organizer import organize_pdfs
from src.core_worker import WorkerThread

class OrganizerArea(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # --- QComboBox для выбора режима Excel ---
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Logos", "Отчёт"])
        self.mode_combo.setObjectName("excelModeCombo")
        try:
            from src.ui_styles import COMBO_BOX_STYLE
            self.mode_combo.setStyleSheet(COMBO_BOX_STYLE)
        except Exception:
            pass
        mode_val = self.main_window.settings.get('excel_mode', 'logos')
        self.mode_combo.setCurrentIndex(0 if mode_val == 'logos' else 1)
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        layout.addWidget(self.mode_combo)

        group = QGroupBox("PDF Organizer")
        form_layout = QFormLayout()

        # Выбор входной папки
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Выберите входную папку...")
        self.input_field.setText(self.main_window.settings.get('organizer_input', ''))
        input_btn = QPushButton("Обзор")
        input_btn.setProperty("iconOnly", "true")
        input_btn.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        input_btn.clicked.connect(
            lambda: self.main_window.browse_directory(self.input_field))
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(input_btn)
        form_layout.addRow("Входная папка:", input_layout)

        # Выбор выходной папки
        self.output_field = QLineEdit()
        self.output_field.setPlaceholderText("Выберите папку для сохранения...")
        self.output_field.setText(self.main_window.settings.get('organizer_output', ''))
        output_btn = QPushButton("Обзор")
        output_btn.setProperty("iconOnly", "true")
        output_btn.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        output_btn.clicked.connect(
            lambda: self.main_window.browse_directory(self.output_field))
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_field)
        output_layout.addWidget(output_btn)
        form_layout.addRow("Выходная папка:", output_layout)

        # Выбор Excel файла для организатора
        self.excel_container = QWidget()
        excel_layout = QHBoxLayout(self.excel_container)
        excel_layout.setContentsMargins(0, 0, 0, 0)
        self.excel_field = QLineEdit()
        self.excel_field.setPlaceholderText("Выберите Excel файл...")
        self.excel_field.setText(self.main_window.settings.get('organizer_excel_file', ''))
        excel_btn = QPushButton("Обзор")
        excel_btn.setProperty("iconOnly", "true")
        excel_btn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        excel_btn.clicked.connect(
            lambda: self.main_window.browse_file(self.excel_field, "Excel Files (*.xlsx *.xls)"))
        excel_layout.addWidget(self.excel_field)
        excel_layout.addWidget(excel_btn)
        form_layout.addRow("Excel файл:", self.excel_container)
        self.excel_container.setVisible(True)

        group.setLayout(form_layout)
        layout.addWidget(group)

        # Кнопка организации
        self.organize_btn = QPushButton("Организовать PDF")
        self.organize_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.organize_btn.clicked.connect(self.organize_pdf)
        layout.addWidget(self.organize_btn)
        self.main_window.start_buttons.append(self.organize_btn)

        # Добавляем подсказки        self.input_field.setToolTip("Выберите папку с PDF файлами для организации")
        self.output_field.setToolTip("Выберите папку для сохранения организованных файлов")
        self.organize_btn.setToolTip("Начать процесс организации PDF файлов")

    def on_mode_changed(self, idx):
        mode = 'logos' if idx == 0 else 'report'
        self.main_window.settings['excel_mode'] = mode
        self.main_window.settings_manager.save_settings(self.main_window.settings)

    def get_excel_mode(self):
        idx = self.mode_combo.currentIndex()
        return 'logos' if idx == 0 else 'report'

    def organize_pdf(self):
        """
        Начать процесс организации PDF файлов
        """
        self.main_window.cleanup_worker()
        
        if not self.check_inputs():
            return
            
        input_folder = self.input_field.text()
        output_folder = self.output_field.text()
        excel_path = self.excel_field.text()
        excel_mode = self.get_excel_mode()
        
        def worker_function(log_callback, progress_callback):
            try:
                from src.utils_data_manager import DataManager
                data_manager = DataManager(mode=excel_mode)
                data_manager.load_excel_data(excel_path)
                # Передайте data_manager дальше по логике, если требуется
                organize_pdfs(
                    input_folder,
                    output_folder,
                    excel_path,
                    log_callback,
                    progress_callback,
                    excel_mode=excel_mode
                )
            except Exception as e:
                log_callback(f"Ошибка при организации PDF: {e}")
                raise
        self.main_window.worker = WorkerThread(worker_function)
        self.main_window.worker.finished.connect(
            lambda: self.main_window.set_worker_state(False))
        self.main_window.worker.progress.connect(self.main_window.update_progress)
        self.main_window.worker.log.connect(self.main_window.log_message)
        self.main_window.worker.error.connect(self.main_window.log_message)
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
            
        if not self.excel_field.text():
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
