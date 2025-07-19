"""
Модуль стилей для пользовательского интерфейса.
Содержит определения стилей для различных элементов интерфейса.
"""

# Глобальные настройки темы
DARK_MODE = False

# Определение цветовых схем для светлой и темной тем
LIGHT_COLORS = {
    "bg_color": "#FFFFFF",  # Белый фон
    "widget_bg": "#FFFFFF",  # Белый фон виджетов
    "text_color": "#212121",  # Тёмно-серый текст
    "border_color": "#E0E0E0",  # Светло-серые границы
    "accent_color": "#2196F3",  # Синий акцент
    "tab_inactive_bg": "#F5F5F5",  # Светло-серый фон неактивных вкладок
    "tab_inactive_hover_bg": "#EEEEEE",  # Серый фон при наведении на неактивные вкладки
    "scrollbar_bg": "#F5F5F5",  # Светло-серый фон скроллбара
    "scrollbar_handle": "#BDBDBD"  # Серый цвет ползунка скроллбара
}

DARK_COLORS = {
    "bg_color": "#1E1E1E",  # Тёмно-серый фон
    "widget_bg": "#2D2D2D",  # Тёмно-серый фон виджетов
    "text_color": "#FFFFFF",  # Белый текст
    "border_color": "#404040",  # Тёмно-серые границы
    "accent_color": "#2196F3",  # Синий акцент
    "tab_inactive_bg": "#252525",  # Тёмно-серый фон неактивных вкладок
    "tab_inactive_hover_bg": "#303030",  # Тёмно-серый фон при наведении на неактивные вкладки
    "scrollbar_bg": "#252525",  # Тёмно-серый фон скроллбара
    "scrollbar_handle": "#404040"  # Тёмно-серый цвет ползунка скроллбара
}

# Основные цвета
PRIMARY_COLOR = "#2196F3"  # Синий
SECONDARY_COLOR = "#FFC107"  # Жёлтый
SUCCESS_COLOR = "#4CAF50"  # Зелёный
ERROR_COLOR = "#F44336"  # Красный
WARNING_COLOR = "#FF9800"  # Оранжевый
INFO_COLOR = "#00BCD4"  # Голубой

# Цвета фона
BACKGROUND_COLOR = "#FFFFFF"  # Белый
SURFACE_COLOR = "#F5F5F5"  # Светло-серый
CARD_COLOR = "#FFFFFF"  # Белый

# Цвета текста
TEXT_PRIMARY = "#212121"  # Тёмно-серый
TEXT_SECONDARY = "#757575"  # Серый
TEXT_DISABLED = "#9E9E9E"  # Светло-серый

# Цвета границ
BORDER_COLOR = "#E0E0E0"  # Светло-серый
DIVIDER_COLOR = "#BDBDBD"  # Серый

# Размеры
BORDER_RADIUS = "4px"
PADDING = "8px"
MARGIN = "8px"

# Стили для кнопок
BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {PRIMARY_COLOR};
        color: white;
        border: none;
        border-radius: {BORDER_RADIUS};
        padding: {PADDING};
        margin: {MARGIN};
    }}
    QPushButton:hover {{
        background-color: {PRIMARY_COLOR}dd;
    }}
    QPushButton:pressed {{
        background-color: {PRIMARY_COLOR}aa;
    }}
    QPushButton:disabled {{
        background-color: {TEXT_DISABLED};
    }}
"""

# Стили для полей ввода
INPUT_STYLE = f"""
    QLineEdit {{
        background-color: {SURFACE_COLOR};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_COLOR};
        border-radius: {BORDER_RADIUS};
        padding: {PADDING};
        margin: {MARGIN};
    }}
    QLineEdit:focus {{
        border: 1px solid {PRIMARY_COLOR};
    }}
    QLineEdit:disabled {{
        background-color: {TEXT_DISABLED}22;
        color: {TEXT_DISABLED};
    }}
"""

# Стили для меток
LABEL_STYLE = f"""
    QLabel {{
        color: {TEXT_PRIMARY};
        margin: {MARGIN};
    }}
"""

# Стили для групп
GROUP_STYLE = f"""
    QGroupBox {{
        background-color: {CARD_COLOR};
        border: 1px solid {BORDER_COLOR};
        border-radius: {BORDER_RADIUS};
        margin-top: 1em;
        padding: {PADDING};
    }}
    QGroupBox::title {{
        color: {TEXT_PRIMARY};
        subcontrol-origin: margin;
        left: {PADDING};
        padding: 0 3px;
    }}
