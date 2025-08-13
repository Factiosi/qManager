"""Модуль для разделения PDF-файлов"""
import os
import shutil
import logging
import numpy as np
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
import sys
from src.utils_data_manager import DataManager

# Настройка логгирования
logger = logging.getLogger(__name__)

# ДОБАВЛЯЕМ ФАЙЛОВЫЙ HANDLER СРАЗУ
try:
    import os
    import sys
    from pathlib import Path
    
    # Определяем путь к корню проекта
    if getattr(sys, 'frozen', False):
        # Если приложение скомпилировано
        project_root = Path(sys.executable).parent
    else:
        # Если запущено из исходников
        project_root = Path(__file__).parent.parent
    
    # Создаем файловый handler
    log_file = project_root / "debug.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # Форматтер для файла
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Добавляем handler к логгеру
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)
    
except Exception:
    pass  # Игнорируем ошибки

def get_average_color_rgb(image):
    """Вычисляет средний RGB цвет"""
    return np.array(image).mean(axis=(0, 1))

def is_greenish_hue(avg_rgb, threshold):
    """Проверяет зелёный цвет"""
    r, g, b = avg_rgb
    return g > (r + threshold) and g > b and g > 100

def is_black_and_white_hue(avg_rgb):
    """Проверяет чёрно-белый цвет"""
    r, g, b = avg_rgb
    is_bw = max(r, g, b) - min(r, g, b) < 30
    logging.debug(f"Проверка на чёрно-белый цвет: RGB {r:.2f}, {g:.2f}, {b:.2f} -> {is_bw}")
    return is_bw

def is_white_hue(avg_rgb):
    """Проверяет белый цвет"""
    r, g, b = avg_rgb
    is_white = r > 200 and g > 200 and b > 200
    logging.debug(f"Проверка на белый цвет: RGB {r:.2f}, {g:.2f}, {b:.2f} -> {is_white}")
    return is_white

def extract_page_as_image(pdf_path, page_number, poppler_path=None):
    """Конвертирует страницу PDF в изображение"""
    if poppler_path is None:
        poppler_path = get_poppler_path()
    
    # Глобальный перехватчик subprocess уже работает, просто вызываем convert_from_path
    images = convert_from_path(
        pdf_path,
        first_page=page_number + 1,
        last_page=page_number + 1,
        poppler_path=poppler_path,
        hide_annotations=True
    )
    
    return images[0] if images else None

def split_pdf_by_green_pages(input_pdf, output_dir, poppler_path=None, threshold=2.3, log_callback=None, progress_callback=None, worker=None):
    """Разделяет PDF по зелёным страницам"""
    def check_stop():
        """Проверяет остановку"""
        if worker and hasattr(worker, 'check_stop'):
            worker.check_stop()
    
    # Детальное логирование для режима отладки
    logger.info(f"Начинаем разделение PDF: {input_pdf}")
    logger.info(f"Выходная папка: {output_dir}")
    logger.info(f"Порог зеленого: {threshold}")
    
    if log_callback:
        log_callback("Начата операция разделения")
    
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Создана выходная папка: {output_dir}")
    
    reader = PdfReader(input_pdf)
    total_pages = len(reader.pages)
    
    logger.info(f"PDF содержит {total_pages} страниц")
    
    if progress_callback:
        progress_callback(0, total_pages)
    
    page_info = []
    for i in range(total_pages):
        # Проверяем остановку
        check_stop()
        
        logger.debug(f"Обрабатываем страницу {i+1}/{total_pages}")
        
        image = extract_page_as_image(input_pdf, i, poppler_path)
        if image is None:
            logger.warning(f"Не удалось извлечь изображение со страницы {i+1}")
            continue
        
        avg_rgb = get_average_color_rgb(image)
        is_green = is_greenish_hue(avg_rgb, threshold)
        
        logger.debug(f"Страница {i+1}: RGB {avg_rgb}, зеленый: {is_green}")
        
        page_info.append((is_green, i))
        del image
        page_type = "АКФК" if is_green else "иной документ"
        if log_callback:
            log_callback(f"Сканирование страницы {i+1} ({page_type})")
        if progress_callback:
            progress_callback(i + 1, total_pages)
    
    logger.info(f"Анализ страниц завершен. Зеленых страниц: {sum(1 for is_green, _ in page_info if is_green)}")
    
    writer = None
    file_index = 1
    saved_files = 0
    for i, (is_green, page_num) in enumerate(page_info):
        # Проверяем остановку
        check_stop()
        
        if page_num is None:
            continue
        if is_green:
            if writer:
                output_path = os.path.join(output_dir, f"output_{file_index}.pdf")
                
                logger.info(f"Сохраняем файл {file_index}: {output_path}")
                
                with open(output_path, "wb") as f:
                    writer.write(f)
                saved_files += 1
                file_index += 1
            writer = PdfWriter()
            writer.add_page(reader.pages[page_num])
        else:
            if writer is None:
                writer = PdfWriter()
            writer.add_page(reader.pages[page_num])
    if writer:
        output_path = os.path.join(output_dir, f"output_{file_index}.pdf")
        with open(output_path, "wb") as f:
            writer.write(f)
        saved_files += 1
    if log_callback:
        log_callback("Операция завершена")
        log_callback(f"Всего файлов сохранено: {saved_files}")

def get_poppler_path():
    """
    Определяет путь к Poppler (необходим для pdf2image).
    :return: str | None
    :raises RuntimeError: если Poppler не найден
    """
    candidates = []
    # vendor/poppler/bin относительно корня проекта
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    candidates.append(os.path.join(base_path, 'vendor', 'poppler', 'bin'))
    # vendor/poppler/bin относительно src
    base_path2 = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    candidates.append(os.path.join(base_path2, 'vendor', 'poppler', 'bin'))
    # В системном PATH
    if shutil.which('pdftoppm') or shutil.which('pdftoppm.exe'):
        candidates.append(None)  # None = использовать системный PATH
    # frozen exe
    if getattr(sys, 'frozen', False):
        exe_path = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_path, 'poppler', 'bin'))
    # Проверяем все пути
    for path in candidates:
        if path is None:
            return None
        if os.path.exists(path) and any(
            os.path.isfile(os.path.join(path, exe)) for exe in ['pdftoppm.exe', 'pdftoppm']):
            return path
    raise RuntimeError('Poppler не найден! Проверьте, что poppler установлен в vendor/poppler/bin или добавлен в PATH.')

if __name__ == "__main__":
    logging.info("Этот модуль предназначен для использования как библиотека.")