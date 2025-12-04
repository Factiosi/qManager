from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QComboBox, 
    QGroupBox, QFormLayout, 
    QLabel, QDateEdit, QAbstractSpinBox
)
from PySide6.QtCore import Qt, QDate
from datetime import datetime
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

        # === Группа: Основные ===
        main_group = QGroupBox("Основные")
        main_form = QFormLayout()
        main_form.setContentsMargins(
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
        )
        self.dark_mode = CustomCheckBox()
        self.dark_mode.setChecked(self.main_window.settings.get('dark_mode', False))
        self.dark_mode.stateChanged.connect(self.on_dark_mode_changed)
        main_form.addRow("Тёмная тема:", self.dark_mode)
        self.debug_mode = CustomCheckBox()
        self.debug_mode.setChecked(self.main_window.settings.get('debug_mode', False))
        self.debug_mode.stateChanged.connect(self.on_debug_mode_changed)
        main_form.addRow("Режим отладки:", self.debug_mode)
        main_group.setLayout(main_form)
        
        # === Группа: Параметры менеджера ===
        manager_group = QGroupBox("Параметры менеджера")
        manager_form = QFormLayout()
        manager_form.setContentsMargins(
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
        )
        # Режим таблиц
        self.excel_mode_combo = QComboBox()
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
        # Режим объединения
        self.merge_mode_combo = QComboBox()
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
        
        # Обновляем доступность режима объединения в зависимости от режима таблиц
        self.update_merge_mode_availability()
        manager_group.setLayout(manager_form)
        
        # === Группа: Принцип фильтрации данных ===
        filter_group = QGroupBox("Принцип фильтрации данных")
        filter_form = QFormLayout()
        filter_form.setContentsMargins(
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
            self.main_window.MARGIN_NORMAL,
        )
        
        self.filter_mode_combo = QComboBox()
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
        
        # Поля дат
        self.filter_date_from = QDateEdit()
        self.filter_date_from.setCalendarPopup(False)  # Отключаем календарь
        self.filter_date_from.setButtonSymbols(QAbstractSpinBox.NoButtons)  # Скрываем кнопки
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
        self.filter_date_to.setCalendarPopup(False)  # Отключаем календарь
        self.filter_date_to.setButtonSymbols(QAbstractSpinBox.NoButtons)  # Скрываем кнопки
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
        
        # Добавляем группы в основной лэйаут
        main_layout.addWidget(main_group)
        main_layout.addWidget(manager_group)
        main_layout.addWidget(filter_group)
        
        # Обновляем видимость полей дат
        self.update_date_fields_visibility()
        main_layout.addStretch()
    
    def on_excel_mode_changed(self, text):
        """Обработчик изменения режима таблиц"""
        if text == "Google Sheets":
            mode = 'sheets'
            # Для Google Sheets всегда используем объединение по коносаменту
            self.main_window.settings['merge_mode'] = 'bl'
            self.merge_mode_combo.setCurrentText("Объединение по номеру коносамента")
        elif text == "Отчёт":
            mode = 'report'
        else:
            mode = 'logos'
        
        self.main_window.settings['excel_mode'] = mode
        self.main_window.settings_manager.save_settings(self.main_window.settings)
        
        # Обновляем доступность режима объединения
        self.update_merge_mode_availability()
    
    def update_merge_mode_availability(self):
        """Обновляет доступность комбобокса режима объединения"""
        current_mode = self.excel_mode_combo.currentText()
        if current_mode == "Google Sheets":
            # Для Google Sheets отключаем объединение по заказу
            self.merge_mode_combo.setEnabled(False)
            self.merge_mode_combo.setToolTip("Для Google Sheets доступно только объединение по коносаменту")
        else:
            self.merge_mode_combo.setEnabled(True)
            self.merge_mode_combo.setToolTip("")
        
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

    def on_merge_mode_changed(self, text: str):
        """Обработчик изменения режима объединения"""
        self.main_window.settings['merge_mode'] = 'bl' if 'коносамента' in text else 'order'
        self.main_window.settings_manager.save_settings(self.main_window.settings)
    
    def on_filter_mode_changed(self, text: str):
        """Обработчик изменения принципа фильтрации"""
        mode = 'period' if text == "За период" else 'unlimited'
        self.main_window.settings['filter_mode'] = mode
        self.main_window.settings_manager.save_settings(self.main_window.settings)
        self.update_date_fields_visibility()
    
    def update_date_fields_visibility(self):
        """Обновляет видимость полей дат в зависимости от выбранного режима"""
        is_period = self.filter_mode_combo.currentText() == "За период"
        # Находим родительскую группу через layout
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, QGroupBox) and widget.title() == "Принцип фильтрации данных":
                    form_layout = widget.layout()
                    if isinstance(form_layout, QFormLayout):
                        # Находим строки с датами и скрываем/показываем их
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
        """Обработчик изменения даты начала периода"""
        date_str = date.toString("yyyy-MM-dd")
        self.main_window.settings['filter_date_from'] = date_str
        self.main_window.settings_manager.save_settings(self.main_window.settings)
    
    def on_filter_date_to_changed(self, date: QDate):
        """Обработчик изменения даты конца периода"""
        date_str = date.toString("yyyy-MM-dd")
        self.main_window.settings['filter_date_to'] = date_str
        self.main_window.settings_manager.save_settings(self.main_window.settings)

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
        }
