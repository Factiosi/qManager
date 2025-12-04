"""Модуль для разделения PDF-файлов"""
import os
import shutil
import logging
import numpy as np
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
import sys
import time

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
    """Вычисляет средний RGB цвет (оптимизированная версия)"""
    # Используем downsampling для ускорения: берем каждый N-й пиксель
    # Для определения цвета достаточно небольшой выборки
    if image.size[0] * image.size[1] > 10000:  # Если изображение большое
        # Берем каждый 4-й пиксель по обеим осям (ускоряет в ~16 раз)
        arr = np.array(image)[::4, ::4]
    else:
        arr = np.array(image)
    return arr.mean(axis=(0, 1))

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
    """Конвертирует страницу PDF в изображение (используется для обратной совместимости)"""
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

def extract_all_pages_as_images(pdf_path, poppler_path=None, dpi=72, log_callback=None, progress_callback=None, total_pages=None, worker=None):
    """Конвертирует все страницы PDF в изображения за один вызов (быстрее чем по одной)"""
    if poppler_path is None:
        poppler_path = get_poppler_path()
    
    def check_stop():
        """Проверяет остановку"""
        if worker and hasattr(worker, 'check_stop'):
            try:
                worker.check_stop()
            except Exception:
                pass
    
    if log_callback and total_pages:
        try:
            log_callback(f"Конвертация {total_pages} страниц в изображения...")
        except Exception:
            pass
    
    check_stop()
    
    # Замеряем время конвертации
    start_time = time.time()
    
    # Конвертируем все страницы сразу
    images = convert_from_path(
        pdf_path,
        poppler_path=poppler_path,
        hide_annotations=True,
        dpi=dpi
    )
    
    elapsed_time = time.time() - start_time
    
    if log_callback and total_pages:
        try:
            log_callback(f"Конвертация завершена: {len(images)} страниц за {elapsed_time:.2f} сек")
        except Exception:
            pass
    
    return images

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
    
    # Конвертируем все страницы сразу - это намного быстрее
    logger.info("Начало конвертации всех страниц в изображения")
    try:
        all_images = extract_all_pages_as_images(
            input_pdf, 
            poppler_path, 
            dpi=50,  # Оптимальный баланс скорости и точности
            log_callback=log_callback,
            progress_callback=progress_callback,
            total_pages=total_pages,
            worker=worker
        )
        logger.info(f"Конвертировано {len(all_images)} страниц")
    except Exception as e:
        error_msg = f"Ошибка при конвертации страниц: {e}"
        logger.error(error_msg, exc_info=True)
        try:
            if log_callback:
                log_callback(error_msg)
        except Exception:
            pass
        return
    
    page_info = []
    for i in range(total_pages):
        # Проверяем остановку
        check_stop()
        
        logger.debug(f"Обрабатываем страницу {i+1}/{total_pages}")
        
        if i >= len(all_images):
            logger.warning(f"Изображение для страницы {i+1} отсутствует")
            page_info.append((False, i))
            continue
        
        image = all_images[i]
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