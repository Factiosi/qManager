import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QComboBox,
    QGroupBox, QFormLayout,
    QLabel, QDateEdit, QAbstractSpinBox, QPushButton, QApplication
)
from PySide6.QtCore import Qt, QDate
from datetime import datetime
from src.ui_styles import toggle_dark_mode
from src.ui_widgets_checkbox import CustomCheckBox
from src.updater import VERSION, PRERELEASE
from src.utils_common import configure_debug_logging

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

        main_group = QGroupBox("Основные")
        main_form = QFormLayout()
        main_form.setContentsMargins(
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
        )
        main_form.setVerticalSpacing(18)
        main_form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.dark_mode = CustomCheckBox()
        self.dark_mode.setChecked(self.main_window.settings.get('dark_mode', False))
        self.dark_mode.stateChanged.connect(self.on_dark_mode_changed)
        main_form.addRow("Тёмная тема:", self.dark_mode)
        self.debug_mode = CustomCheckBox()
        self.debug_mode.setChecked(self.main_window.settings.get('debug_mode', False))
        self.debug_mode.stateChanged.connect(self.on_debug_mode_changed)
        main_form.addRow("Режим отладки:", self.debug_mode)
        self.auto_run_renamer = CustomCheckBox()
        self.auto_run_renamer.setChecked(self.main_window.settings.get('auto_run_renamer', False))
        self.auto_run_renamer.stateChanged.connect(self.on_auto_run_renamer_changed)
        main_form.addRow("Автоматически запускать переименование:", self.auto_run_renamer)
        
        self.ocr_binarization = CustomCheckBox()
        self.ocr_binarization.setChecked(self.main_window.settings.get('ocr_binarization', False))
        self.ocr_binarization.stateChanged.connect(self.on_ocr_binarization_changed)
        self.ocr_binarization.setToolTip(
            "Применять бинаризацию только если обычный OCR не распознал контейнер. "
            "Два прохода: стандартный (127) и второй (80)."
        )
        main_form.addRow("Бинаризация (при неудаче):", self.ocr_binarization)
        
        main_group.setLayout(main_form)
        
        manager_group = QGroupBox("Параметры менеджера")
        manager_form = QFormLayout()
        manager_form.setContentsMargins(
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
        )
        manager_form.setVerticalSpacing(6)
        manager_form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.excel_mode_combo = QComboBox()
        self.excel_mode_combo.setFixedHeight(self.main_window.BUTTON_HEIGHT)
        self.excel_mode_combo.addItems(["Отчёт", "Logos", "Google Sheets"])
        excel_mode_value = self.main_window.settings.get('excel_mode', 'logos')
        if excel_mode_value == 'sheets':
            current_mode = "Google Sheets"
        elif excel_mode_value == 'report':
            current_mode = "Отчёт"
        else:
            current_mode = "Logos"
        self.excel_mode_combo.setCurrentText(current_mode)
        self.excel_mode_combo.currentTextChanged.connect(self.on_excel_mode_changed)
        manager_form.addRow("Режим таблиц:", self.excel_mode_combo)
        self.merge_mode_combo = QComboBox()
        self.merge_mode_combo.setFixedHeight(self.main_window.BUTTON_HEIGHT)
        self.merge_mode_combo.addItems([
            "Объединение по номеру заказа",
            "Объединение по номеру коносамента",
        ])
        merge_mode_value = self.main_window.settings.get('merge_mode', 'order')
        self.merge_mode_combo.setCurrentText(
            "Объединение по номеру коносамента" if merge_mode_value == 'bl' else "Объединение по номеру заказа"
        )
        self.merge_mode_combo.currentTextChanged.connect(self.on_merge_mode_changed)
        manager_form.addRow("Режим объединения:", self.merge_mode_combo)
        
        self.update_merge_mode_availability()
        manager_group.setLayout(manager_form)

        filter_group = QGroupBox("Принцип фильтрации данных")
        filter_form = QFormLayout()
        filter_form.setContentsMargins(
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
        )
        filter_form.setVerticalSpacing(6)
        filter_form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.filter_mode_combo = QComboBox()
        self.filter_mode_combo.setFixedHeight(self.main_window.BUTTON_HEIGHT)
        self.filter_mode_combo.addItems([
            "От новых к старым (неограниченно)",
            "За период"
        ])
        filter_mode_value = self.main_window.settings.get('filter_mode', 'unlimited')
        self.filter_mode_combo.setCurrentText(
            "За период" if filter_mode_value == 'period' else "От новых к старым (неограниченно)"
        )
        self.filter_mode_combo.currentTextChanged.connect(self.on_filter_mode_changed)
        filter_form.addRow("Принцип фильтрации данных:", self.filter_mode_combo)
        
        self.filter_date_from = QDateEdit()
        self.filter_date_from.setCalendarPopup(False)
        self.filter_date_from.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.filter_date_from.setDisplayFormat("dd.MM.yyyy")
        self.filter_date_from.setFixedHeight(self.main_window.BUTTON_HEIGHT)
        date_from_str = self.main_window.settings.get('filter_date_from')
        if date_from_str:
            try:
                date_from = datetime.strptime(date_from_str, "%Y-%m-%d").date()
                self.filter_date_from.setDate(QDate(date_from.year, date_from.month, date_from.day))
            except:
                self.filter_date_from.setDate(QDate.currentDate())
        else:
            self.filter_date_from.setDate(QDate.currentDate())
        self.filter_date_from.dateChanged.connect(self.on_filter_date_from_changed)
        filter_form.addRow("Период от:", self.filter_date_from)
        
        self.filter_date_to = QDateEdit()
        self.filter_date_to.setCalendarPopup(False)
        self.filter_date_to.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.filter_date_to.setDisplayFormat("dd.MM.yyyy")
        self.filter_date_to.setFixedHeight(self.main_window.BUTTON_HEIGHT)
        date_to_str = self.main_window.settings.get('filter_date_to')
        if date_to_str:
            try:
                date_to = datetime.strptime(date_to_str, "%Y-%m-%d").date()
                self.filter_date_to.setDate(QDate(date_to.year, date_to.month, date_to.day))
            except:
                self.filter_date_to.setDate(QDate.currentDate())
        else:
            self.filter_date_to.setDate(QDate.currentDate())
        self.filter_date_to.dateChanged.connect(self.on_filter_date_to_changed)
        filter_form.addRow("Период до:", self.filter_date_to)
        
        filter_group.setLayout(filter_form)
        
        update_group = QGroupBox("Обновления")
        update_layout = QVBoxLayout()
        update_layout.setContentsMargins(
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
        )
        update_layout.setSpacing(self.main_window.MARGIN_SMALL)
        self._installer_path: str | None = None

        update_layout.addWidget(QLabel(f"Текущая версия: {VERSION}"))

        if PRERELEASE:
            notice = QLabel("Данная версия приложения не поддерживает обновления")
            notice.setWordWrap(True)
            update_layout.addWidget(notice)
            self._update_status = None
            self._check_btn = None
            self._install_btn = None
        else:
            self._update_status = QLabel("Проверка обновлений...")

            self._check_btn = QPushButton("Проверить обновления")
            self._check_btn.setFixedHeight(self.main_window.BUTTON_HEIGHT)
            self._check_btn.setProperty("secondary", "true")
            self._check_btn.clicked.connect(self._on_manual_check)

            self._install_btn = QPushButton("Установить обновление")
            self._install_btn.setFixedHeight(self.main_window.BUTTON_HEIGHT)
            self._install_btn.hide()
            self._install_btn.clicked.connect(self._install_update)

            update_layout.addWidget(self._update_status)
            update_layout.addWidget(self._check_btn)
            update_layout.addWidget(self._install_btn)

        update_group.setLayout(update_layout)

        main_layout.addWidget(main_group)
        main_layout.addWidget(manager_group)
        main_layout.addWidget(filter_group)
        main_layout.addWidget(update_group)

        self.update_date_fields_visibility()
        main_layout.addStretch()
    
    def on_excel_mode_changed(self, text):
        if text == "Google Sheets":
            mode = 'sheets'
            # Google Sheets поддерживает только объединение по коносаменту
            self.main_window.settings['merge_mode'] = 'bl'
            self.merge_mode_combo.setCurrentText("Объединение по номеру коносамента")
        elif text == "Отчёт":
            mode = 'report'
        else:
            mode = 'logos'
        
        self.main_window.settings['excel_mode'] = mode
        self.main_window.settings_manager.save_settings(self.main_window.settings)
        self.update_merge_mode_availability()
    
    def update_merge_mode_availability(self):
        current_mode = self.excel_mode_combo.currentText()
        if current_mode == "Google Sheets":
            self.merge_mode_combo.setEnabled(False)
            self.merge_mode_combo.setToolTip("Для Google Sheets доступно только объединение по коносаменту")
        else:
            self.merge_mode_combo.setEnabled(True)
            self.merge_mode_combo.setToolTip("")
        
    def on_dark_mode_changed(self, state):
        self.main_window.settings['dark_mode'] = bool(state)
        self.main_window.settings_manager.save_settings(self.main_window.settings)
        toggle_dark_mode()
        self.main_window.apply_styles()
        
    def on_debug_mode_changed(self, state):
        is_debug = bool(state)
        self.main_window.settings['debug_mode'] = is_debug
        self.main_window.settings_manager.save_settings(self.main_window.settings)
        self.main_window.debug_mode = is_debug
        configure_debug_logging(is_debug)
    
    def on_auto_run_renamer_changed(self, state):
        self.main_window.settings['auto_run_renamer'] = bool(state)
        self.main_window.settings_manager.save_settings(self.main_window.settings)

    def on_ocr_binarization_changed(self, state):
        self.main_window.settings['ocr_binarization'] = bool(state)
        self.main_window.settings_manager.save_settings(self.main_window.settings)

    def on_merge_mode_changed(self, text: str):
        self.main_window.settings['merge_mode'] = 'bl' if 'коносамента' in text else 'order'
        self.main_window.settings_manager.save_settings(self.main_window.settings)
    
    def on_filter_mode_changed(self, text: str):
        mode = 'period' if text == "За период" else 'unlimited'
        self.main_window.settings['filter_mode'] = mode
        self.main_window.settings_manager.save_settings(self.main_window.settings)
        self.update_date_fields_visibility()
    
    def update_date_fields_visibility(self):
        is_period = self.filter_mode_combo.currentText() == "За период"
        # QFormLayout не даёт прямого доступа к строкам — обходим через layout-дерево
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, QGroupBox) and widget.title() == "Принцип фильтрации данных":
                    form_layout = widget.layout()
                    if isinstance(form_layout, QFormLayout):
                        for j in range(form_layout.rowCount()):
                            label_item = form_layout.itemAt(j, QFormLayout.LabelRole)
                            field_item = form_layout.itemAt(j, QFormLayout.FieldRole)
                            if label_item and field_item:
                                label = label_item.widget()
                                field = field_item.widget()
                                if label and field and (field == self.filter_date_from or field == self.filter_date_to):
                                    label.setVisible(is_period)
                                    field.setVisible(is_period)
                    break
    
    def on_filter_date_from_changed(self, date: QDate):
        date_str = date.toString("yyyy-MM-dd")
        self.main_window.settings['filter_date_from'] = date_str
        self.main_window.settings_manager.save_settings(self.main_window.settings)
    
    def on_filter_date_to_changed(self, date: QDate):
        date_str = date.toString("yyyy-MM-dd")
        self.main_window.settings['filter_date_to'] = date_str
        self.main_window.settings_manager.save_settings(self.main_window.settings)

    def save_settings(self):
        try:
            if hasattr(self.main_window, 'settings_manager'):
                self.main_window.settings_manager.save_settings(self.main_window.settings)
        except Exception:
            pass

    def _on_manual_check(self):
        self._update_status.setText("Проверка обновлений...")
        self._install_btn.hide()
        self._installer_path = None
        self.main_window._start_update_check()

    def set_update_status(self, text: str) -> None:
        if self._update_status:
            self._update_status.setText(text)

    def show_install_button(self, path: str) -> None:
        if not self._install_btn:
            return
        self._installer_path = path
        self._update_status.setText("Готово к установке")
        self._install_btn.show()

    def _install_update(self) -> None:
        if self._installer_path and os.path.exists(self._installer_path):
            os.startfile(self._installer_path)
            QApplication.quit()

    def get_settings(self) -> dict:
        text = self.excel_mode_combo.currentText()
        if text == "Google Sheets":
            mode = 'sheets'
        elif text == "Отчёт":
            mode = 'report'
        else:
            mode = 'logos'
        
        filter_mode_text = self.filter_mode_combo.currentText()
        filter_mode = 'period' if filter_mode_text == "За период" else 'unlimited'
        
        return {
            'excel_mode': mode,
            'dark_mode': bool(self.dark_mode.isChecked()),
            'debug_mode': bool(self.debug_mode.isChecked()),
            'merge_mode': ('bl' if 'коносамента' in self.merge_mode_combo.currentText() else 'order'),
            'filter_mode': filter_mode,
            'filter_date_from': self.filter_date_from.date().toString("yyyy-MM-dd"),
            'filter_date_to': self.filter_date_to.date().toString("yyyy-MM-dd"),
            'auto_run_renamer': bool(self.auto_run_renamer.isChecked()),
            'ocr_binarization': bool(self.ocr_binarization.isChecked()),
        }