"""

# Стили для прогресс-бара
PROGRESS_BAR_STYLE = f"""
    QProgressBar {{
        border: 1px solid {BORDER_COLOR};
        border-radius: {BORDER_RADIUS};
        text-align: center;
        background-color: {SURFACE_COLOR};
    }}
    QProgressBar::chunk {{
        background-color: {PRIMARY_COLOR};
        border-radius: {BORDER_RADIUS};
    }}
"""

# Стили для выпадающих списков
COMBO_BOX_STYLE = f"""
    QComboBox {{
        background-color: #e9eef5; /* чуть темнее, чем {SURFACE_COLOR} */
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_COLOR};
        border-radius: {BORDER_RADIUS};
        padding: {PADDING};
        margin: {MARGIN};
    }}
    QComboBox:hover {{
        border: 1px solid {PRIMARY_COLOR};
    }}
    QComboBox::drop-down {{
        border: none;
    }}
    QComboBox::down-arrow {{
        width: 12px;
        height: 12px;
    }}
    QComboBox:disabled {{
        background-color: {TEXT_DISABLED}22;
        color: {TEXT_DISABLED};
    }}
    QComboBox QAbstractItemView {{
        background: #e0e6ee; /* ещё чуть темнее */
        color: {TEXT_PRIMARY};
        border: 1px solid {PRIMARY_COLOR};
        selection-background-color: #c2d3ee; /* яркая подсветка выбранного */
        selection-color: {PRIMARY_COLOR};
        outline: none;
    }}
    QComboBox QAbstractItemView::item:hover {{
        background: #b3c9e6; /* ещё более заметная подсветка при наведении */
        color: {PRIMARY_COLOR};
    }}
"""

# Стили для спинбоксов
SPIN_BOX_STYLE = f"""
    QSpinBox, QDoubleSpinBox {{
        background-color: {SURFACE_COLOR};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_COLOR};
        border-radius: {BORDER_RADIUS};
        padding: {PADDING};
        margin: {MARGIN};
    }}
    QSpinBox:hover, QDoubleSpinBox:hover {{
        border: 1px solid {PRIMARY_COLOR};
    }}
    QSpinBox:disabled, QDoubleSpinBox:disabled {{
        background-color: {TEXT_DISABLED}22;
        color: {TEXT_DISABLED};
    }}
"""

# Стили для главного окна
MAIN_WINDOW_STYLE = f"""
    QMainWindow {{
        background-color: {BACKGROUND_COLOR};
    }}
"""

# Стили для вкладок
TAB_WIDGET_STYLE = f"""
    QTabWidget::pane {{
        border: 1px solid {BORDER_COLOR};
        border-radius: {BORDER_RADIUS};
        background-color: {CARD_COLOR};
    }}
    QTabBar::tab {{
        background-color: {SURFACE_COLOR};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_COLOR};
        border-bottom: none;
        border-top-left-radius: {BORDER_RADIUS};
        border-top-right-radius: {BORDER_RADIUS};
        padding: {PADDING};
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background-color: {CARD_COLOR};
        border-bottom: 1px solid {CARD_COLOR};
    }}
    QTabBar::tab:hover {{
        background-color: {PRIMARY_COLOR}22;
    }}
"""

# Стили для сообщений
MESSAGE_BOX_STYLE = f"""
    QMessageBox {{
        background-color: {CARD_COLOR};
    }}
    QMessageBox QLabel {{
        color: {TEXT_PRIMARY};
    }}
    QMessageBox QPushButton {{
        {BUTTON_STYLE}
    }}
"""

# Стили для диалогов
DIALOG_STYLE = f"""
    QDialog {{
        background-color: {CARD_COLOR};
    }}
    QDialog QLabel {{
        color: {TEXT_PRIMARY};
    }}
    QDialog QPushButton {{
        {BUTTON_STYLE}
    }}
"""

# Стили для меню
MENU_STYLE = f"""
    QMenuBar {{
        background-color: {SURFACE_COLOR};
        color: {TEXT_PRIMARY};
    }}
    QMenuBar::item:selected {{
        background-color: {PRIMARY_COLOR}22;
    }}
    QMenu {{
        background-color: {CARD_COLOR};
        border: 1px solid {BORDER_COLOR};
    }}
    QMenu::item {{
        color: {TEXT_PRIMARY};
        padding: {PADDING};
    }}
    QMenu::item:selected {{
        background-color: {PRIMARY_COLOR}22;
    }}
