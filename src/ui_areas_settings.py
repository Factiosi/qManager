from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QComboBox, 
    QGroupBox, QFormLayout, 
    QLabel
)
from PySide6.QtCore import Qt
from src.ui_styles import toggle_dark_mode
from src.ui_widgets_checkbox import CustomCheckBox

class SettingsArea(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
        )
        main_layout.setSpacing(self.main_window.MARGIN_NORMAL)

        
        settings_group = QGroupBox("Настройки")
        form = QFormLayout()
        form.setContentsMargins(
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
        )
        form.setVerticalSpacing(self.main_window.MARGIN_NORMAL)

        
        self.excel_mode_combo = QComboBox()
        self.excel_mode_combo.addItems(["Отчёт", "Logos"])
        current_mode = "Logos" if self.main_window.settings.get('excel_mode') == 'logos' else "Отчёт"
        self.excel_mode_combo.setCurrentText(current_mode)
        self.excel_mode_combo.currentTextChanged.connect(self.on_excel_mode_changed)
        form.addRow("Режим Excel:", self.excel_mode_combo)

        
        self.dark_mode = CustomCheckBox()
        self.dark_mode.setChecked(self.main_window.settings.get('dark_mode', False))
        self.dark_mode.stateChanged.connect(self.on_dark_mode_changed)
        form.addRow("Тёмная тема:", self.dark_mode)

        
        self.debug_mode = CustomCheckBox()
        self.debug_mode.setChecked(self.main_window.settings.get('debug_mode', False))
        self.debug_mode.stateChanged.connect(self.on_debug_mode_changed)
        form.addRow("Режим отладки:", self.debug_mode)

        settings_group.setLayout(form)
        main_layout.addWidget(settings_group)
        main_layout.addStretch()
    
    def on_excel_mode_changed(self, text):
        """Обработчик изменения режима Excel"""
        mode = 'logos' if text == "Logos" else 'report'
        self.main_window.settings['excel_mode'] = mode
        self.main_window.settings_manager.save_settings(self.main_window.settings)
        
    def on_dark_mode_changed(self, state):
        """Обработчик изменения темы интерфейса"""
        self.main_window.settings['dark_mode'] = bool(state)
        self.main_window.settings_manager.save_settings(self.main_window.settings)
        toggle_dark_mode()
        self.main_window.apply_styles()
        
    def on_debug_mode_changed(self, state):
        """Обработчик изменения режима отладки"""
        is_debug = bool(state)
        self.main_window.settings['debug_mode'] = is_debug
        self.main_window.settings_manager.save_settings(self.main_window.settings)
        self.main_window.debug_mode = is_debug

    # Инспектор UI удалён

    # ===== Сохранение настроек =====
    def save_settings(self):
        """Сохраняет текущие настройки"""
        try:
            if hasattr(self.main_window, 'settings_manager'):
                self.main_window.settings_manager.save_settings(self.main_window.settings)
        except Exception:
            pass

    def get_settings(self) -> dict:
        mode = 'logos' if self.excel_mode_combo.currentText() == 'Logos' else 'report'
        return {
            'excel_mode': mode,
            'dark_mode': bool(self.dark_mode.isChecked()),
            'debug_mode': bool(self.debug_mode.isChecked()),
        }
