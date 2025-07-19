import os
import sys
import subprocess
from pathlib import Path

if __name__ == '__main__':
    # Получаем абсолютный путь к директории проекта
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    
    # Добавляем корень проекта в PYTHONPATH
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    
    # Изменение пути для корректного импорта src.main
    SRC_PATH = os.path.join(PROJECT_ROOT, 'src')
    if SRC_PATH not in sys.path:
        sys.path.insert(0, SRC_PATH)
    
    # Импортируем и запускаем main
    from src.main import main
    main()