"""Модуль стилей для интерфейса"""

# Глобальные настройки темы
DARK_MODE = False

def get_colors():
    """Возвращает текущую цветовую схему"""
    return DARK_COLORS if DARK_MODE else LIGHT_COLORS

def toggle_dark_mode():
    """Переключает темную тему"""
    global DARK_MODE
    DARK_MODE = not DARK_MODE
    return DARK_MODE

# Определение цветовых схем для светлой и темной тем
LIGHT_COLORS = {
    "bg_color": "#F5F6F8",
    "widget_bg": "#FFFFFF",
    "text_color": "#1F2937",
    "border_color": "#D1D5DB",
    "accent_color": "#1D9BF0",
    "accent_color_hover": "#187CC0",

    "error_color": "#DC2626",
    "success_color": "#16A34A",
    "warning_color": "#F59E0B",
    "disabled_bg": "#EEF0F3",
    "disabled_text": "#9CA3AF",

    "tab_active_bg": "#E6F0FA",
    "tab_active_border": "#1D9BF0",
    "tab_inactive_bg": "#FFFFFF",
    "tab_inactive_hover_bg": "#E9EEF5",

    "menu_bg": "#FFFFFF",
    "menu_text": "#1F2937",
    "menu_hover_bg": "#EEF2F7",

    "statusbar_bg": "#F5F6F8",
    "scrollbar_bg": "#F0F2F5",
    "scrollbar_handle": "#C7CDD6",
    "shadow_color": "#00000022",
    "console_bg": "#F9FAFB",
    "console_text": "#111827",
    "console_system": "#6B7280",
    "console_error": "#DC2626",
    "console_warn": "#D97706",
    "console_success": "#15803D"
}

DARK_COLORS = {
    "bg_color": "#1E1E2E",
    "widget_bg": "#2A2A3C",
    "text_color": "#F9FAFB",
    "border_color": "#3B3B4F",
    "accent_color": "#3B82F6",
    "accent_color_hover": "#2563EB",

    "error_color": "#F87171",
    "success_color": "#34D399",
    "warning_color": "#FBBF24",
    "disabled_bg": "#333345",
    "disabled_text": "#9CA3AF",

    "tab_active_bg": "#273849",
    "tab_active_border": "#3B82F6",
    "tab_inactive_bg": "#2A2A3C",
    "tab_inactive_hover_bg": "#323248",

    "menu_bg": "#2A2A3C",
    "menu_text": "#F9FAFB",
    "menu_hover_bg": "#33334A",

    "statusbar_bg": "#2A2A3C",
    "scrollbar_bg": "#26263A",
    "scrollbar_handle": "#3F3F56",
    "shadow_color": "#00000066",
    "console_bg": "#1E1E1E",
    "console_text": "#D1D5DB",
    "console_system": "#9CA3AF",
    "console_error": "#F87171",
    "console_warn": "#FBBF24",
    "console_success": "#4ADE80"
}

# Параметры стиля
BORDER_RADIUS = "4px"
LARGE_BORDER_RADIUS = "8px"
PADDING = "8px"
MARGIN = "8px"

