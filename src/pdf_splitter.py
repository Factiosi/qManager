"""
Модуль для разделения PDF-файлов по цветовым маркерам (например, по зелёным страницам).
Используется для автоматической нарезки документов на части.
"""
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

def get_average_color_rgb(image):
    """
    Вычисляет средний RGB цвет изображения.
    :param image: PIL.Image
    :return: np.ndarray из трёх значений (R, G, B)
    """
    return np.array(image).mean(axis=(0, 1))

def is_greenish_hue(avg_rgb, threshold):
    """
    Проверяет, является ли цвет зелёным по заданному порогу.
    :param avg_rgb: np.ndarray (R, G, B)
    :param threshold: float, порог для компоненты G
    :return: bool
    """
    r, g, b = avg_rgb
    return g > (r + threshold) and g > b and g > 100

def is_black_and_white_hue(avg_rgb):
    """
    Проверяет, является ли цвет чёрно-белым (низкая насыщенность).
    :param avg_rgb: np.ndarray (R, G, B)
    :return: bool
    """
    r, g, b = avg_rgb
    is_bw = max(r, g, b) - min(r, g, b) < 30
    logging.debug(f"Проверка на чёрно-белый цвет: RGB {r:.2f}, {g:.2f}, {b:.2f} -> {is_bw}")
    return is_bw

def is_white_hue(avg_rgb):
    """
    Проверяет, является ли цвет белым (высокая яркость, низкая насыщенность).
    :param avg_rgb: np.ndarray (R, G, B)
    :return: bool
    """
    r, g, b = avg_rgb
    is_white = r > 200 and g > 200 and b > 200
    logging.debug(f"Проверка на белый цвет: RGB {r:.2f}, {g:.2f}, {b:.2f} -> {is_white}")
    return is_white

def extract_page_as_image(pdf_path, page_number, poppler_path=None):
    """
    Конвертирует страницу PDF в изображение.
    :param pdf_path: str
    :param page_number: int (нумерация с 0)
    :param poppler_path: str | None
    :return: PIL.Image | None
    """
    if poppler_path is None:
        poppler_path = get_poppler_path()
    images = convert_from_path(
        pdf_path,
        first_page=page_number + 1,
        last_page=page_number + 1,
        poppler_path=poppler_path
    )
    return images[0] if images else None

def split_pdf_by_green_pages(input_pdf, output_dir, poppler_path=None, threshold=2.3, log_callback=None, progress_callback=None):
    """
    Разделяет PDF по зелёным страницам (маркерным).
    :param input_pdf: str
    :param output_dir: str
    :param poppler_path: str | None
    :param threshold: float
    :param log_callback: callable | None
    :param progress_callback: callable | None
    """
    def log(message):
        # Если есть callback - используем его, если нет - логируем через logging
        if log_callback:
            log_callback(message)
        else:
            logger.info(message)

    os.makedirs(output_dir, exist_ok=True)
    reader = PdfReader(input_pdf)
    total_pages = len(reader.pages)

    if progress_callback:
        progress_callback(0, total_pages)

    page_info = []
    log("Анализ страниц...")
    
    for i in range(total_pages):
        if progress_callback:
            progress_callback(i + 1, total_pages)

        image = extract_page_as_image(input_pdf, i, poppler_path)
        if image is None:
            log(f"Не удалось обработать страницу {i+1}")
            page_info.append((False, None))
            continue

        avg_rgb = get_average_color_rgb(image)
        is_green = is_greenish_hue(avg_rgb, threshold)
        page_info.append((is_green, i))
        del image
        
        log(f"Страница {i+1}: {'зеленая' if is_green else 'обычная'}")

    log("Создание файлов...")
    writer = None
    file_index = 1
    
    for i, (is_green, page_num) in enumerate(page_info):
        if page_num is None:
            continue
        
        if is_green:
            if writer:
                output_path = os.path.join(output_dir, f"output_{file_index}.pdf")
                with open(output_path, "wb") as f:
                    writer.write(f)
                log(f"Создан файл: {output_path}")
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
        log(f"Создан последний файл: {output_path}")

    log("Разделение завершено")

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