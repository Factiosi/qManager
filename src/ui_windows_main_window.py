import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QFileDialog, QProgressBar,
    QTabWidget, QStyle
)
from PySide6.QtGui import QIcon

from src.core_settings import SettingsManager
from src.ui_styles import get_stylesheet, DARK_MODE
from src.ui_areas_splitter import SplitterArea
from src.ui_areas_renamer import RenamerArea
from src.ui_areas_organizer import OrganizerArea

def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, relative_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("qManager")
        self.setMinimumSize(800, 600)
        self.worker = None
        
        # Set application icon
        icon_path = get_resource_path("resources/Icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Initialize settings manager
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load_settings()
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Store start buttons references
        self.start_buttons = []
        
        # Create tabs
        self.tabs = QTabWidget()
        self.splitter_area = SplitterArea(self)
        self.renamer_area = RenamerArea(self)
        self.organizer_area = OrganizerArea(self)
        
        self.tabs.addTab(self.splitter_area, "Разделение")
        self.tabs.addTab(self.renamer_area, "Переименование")
        self.tabs.addTab(self.organizer_area, "Организация")
        layout.addWidget(self.tabs)

        # Stop button
        self.stop_btn = QPushButton("Стоп")
        self.stop_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("background-color: #cccccc; color: #666666;")
        self.stop_btn.clicked.connect(self.stop_worker)
        layout.addWidget(self.stop_btn)

        # Create progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Apply styles
        self.apply_styles()

    def apply_styles(self):
        """Применяет стиль к интерфейсу"""
        self.setStyleSheet(get_stylesheet(DARK_MODE))

    def set_worker_state(self, running: bool):
        """Управляет состоянием кнопок во время выполнения задачи"""
        if running:
            self.stop_btn.setEnabled(True)
            self.stop_btn.setStyleSheet("background-color: #0d6efd; color: white;")
            for btn in self.start_buttons:
                btn.setEnabled(False)
                btn.setStyleSheet("background-color: #cccccc; color: #666666;")
        else:
            self.stop_btn.setEnabled(False)
            self.stop_btn.setStyleSheet("background-color: #cccccc; color: #666666;")
            for btn in self.start_buttons:
                btn.setEnabled(True)
                btn.setStyleSheet("background-color: #0d6efd; color: white;")

    def cleanup_worker(self):
        """Очищает текущий рабочий поток, если он существует"""
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
            self.worker = None

    def stop_worker(self):
        """Останавливает текущий рабочий поток"""
        if self.worker and self.worker.isRunning():
            print("Остановка текущей операции...")
            self.worker.terminate()
            self.worker.wait()
            self.worker = None
            print("Операция остановлена.")
        self.set_worker_state(False)

    def log_message(self, message: str):
        """Логирует сообщение и сохраняет текущие настройки"""
        print(message)
        
        # Обновляем настройки из всех областей
        self.settings.update(self.splitter_area.get_settings())
        self.settings.update(self.renamer_area.get_settings())
        self.settings.update(self.organizer_area.get_settings())
        
        # Сохраняем обновленные настройки
        self.settings_manager.save_settings(self.settings)

    def update_progress(self, current, total):
        """Обновляет прогресс-бар"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat("Файл %v из %m")

    def browse_file(self, input_field, file_filter="All Files (*)"):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", file_filter)
        if file_path:
            input_field.setText(file_path)

    def browse_directory(self, output_field):
        directory = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if directory:
            output_field.setText(directory)