def get_stylesheet(dark_mode=False):
    """Возвращает таблицу стилей для приложения"""
    global DARK_MODE
    DARK_MODE = dark_mode
    colors = get_colors()
    
    return f"""
    /* Главное окно */
    QMainWindow {{
        background-color: {colors['bg_color']};
        color: {colors['text_color']};
    }}
    
    /* Меню */
    QMenuBar {{
        background-color: {colors['menu_bg']};
        color: {colors['menu_text']};
        border-bottom: 1px solid {colors['border_color']};
    }}
    
    QMenuBar::item:selected {{
        background-color: {colors['menu_hover_bg']};
    }}
    
    QMenu {{
        background-color: {colors['menu_bg']};
        color: {colors['menu_text']};
        border: 1px solid {colors['border_color']};
    }}
    
    QMenu::item:selected {{
        background-color: {colors['menu_hover_bg']};
    }}
    
    /* Вкладки */
    QTabWidget::pane {{
        border: 1px solid {colors['border_color']};
        background-color: {colors['widget_bg']};
        border-radius: {BORDER_RADIUS};
        padding-top: 0;
    }}
    
    QTabBar::tab {{
        background-color: {colors['tab_inactive_bg']};
        color: {colors['text_color']};
        padding: 8px 16px;
        border: 1px solid {colors['border_color']};
        border-bottom: none;
        border-top-left-radius: {BORDER_RADIUS};
        border-top-right-radius: {BORDER_RADIUS};
        margin: 0 2px 0 0;
    }}
    
    QTabBar::tab:selected {{
        background-color: {colors['tab_active_bg']};
        border-bottom: 2px solid {colors['tab_active_border']};
        margin-bottom: 0;
    }}
    
    QTabBar::tab:hover:!selected {{
        background-color: {colors['tab_inactive_hover_bg']};
    }}
    
    /* Кнопки */
    QPushButton {{
        background-color: {colors['accent_color']};
        color: white;
        border: none;
        border-radius: {BORDER_RADIUS};
        padding: 4px;
        font-weight: 600;
        text-align: center;
        spacing: 4px;
    }}
    
    QPushButton:hover {{
        background-color: {colors['accent_color_hover']};
    }}
    
    QPushButton:pressed {{
        background-color: {colors['accent_color_hover']};
        margin: 1px 0 0 1px;
    }}
    
    QPushButton[iconOnly="true"] {{
        padding: 0px;
    }}
    
    QPushButton:disabled {{
        background-color: {colors['disabled_bg']};
        color: {colors['disabled_text']};
    }}
    
    QPushButton[small="true"] {{
        padding: 4px 8px;
        font-size: 12px;
    }}
    
    /* Поля ввода */
    QLineEdit {{
        background-color: {colors['widget_bg']};
        color: {colors['text_color']};
        border: 1px solid {colors['border_color']};
        border-radius: {BORDER_RADIUS};
        padding: 3px {PADDING};
    }}
    
    QLineEdit:focus {{
        border: 1px solid {colors['accent_color']};
    }}
    
    QLineEdit:disabled {{
        background-color: {colors['disabled_bg']};
        color: {colors['disabled_text']};
    }}
    
    /* Поля выбора даты */
    QDateEdit {{
        background-color: {colors['widget_bg']};
        color: {colors['text_color']};
        border: 1px solid {colors['border_color']};
        border-radius: {BORDER_RADIUS};
        padding: 3px {PADDING};
    }}
    
    QDateEdit:hover {{
        border: 1px solid {colors['accent_color']};
    }}
    
    QDateEdit:focus {{
        border: 1px solid {colors['accent_color']};
    }}
    
    QDateEdit:disabled {{
        background-color: {colors['disabled_bg']};
        color: {colors['disabled_text']};
    }}
    
    /* Скрываем кнопки спинбокса в QDateEdit */
    QDateEdit::up-button, QDateEdit::down-button {{
        width: 0px;
        border: none;
    }}
    
    /* Выпадающие списки */
    QComboBox {{
        background-color: {colors['widget_bg']};
        color: {colors['text_color']};
        border: 1px solid {colors['border_color']};
        border-radius: {BORDER_RADIUS};
        padding: {PADDING};
        min-height: 0;
        font-size: 13px;
    }}
    
    QComboBox:hover {{
        border: 1px solid {colors['accent_color']};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {colors['widget_bg']};
        color: {colors['text_color']};
        border: 1px solid {colors['border_color']};
        outline: 0;
    }}
    QComboBox QAbstractItemView::item {{
        min-height: 28px;
        padding: 6px 10px;
        font-size: 14px;
    }}
    QComboBox QAbstractItemView::item:selected {{
        background: {colors['tab_inactive_hover_bg']};
        color: {colors['text_color']};
    }}
    
    /* Чекбоксы */
    QCheckBox {{
        color: {colors['text_color']};
        spacing: 8px;
    }}
    
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {colors['border_color']};
        border-radius: 3px;
        background-color: {colors['widget_bg']};
    }}

    QCheckBox::indicator:checked {{
        background-color: {colors['accent_color']};
        border-color: {colors['accent_color']};
    }}
    
    QCheckBox::indicator:checked:hover {{
        background-color: {colors['accent_color_hover']};
        border-color: {colors['accent_color_hover']};
    }}
    
    QCheckBox::indicator:hover {{
        border-color: {colors['accent_color']};
    }}
    
    /* Спинбоксы */
    QSpinBox, QDoubleSpinBox {{
        background-color: {colors['widget_bg']};
        color: {colors['text_color']};
        border: 1px solid {colors['border_color']};
        border-radius: {BORDER_RADIUS};
        padding: 4px;
    }}
    
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 1px solid {colors['accent_color']};
    }}
    
    /* Группы */
    QGroupBox {{
        border: 1px solid {colors['border_color']};
        border-radius: {BORDER_RADIUS};
        margin-top: 1.5em;
        padding: {PADDING};
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 {PADDING};
        color: {colors['text_color']};
        background-color: transparent;
    }}
    
    /* Прогресс бар */
    QProgressBar {{
        border: 1px solid {colors['border_color']};
        border-radius: {BORDER_RADIUS};
        background-color: {colors['bg_color']};
        text-align: center;
        color: {colors['text_color']};
    }}
    
    QProgressBar::chunk {{
        background-color: {colors['accent_color']};
        border-radius: {BORDER_RADIUS};
    }}

    /* Панель управления (фон) */
    QFrame#controlPanel {{
        background-color: {colors['bg_color']};
        border-top: 1px solid {colors['border_color']};
        border-left: none;
        border-right: none;
        border-bottom: none;
        border-radius: 0;
        padding: 6px 8px; /* уменьшили вертикальные отступы */
    }}

    QLabel {{
        color: {colors['text_color']};
    }}

    /* Псевдотерминал */
    QPlainTextEdit#logView {{
        background-color: {colors['console_bg']};
        color: {colors['console_text']};
        border: 1px solid {colors['border_color']};
        border-radius: {BORDER_RADIUS};
        min-height: 120px;
    }}
    QPlainTextEdit#logView .system {{ color: {colors['console_system']}; }}
    QPlainTextEdit#logView .error {{ color: {colors['console_error']}; }}
    QPlainTextEdit#logView .warn {{ color: {colors['console_warn']}; }}
    QPlainTextEdit#logView .success {{ color: {colors['console_success']}; }}
    
    /* Скроллбар для консоли - синий как у кнопок */
    QPlainTextEdit#logView QScrollBar:vertical {{
        border: none;
        background-color: {colors['scrollbar_bg']};
        width: 10px;
        margin: 0;
    }}
    
    QPlainTextEdit#logView QScrollBar::handle:vertical {{
        background-color: {colors['accent_color']};
        min-height: 20px;
        border-radius: 5px;
    }}
    
    QPlainTextEdit#logView QScrollBar::handle:vertical:hover {{
        background-color: {colors['accent_color_hover']};
    }}
    
    QPlainTextEdit#logView QScrollBar:horizontal {{
        border: none;
        background-color: {colors['scrollbar_bg']};
        height: 10px;
        margin: 0;
    }}
    
    QPlainTextEdit#logView QScrollBar::handle:horizontal {{
        background-color: {colors['accent_color']};
        min-width: 20px;
        border-radius: 5px;
    }}
    
    QPlainTextEdit#logView QScrollBar::handle:horizontal:hover {{
        background-color: {colors['accent_color_hover']};
    }}
    
    /* Статус бар */
    QStatusBar {{
        background-color: {colors['statusbar_bg']};
        color: {colors['text_color']};
    }}
    
    /* Скроллбары */
    QScrollBar:vertical {{
        border: none;
        background-color: {colors['scrollbar_bg']};
        width: 10px;
        margin: 0;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {colors['scrollbar_handle']};
        min-height: 20px;
        border-radius: 5px;
    }}
    
    QScrollBar:horizontal {{
        border: none;
        background-color: {colors['scrollbar_bg']};
        height: 10px;
        margin: 0;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {colors['scrollbar_handle']};
        min-width: 20px;
        border-radius: 5px;
    }}
    """
