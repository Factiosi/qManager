from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFormLayout, QDoubleSpinBox,
                              QGroupBox, QStyle)
from PySide6.QtCore import Qt

from src.pdf_splitter import split_pdf_by_green_pages, get_poppler_path
from src.core_worker import WorkerThread

from src.ui_areas_renamer import RenamerArea
from src.ui_areas_organizer import OrganizerArea

class SplitterArea(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        group = QGroupBox("PDF Splitter")
        form_layout = QFormLayout()

        # Выбор входного файла
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Выберите PDF файл...")
        self.input_field.setText(self.main_window.settings.get('splitter_input', ''))
        input_btn = QPushButton("Обзор")
        input_btn.setProperty("iconOnly", "true")
        input_btn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        input_btn.clicked.connect(
            lambda: self.main_window.browse_file(self.input_field, "PDF Files (*.pdf)"))
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(input_btn)
        form_layout.addRow("Входной файл:", input_layout)

        # Выбор выходной папки
        self.output_field = QLineEdit()
        self.output_field.setPlaceholderText("Выберите папку для сохранения...")
        self.output_field.setText(self.main_window.settings.get('splitter_output', ''))
        output_btn = QPushButton("Обзор")
        output_btn.setProperty("iconOnly", "true")
        output_btn.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        output_btn.clicked.connect(
            lambda: self.main_window.browse_directory(self.output_field))
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_field)
        output_layout.addWidget(output_btn)
        form_layout.addRow("Выходная папка:", output_layout)

        # Выбор порогового значения
        threshold_layout = QHBoxLayout()
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.1, 5.0)
        self.threshold_spin.setValue(self.main_window.settings.get('threshold', 2.3))
        self.threshold_spin.setSingleStep(0.1)
        self.threshold_spin.setButtonSymbols(QDoubleSpinBox.NoButtons)
        
        minus_btn = QPushButton("−")
        minus_btn.setProperty("small", "true")
        minus_btn.clicked.connect(
            lambda: self.threshold_spin.setValue(self.threshold_spin.value() - 0.1))
        
        plus_btn = QPushButton("+")
        plus_btn.setProperty("small", "true")
        plus_btn.clicked.connect(
            lambda: self.threshold_spin.setValue(self.threshold_spin.value() + 0.1))
        
        self.threshold_spin.setAlignment(Qt.AlignCenter)
        self.threshold_spin.setFixedWidth(80)
        self.threshold_spin.setStyleSheet("""
            QDoubleSpinBox {
                padding: 2px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QDoubleSpinBox:focus {
                border: 1px solid #2196F3;
            }
        """)
        
        threshold_layout.addWidget(minus_btn)
        threshold_layout.addWidget(self.threshold_spin)
        threshold_layout.addWidget(plus_btn)
        threshold_layout.addStretch()
        threshold_layout.setSpacing(4)
        form_layout.addRow("Порог:", threshold_layout)

        group.setLayout(form_layout)
        layout.addWidget(group)

        # Кнопка разделения
        self.split_btn = QPushButton("Разделить PDF")
        self.split_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.split_btn.clicked.connect(self.split_pdf)
        layout.addWidget(self.split_btn)
        self.main_window.start_buttons.append(self.split_btn)

        # Добавляем подсказки
        self.input_field.setToolTip("Выберите PDF файл для разделения")
        self.output_field.setToolTip("Выберите папку для сохранения разделенных файлов")
        self.threshold_spin.setToolTip("Пороговое значение для определения зеленых страниц")
        self.split_btn.setToolTip("Начать процесс разделения PDF файла")

    def split_pdf(self):
        """Начать процесс разделения PDF файла"""
        self.main_window.cleanup_worker()
        
        if not self.check_inputs():
            return
            
        input_path = self.input_field.text()
        output_dir = self.output_field.text()
        threshold = self.threshold_spin.value()
        
        def worker_function(log_callback, progress_callback):
            try:
                split_pdf_by_green_pages(
                    input_pdf=input_path,
                    output_dir=output_dir,
                    threshold=threshold,
                    poppler_path=get_poppler_path(),
                    log_callback=log_callback,
                    progress_callback=progress_callback
                )
            except Exception as e:
                log_callback(f"Ошибка при разделении PDF: {e}")
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
            self.main_window.log_message("Ошибка: Не выбран входной PDF файл")
            return False
            
        if not self.output_field.text():
            self.main_window.log_message("Ошибка: Не выбрана выходная папка")
            return False
            
        return True

    def get_settings(self) -> dict:
        """Получить текущие настройки для сохранения"""
        return {
            'splitter_input': self.input_field.text(),
            'splitter_output': self.output_field.text(),
            'threshold': self.threshold_spin.value()
        }