"""

# Стили для статусной строки
STATUS_BAR_STYLE = f"""
    QStatusBar {{
        background-color: {SURFACE_COLOR};
        color: {TEXT_PRIMARY};
    }}
"""

# Стили для скроллбара
SCROLL_BAR_STYLE = f"""
    QScrollBar:vertical {{
        border: none;
        background-color: {SURFACE_COLOR};
        width: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {TEXT_DISABLED};
        border-radius: 5px;
        min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {TEXT_SECONDARY};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        border: none;
        background-color: {SURFACE_COLOR};
        height: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {TEXT_DISABLED};
        border-radius: 5px;
        min-width: 20px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {TEXT_SECONDARY};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
"""

def get_stylesheet(dark_mode: bool) -> str:
    """Возвращает QSS стиль для приложения"""
    colors = DARK_COLORS if dark_mode else LIGHT_COLORS
    
    return f"""
    QMainWindow {{
        background-color: {colors["bg_color"]};
        font-family: "Segoe UI", sans-serif;
    }}
    
    QWidget {{
        background-color: {colors["widget_bg"]};
        color: {colors["text_color"]};
        font-family: "Segoe UI", sans-serif;
    }}
    
    QGroupBox {{
        border: 1px solid {colors["border_color"]};
        border-radius: 8px;
        margin-top: 1.5em;
        padding: 8px;
        background-color: {colors["widget_bg"]};
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 5px;
        background-color: {colors["widget_bg"]};
    }}
    
    QPushButton {{
        background-color: {colors["accent_color"]};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        min-height: 20px;
    }}
    
    QPushButton:hover {{
        background-color: #005a9e;
    }}
    
    QPushButton:pressed {{
        background-color: #004578;
    }}
    
    QLineEdit, QTextEdit {{
        border: 1px solid {colors["border_color"]};
        border-radius: 8px;
        padding: 6px 8px;
        background-color: {colors["widget_bg"]};
        color: {colors["text_color"]};
        selection-background-color: {colors["accent_color"]};
        min-height: 20px;
    }}
    
    QProgressBar {{
        border: 1px solid {colors["border_color"]};
        border-radius: 8px;
        text-align: center;
        background-color: {colors["widget_bg"]};
        color: {colors["text_color"]};
        min-height: 20px;
        padding: 1px;
    }}
    
    QProgressBar::chunk {{
        background-color: {colors["accent_color"]};
        border-radius: 6px;
        margin: 2px;
    }}
    
    QTabWidget {{
        background: transparent;
        border: none;
    }}
    
    QTabWidget::pane {{
        border: 1px solid {colors["border_color"]};
        background: {colors["widget_bg"]};
        border-bottom-left-radius: 8px;
        border-bottom-right-radius: 8px;
        margin: 0px;
        top: -1px;
    }}
    
    QTabBar::tab {{
        background: {colors["tab_inactive_bg"]};
        border: 1px solid {colors["border_color"]};
        border-bottom: none;
        padding: 8px 16px;
        margin: 0px;
        margin-right: 2px;
        min-height: 20px;
        min-width: 80px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }}
    
    QTabBar::tab:selected {{
        background: {colors["widget_bg"]};
        color: {colors["text_color"]};
        border: 1px solid {colors["accent_color"]};
        border-bottom: none;
        margin-bottom: -1px;
        padding-bottom: 9px;
    }}
    
    QTabBar::tab:!selected {{
        background: {colors["tab_inactive_bg"]};
        color: {colors["text_color"]};
    }}
    
    QTabBar::tab:hover:!selected {{
        background: {colors["tab_inactive_hover_bg"]};
    }}
    
    QScrollBar:vertical {{
        border: none;
        background: {colors["scrollbar_bg"]};
        width: 14px;
        margin: 0px;
        border-radius: 7px;
    }}
    
    QScrollBar::handle:vertical {{
        background: {colors["scrollbar_handle"]};
        min-height: 30px;
        border-radius: 7px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background: {colors["accent_color"]};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    
    QScrollBar:horizontal {{
        border: none;
        background: {colors["scrollbar_bg"]};
        height: 14px;
        margin: 0px;
        border-radius: 7px;
    }}
    
    QScrollBar::handle:horizontal {{
        background: {colors["scrollbar_handle"]};
        min-width: 30px;
        border-radius: 7px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background: {colors["accent_color"]};
    }}
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}
    """