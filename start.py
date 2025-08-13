#!/usr/bin/env python3
"""Точка входа в приложение qManager"""

import sys
import os
from pathlib import Path

# Настройка путей для корректной работы модулей
PROJECT_ROOT = Path(__file__).parent
SRC_PATH = PROJECT_ROOT / "src"

# Добавляем src в путь для импорта модулей
sys.path.insert(0, str(SRC_PATH))

# Отключаем вывод логов в терминал
import logging

# ПРИНУДИТЕЛЬНО ОТКЛЮЧАЕМ ВСЕ HANDLERS
logging.basicConfig(
    level=logging.CRITICAL,
    handlers=[],
    force=True
)
logging.getLogger().handlers.clear()
logging.getLogger().setLevel(logging.CRITICAL)  # Только критические ошибки

# Активируем глобальный перехватчик subprocess
import src.subprocess_hider

# Запускаем приложение
from PySide6.QtWidgets import QApplication
from src.ui_windows_main_window import MainWindow
from PySide6.QtCore import QTimer

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # Настраиваем детальное логирование для псевдоконсоли
    def setup_detailed_logging():
        """Настраивает детальное логирование в псевдоконсоль"""
        # ОТКЛЮЧАЕМ КОНСОЛЬНЫЙ HANDLER - ЛОГИ ТОЛЬКО В ФАЙЛ
        pass
    
    # Настраиваем файловое логирование для режима отладки
    def setup_file_logging():
        """Настраивает файловое логирование для детальных логов"""
        # HANDLER'Ы ТЕПЕРЬ ДОБАВЛЯЮТСЯ В САМИХ МОДУЛЯХ
        pass
    
    # Настраиваем логирование после создания окна
    # QTimer.singleShot(100, setup_file_logging)  # ФАЙЛОВОЕ ЛОГИРОВАНИЕ ОТКЛЮЧЕНО
    # QTimer.singleShot(200, setup_detailed_logging)  # КОНСОЛЬНЫЙ HANDLER ОТКЛЮЧЕН
    
    # HANDLER'Ы ДОБАВЛЯЮТСЯ В САМИХ МОДУЛЯХ
    # setup_file_logging()
    
    window.show()
    
    # ПРИНУДИТЕЛЬНО ОТКЛЮЧАЕМ ЛОГИ В ТЕРМИНАЛ ПОСЛЕ СОЗДАНИЯ ВСЕХ ОБЪЕКТОВ
    QTimer.singleShot(500, lambda: logging.getLogger().handlers.clear())
    QTimer.singleShot(500, lambda: logging.getLogger().setLevel(logging.CRITICAL))
    
    sys.exit(app.exec())