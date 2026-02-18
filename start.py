#!/usr/bin/env python3
"""Точка входа в приложение qManager"""

import sys
from pathlib import Path

# Настройка путей для корректной работы модулей
PROJECT_ROOT = Path(__file__).parent

# Добавляем корень проекта для импорта from src.xxx
sys.path.insert(0, str(PROJECT_ROOT))

# Отключаем вывод логов в терминал
import logging
logging.basicConfig(
    level=logging.CRITICAL,
    handlers=[logging.NullHandler()],
    force=True
)

# Активируем глобальный перехватчик subprocess
import src.subprocess_hider

# Запускаем приложение
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from src.ui_windows_main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())