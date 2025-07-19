"""
Главная точка входа в приложение.
Запускает основное окно на PySide6.

Примечание: Рекомендуется запускать приложение через start.py в корне проекта,
а не напрямую через этот файл.
"""
import sys
import logging
import os

from PySide6.QtWidgets import QApplication

from src.ui_windows_main_window import MainWindow

# Добавление пути к корню проекта в PYTHONPATH
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # Убираем дату и уровень, оставляем только сообщение
    handlers=[
        logging.StreamHandler(sys.stdout)  # Выводим в stdout вместо stderr
    ]
)

def main():
    # Запуск главного окна приложения
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()