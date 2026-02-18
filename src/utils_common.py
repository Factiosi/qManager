import os
import sys
import logging
import shutil
from pathlib import Path

_DEBUG_HANDLER_ATTR = "qmanager_debug_handler"


def get_project_root() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


def configure_debug_logging(debug_mode: bool) -> None:
    """Глобальная настройка логирования в файл. Вызывать при старте и при смене debug_mode."""
    root = logging.getLogger()
    for h in list(root.handlers):
        if getattr(h, _DEBUG_HANDLER_ATTR, False):
            root.removeHandler(h)
            h.close()

    if not debug_mode:
        root.setLevel(logging.CRITICAL)
        return

    try:
        fh = logging.FileHandler(get_project_root() / "debug.log", encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        setattr(fh, _DEBUG_HANDLER_ATTR, True)
        root.addHandler(fh)
        root.setLevel(logging.DEBUG)
    except Exception:
        pass


# Оставлен для обратной совместимости, делегирует в configure_debug_logging
def ensure_debug_file_logger(debug_mode: bool, logger: logging.Logger) -> None:
    configure_debug_logging(debug_mode)


def get_unique_filename(base_path: str, original_name: str) -> str:
    if not os.path.exists(base_path):
        return original_name
    
    name, ext = os.path.splitext(original_name)
    counter = 2
    new_name = original_name
    
    while os.path.exists(os.path.join(base_path, new_name)):
        new_name = f"{name} ({counter}){ext}"
        counter += 1
    
    return new_name


def safe_move_file(src: str, dst: str) -> None:
    try:
        shutil.move(src, dst)
    except OSError:
        shutil.copy2(src, dst)
        os.remove(src)
