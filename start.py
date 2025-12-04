#!/usr/bin/env python3
"""Точка входа в приложение qManager"""

import sys
from pathlib import Path

# Настройка путей для корректной работы модулей
PROJECT_ROOT = Path(__file__).parent
SRC_PATH = PROJECT_ROOT / "src"

# Добавляем src в путь для импорта модулей
sys.path.insert(0, str(SRC_PATH))

# Отключаем вывод логов в терминал
import logging
logging.basicConfig(
    level=logging.CRITICAL,
    handlers=[],
    force=True
)

# Активируем глобальный перехватчик subprocess
import src.subprocess_hider

# Запускаем приложение
from PySide6.QtWidgets import QApplication
from src.ui_windows_main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())