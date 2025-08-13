import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QProgressBar, QLineEdit,
    QTabWidget, QStyle, QFrame, QSizePolicy
)
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import Qt

from src.core_settings import SettingsManager
import src.ui_styles as ui_styles
from src.ui_areas_splitter import SplitterArea
from src.ui_areas_renamer import RenamerArea
from src.ui_areas_organizer import OrganizerArea
from src.ui_areas_settings import SettingsArea
from src.ui_areas_playwright import PlaywrightArea
from src.ui_widgets_console import LogConsole
from src.ui_widgets_splitter import IconSplitter

def get_resource_path(relative_path: str) -> str:
    """Получает абсолютный путь к ресурсу"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def get_icon_path(name: str) -> str | None:
    """Возвращает путь к иконке"""
    base = "src/resources/icons"
    theme = "dark" if ui_styles.DARK_MODE else "light"
    candidates = [
        f"{base}/{name}_{theme}.svg",
        f"{base}/{name}_{theme}.png",
        f"{base}/{name}.svg",
        f"{base}/{name}.png",
        f"{base}/{name}_{'light' if theme=='dark' else 'dark'}.svg",
        f"{base}/{name}_{'light' if theme=='dark' else 'dark'}.png",
    ]
    for rel in candidates:
        path = get_resource_path(rel)
        if os.path.exists(path):
            return path
    return None

def load_icon(name: str, fallback_style=None, widget=None) -> QIcon:
    """Загружает иконку"""
    try:
        path = get_icon_path(name)
        if path:
            size = 16
            if path.lower().endswith(".svg"):
                renderer = QSvgRenderer(path)
                pm = QPixmap(size, size)
                pm.fill(Qt.transparent)
                p = QPainter(pm)
                renderer.render(p)
                p.end()
            else:
                pm = QPixmap(path)
                if pm.isNull():
                    pm = QPixmap(size, size)
                    pm.fill(Qt.transparent)
                else:
                    pm = pm.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            if name in ['file', 'folder', 'check'] or ui_styles.DARK_MODE:
                tinted = QPixmap(pm.size())
                tinted.fill(Qt.transparent)
                p2 = QPainter(tinted)
                p2.drawPixmap(0, 0, pm)
                p2.setCompositionMode(QPainter.CompositionMode_SourceIn)
                p2.fillRect(tinted.rect(), QColor("#F9FAFB"))
                p2.end()
                return QIcon(tinted)
            return QIcon(pm)
    except Exception:
        pass
    if fallback_style is not None:
        try:
            style = widget.style() if widget else QStyle()
            return style.standardIcon(fallback_style)
        except Exception:
            return QIcon()
    return QIcon()

def load_tinted_icon(name: str, fallback_style=None, widget=None, size: int = 16, color_hex: str | None = None) -> QIcon:
    """Загружает иконку с тонированием"""
    target_color = color_hex if color_hex else ui_styles.get_colors().get('text_color', '#FFFFFF')
    path = get_icon_path(name)
    pm = None
    if path:
        try:
            if path.lower().endswith('.svg'):
                renderer = QSvgRenderer(path)
                pm = QPixmap(size, size)
                pm.fill(Qt.transparent)
                p = QPainter(pm)
                renderer.render(p)
                p.end()
            else:
                base = QPixmap(path)
                if not base.isNull():
                    pm = base.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        except Exception:
            pm = None
    if pm is None:
        try:
            icon = (widget.style() if widget else QStyle()).standardIcon(fallback_style or QStyle.SP_FileIcon)
            pm = icon.pixmap(size, size)
        except Exception:
            pm = QPixmap(size, size)
            pm.fill(Qt.transparent)
    tinted = QPixmap(pm.size())
    tinted.fill(Qt.transparent)
    p2 = QPainter(tinted)
    p2.drawPixmap(0, 0, pm)
    p2.setCompositionMode(QPainter.CompositionMode_SourceIn)
    p2.fillRect(tinted.rect(), QColor(target_color))
    p2.end()
    return QIcon(tinted)

class MainWindow(QMainWindow):
    WINDOW_MIN_WIDTH = 1024
    WINDOW_MIN_HEIGHT = 768
    MARGIN_SMALL = 4
    MARGIN_NORMAL = 8
    BUTTON_HEIGHT = 32
    instance = None

    def __init__(self):
        super().__init__()
        self.setWindowTitle("qManager")
        self.setMinimumSize(self.WINDOW_MIN_WIDTH, self.WINDOW_MIN_HEIGHT)
        self.worker = None
        
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load_settings()
        
        self.debug_mode = self.settings.get('debug_mode', False)
        
        self.resize(*self.settings.get('window_size', [self.WINDOW_MIN_WIDTH, self.WINDOW_MIN_HEIGHT]))
        self.move(*self.settings.get('window_position', [100, 100]))
        
        icon_path = get_resource_path("resources/Icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        ui_styles.DARK_MODE = self.settings.get('dark_mode', False)
        
        self.menuBar().setVisible(False)

        # Инициализируем интерфейс
        self.setup_ui()
        MainWindow.instance = self
        
    def setup_ui(self):
        """Инициализация интерфейса"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(self.MARGIN_NORMAL, self.MARGIN_NORMAL, self.MARGIN_NORMAL, self.MARGIN_NORMAL)
        main_layout.setSpacing(self.MARGIN_NORMAL)

        self.setup_tabs()

        self.console = LogConsole(self)
        self.console.set_min_height(180)
        self.console.clear_btn.clicked.connect(self.clear_current_log)

        self.setup_control_panel()

        # Вертикальный сплиттер: вкладки / консоль / панель управления
        # Иконка-ручка: инвертируем только в тёмной теме
        handle_icon = load_tinted_icon("resize", None, self, color_hex="#F9FAFB") if ui_styles.DARK_MODE else load_icon("resize", None, self)
        splitter = IconSplitter(Qt.Vertical, self, handle_icon, size_px=14)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.tabs)
        splitter.addWidget(self.console)
        splitter.setStretchFactor(0, 10)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)

        # Панель управления под сплиттером
        main_layout.addWidget(self.control_panel)

        # Иконка-ручка рисуется кастомным сплиттером; внутри консоли не требуется
        
        # Убираем стандартный статус-бар; сообщения покажем рядом с прогрессом
        
        # Применяем стили
        self.apply_styles()
        
    def setup_tabs(self):
        """Настройка вкладок"""
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(False)
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(False)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Создаем области
        self.splitter_area = SplitterArea(self)
        self.renamer_area = RenamerArea(self)
        self.organizer_area = OrganizerArea(self)
        self.playwright_area = PlaywrightArea(self)
        self.settings_area = SettingsArea(self)
        
        # Иконки вкладок (кастомные с фоллбеком)
        self.tabs.addTab(self.splitter_area, load_icon("tab_splitter", QStyle.SP_FileDialogDetailedView, self), "Разделение")
        self.tabs.addTab(self.renamer_area, load_icon("tab_renamer", QStyle.SP_FileIcon, self), "Переименование")
        self.tabs.addTab(self.organizer_area, load_icon("tab_organizer", QStyle.SP_DirIcon, self), "Организация")
        self.tabs.addTab(self.playwright_area, load_icon("tab_playwright", QStyle.SP_DesktopIcon, self), "Playwright")
        self.tabs.addTab(self.settings_area, load_icon("tab_settings", QStyle.SP_FileDialogInfoView, self), "Настройки")
        
        # Восстанавливаем активную вкладку
        last_tab = self.settings.get('last_tab', 0)
        if 0 <= last_tab < self.tabs.count():
            self.tabs.setCurrentIndex(last_tab)
        # Инспектор UI удалён
    
    def setup_control_panel(self):
        """Настройка панели управления"""
        self.control_panel = QFrame()
        self.control_panel.setFrameShape(QFrame.StyledPanel)
        
        control_layout = QHBoxLayout(self.control_panel)
        control_layout.setContentsMargins(self.MARGIN_NORMAL, self.MARGIN_NORMAL, self.MARGIN_NORMAL, self.MARGIN_NORMAL)
        control_layout.setSpacing(self.MARGIN_NORMAL)
        self.control_panel.setObjectName("controlPanel")
        
        # Кнопка действия (Запустить/Стоп)
        self.action_btn = self.create_button(
            "Запустить",
            load_icon("start", QStyle.SP_MediaPlay, self),
            self.on_action_clicked,
            is_enabled=True
        )
        self.action_btn.setFixedWidth(180)
        control_layout.addWidget(self.action_btn, stretch=0)

        # Убрали статус-лейбл слева от прогресс-бара

        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Файл %v из %m")
        self.progress_bar.setFixedHeight(self.BUTTON_HEIGHT)
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # занимать всё оставшееся пространство справа
        control_layout.addWidget(self.progress_bar, stretch=1)
        # выравниваем визуально отступы слева/справа
        control_layout.addSpacing(self.MARGIN_NORMAL)

        # Первичная подпись кнопки по активной вкладке
        self.update_action_button()

        # Кнопка очистки перенесена в заголовок консоли (см. LogConsole)

        # Буферы логов по вкладкам
        self.log_buffers = {
            'split': [],
            'rename': [],
            'organize': [],
            'playwright': [],
            'settings': []
        }
        
    def create_button(self, text="", icon_style=None, on_click=None, is_enabled=True, icon_only=False):
        """Создание кнопки с унифицированным стилем"""
        btn = QPushButton(text)
        btn.setMouseTracking(True)  # Для лучшего отслеживания мыши
        
        # Устанавливаем иконку
        if icon_style is not None:
            if isinstance(icon_style, QIcon):
                btn.setIcon(icon_style)
            else:
                btn.setIcon(self.style().standardIcon(icon_style))
        
        # Настройка обработчика клика
        if on_click is not None:
            btn.clicked.connect(on_click)
        
        btn.setEnabled(is_enabled)
        
        # Настройка размеров
        if icon_only:
            btn.setProperty("iconOnly", "true")
            btn.setText("")
            size = self.BUTTON_HEIGHT
            btn.setFixedSize(size, size)
        else:
            btn.setFixedHeight(self.BUTTON_HEIGHT)
            # Убедимся, что текст не мешает клику
            btn.setStyleSheet("""
                QPushButton {
                    padding: 4px;
                    text-align: center;
                }
                QPushButton:pressed {
                    padding: 4px;
                }
            """)
        
        # Убедимся, что вся кнопка кликабельна
        btn.setAttribute(Qt.WA_AcceptTouchEvents, True)
        btn.setFocusPolicy(Qt.StrongFocus)
        
        return btn
    
    def create_browse_row(self, placeholder="", file_mode=True, file_filter="All Files (*)"):
        """Создание строки с полем ввода и кнопкой обзора"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self.MARGIN_SMALL)

        # Поле ввода
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setFixedHeight(self.BUTTON_HEIGHT)
        layout.addWidget(input_field)
        # Кнопка обзора с иконкой (кастом+фоллбек)
        # Всегда светлая иконка
        icon_style = load_tinted_icon(
            "file" if file_mode else "folder",
            (QStyle.SP_FileIcon if file_mode else QStyle.SP_DirIcon),
            self,
            color_hex="#F9FAFB"
        )
        browse_btn = self.create_button(
            "Обзор",
            icon_style,
            lambda: self.browse_file(input_field, file_filter) if file_mode else self.browse_directory(input_field)
        )
        layout.addWidget(browse_btn)
        
        return container, input_field
    
    def apply_styles(self):
        """Применяет стиль к интерфейсу и обновляет иконки под тему"""
        self.setStyleSheet(ui_styles.get_stylesheet(ui_styles.DARK_MODE))
        self.refresh_icons()

    def refresh_icons(self):
        """Обновляет иконки вкладок и кнопок с учётом текущей темы"""
        try:
            self.tabs.setTabIcon(0, load_icon("tab_splitter", QStyle.SP_FileDialogDetailedView, self))
            self.tabs.setTabIcon(1, load_icon("tab_renamer", QStyle.SP_FileIcon, self))
            self.tabs.setTabIcon(2, load_icon("tab_organizer", QStyle.SP_DirIcon, self))
            self.tabs.setTabIcon(3, load_icon("tab_playwright", QStyle.SP_DesktopIcon, self))
            self.tabs.setTabIcon(4, load_icon("tab_settings", QStyle.SP_FileDialogInfoView, self))
        except Exception:
            pass
        if hasattr(self, 'action_btn') and self.action_btn:
            # Используем QTimer для отложенного обновления, чтобы избежать конфликтов
            from PySide6.QtCore import QTimer
            QTimer.singleShot(50, self.update_action_button)

    # Инспектор UI полностью удалён
    def _current_log_key(self) -> str:
        w = self.tabs.currentWidget()
        if w == self.splitter_area:
            return 'split'
        if w == self.renamer_area:
            return 'rename'
        if w == self.organizer_area:
            return 'organize'
        if w == self.playwright_area:
            return 'playwright'
        return 'settings'

    def clear_current_log(self):
        key = self._current_log_key()
        self.log_buffers[key].clear()
        if hasattr(self, 'console'):
            self.console.clear()

    def set_worker_state(self, running: bool):
        """Управляет состоянием кнопок во время выполнения задачи"""
        if running:
            if hasattr(self, 'action_btn') and self.action_btn:
                self.action_btn.setText("Стоп")
                self.action_btn.setIcon(load_tinted_icon("stop", QStyle.SP_MediaStop, self, color_hex="#F9FAFB"))
                # Принудительно обновляем состояние
                self.action_btn.repaint()
        else:
            # Используем QTimer для отложенного обновления, чтобы избежать конфликтов
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self.update_action_button)

    def stop_worker(self):
        """Останавливает текущий рабочий поток"""
        if self.worker and hasattr(self.worker, 'isRunning') and self.worker.isRunning():
            self.log_message("Остановка текущей операции...")
            
            # Запрашиваем мягкую остановку
            self.worker.request_stop()
            
            # Даем немного времени на мягкую остановку
            self.worker.quit()
            
            # Ждем завершения с коротким таймаутом
            if not self.worker.wait(1000):  # 1 секунда
                self.log_message("Принудительная остановка...")
                self.worker.terminate()
                # Не ждем долго, просто принудительно останавливаем
                self.worker.wait(500)  # 0.5 секунды
                self.log_message("Операция принудительно остановлена.")
            else:
                self.log_message("Операция остановлена.")
            
            self.worker = None
            
            # Сбрасываем прогресс-бар при остановке
            if hasattr(self, 'progress_bar') and self.progress_bar:
                self.progress_bar.setValue(0)
                
        # Принудительно обновляем состояние кнопки
        self.set_worker_state(False)

    def on_tab_changed(self, _index: int):
        if hasattr(self, 'action_btn') and self.action_btn:
            # Используем QTimer для отложенного обновления, чтобы избежать конфликтов
            from PySide6.QtCore import QTimer
            QTimer.singleShot(50, self.update_action_button)
        
        # Обновляем текст прогресс-бара в зависимости от вкладки
        if hasattr(self, 'progress_bar') and self.progress_bar:
            current_widget = self.tabs.currentWidget()
            if current_widget == self.splitter_area:
                self.progress_bar.setFormat("Страница %v из %m")
            else:
                self.progress_bar.setFormat("Файл %v из %m")

    def update_action_button(self):
        """Обновляет текст и иконку кнопки действия согласно активной вкладке."""
        if not hasattr(self, 'action_btn') or not self.action_btn:
            return
            
        # Проверяем состояние worker'а более надежно
        worker_running = self.worker and hasattr(self.worker, 'isRunning') and self.worker.isRunning()
        
        if worker_running:
            self.action_btn.setText("Стоп")
            self.action_btn.setIcon(load_tinted_icon("stop", QStyle.SP_MediaStop, self, color_hex="#F9FAFB"))
            # Принудительно обновляем состояние
            self.action_btn.repaint()
            return
            
        text, icon = self.get_current_action_meta()
        handler = self.get_current_action_handler()
        if not handler:
            self.action_btn.setVisible(False)
            return
            
        self.action_btn.setVisible(True)
        self.action_btn.setText(text)
        # Используем всегда светлую старт-иконку
        if icon is None or icon == QStyle.SP_MediaPlay:
            self.action_btn.setIcon(load_tinted_icon("start", QStyle.SP_MediaPlay, self, color_hex="#F9FAFB"))
        else:
            self.action_btn.setIcon(self.style().standardIcon(icon))
            
        # Принудительно обновляем состояние
        self.action_btn.repaint()

    def on_action_clicked(self):
        """Запуск текущего действия или остановка."""
        try:
            worker_running = self.worker and hasattr(self.worker, 'isRunning') and self.worker.isRunning()
            
            if worker_running:
                self.stop_worker()
            else:
                handler = self.get_current_action_handler()
                if handler:
                    handler()
        except Exception as e:
            self.log_message(f"Ошибка: {str(e)}")

    def get_current_action_meta(self):
        """Возвращает (text, icon) для текущей вкладки, если она предоставляет action."""
        current = self.tabs.currentWidget()
        if hasattr(current, "get_action"):
            meta = current.get_action()
            return meta.get("text", "Запустить"), meta.get("icon", QStyle.SP_MediaPlay)
        return "Запустить", QStyle.SP_MediaPlay

    def get_current_action_handler(self):
        current = self.tabs.currentWidget()
        if hasattr(current, "get_action"):
            meta = current.get_action()
            return meta.get("handler")
        return None

    def log_message(self, message: str):
        """Логирует сообщение и сохраняет текущие настройки"""
        import logging
        from datetime import datetime
        
        key = self._current_log_key()
        
        # Настройка логирования для режима отладки - ТОЛЬКО ФИЛЬТРАЦИЯ
        if self.settings.get('debug_mode', False):
            # В режиме отладки НЕ ТРОГАЕМ ЛОГГЕРЫ ВООБЩЕ
            # Просто логируем все сообщения как есть
            pass
        
        # Добавляем перенос строки перед новыми операциями
        if message.startswith("Начата операция"):
            # ВСЕГДА добавляем \n перед операцией, кроме самой первой в приложении
            # Проверяем, есть ли сообщения в ЛЮБОМ из буферов
            any_messages = any(bool(buf) for buf in self.log_buffers.values())
            if any_messages:
                message = f"\n[{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}] {message}"
            else:
                message = f"[{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}] {message}"
        else:
            message = f"[{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}] {message}"
        
        # Добавляем сообщение в лог буфер и консоль UI
        self.log_buffers[key].append(message)
        if hasattr(self, 'console'):
            self.console.append_line(message)
        
        # Сохраняем настройки
        if hasattr(self, 'settings_area'):
            self.settings_area.save_settings()

    def update_progress(self, current, total):
        """Обновляет прогресс-бар"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        
        # Сбрасываем прогресс-бар по завершении операции
        if current >= total:
            self.progress_bar.setValue(0)

    def browse_file(self, input_field, file_filter="All Files (*)"):
        """Диалог выбора файла"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", file_filter)
        if file_path:
            input_field.setText(file_path)

    def browse_directory(self, output_field):
        """Диалог выбора директории"""
        directory = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if directory:
            output_field.setText(directory)
                        
    def closeEvent(self, event):
        """Сохраняем настройки при закрытии окна"""
        self.stop_worker()
        
        # Сохраняем размер и позицию окна
        self.settings['window_size'] = [self.width(), self.height()]
        self.settings['window_position'] = [self.x(), self.y()]
        
        # Сохраняем номер активной вкладки
        self.settings['last_tab'] = self.tabs.currentIndex()
        
        # Сохраняем настройки темы
        self.settings['dark_mode'] = ui_styles.DARK_MODE
        
        # Сохраняем все настройки
        self.settings_manager.save_settings(self.settings)
        
        event.accept()
