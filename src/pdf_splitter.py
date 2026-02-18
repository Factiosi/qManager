import os
import shutil
import logging
import numpy as np
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
import sys
import time

logger = logging.getLogger(__name__)

def get_average_color_rgb(image):
    if image.size[0] * image.size[1] > 10000:
        arr = np.array(image)[::4, ::4]
    else:
        arr = np.array(image)
    return arr.mean(axis=(0, 1))

def is_greenish_hue(avg_rgb, threshold):
    r, g, b = avg_rgb
    return g > (r + threshold) and g > b and g > 100

def extract_page_as_image(pdf_path, page_number, poppler_path=None):
    if poppler_path is None:
        poppler_path = get_poppler_path()
    
    images = convert_from_path(
        pdf_path,
        first_page=page_number + 1,
        last_page=page_number + 1,
        poppler_path=poppler_path,
        hide_annotations=True
    )
    
    return images[0] if images else None

def extract_all_pages_as_images(pdf_path, poppler_path=None, dpi=72, log_callback=None, progress_callback=None, total_pages=None, worker=None):
    if poppler_path is None:
        poppler_path = get_poppler_path()
    
    def check_stop():
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
    
    start_time = time.time()
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
    def check_stop():
        if worker and hasattr(worker, 'check_stop'):
            worker.check_stop()
    
    if log_callback:
        log_callback("Начата операция разделения")
    
    os.makedirs(output_dir, exist_ok=True)
    
    reader = PdfReader(input_pdf)
    total_pages = len(reader.pages)
    
    if progress_callback:
        progress_callback(0, total_pages)
    
    try:
        all_images = extract_all_pages_as_images(
            input_pdf, 
            poppler_path, 
            dpi=50,
            log_callback=log_callback,
            progress_callback=progress_callback,
            total_pages=total_pages,
            worker=worker
        )
    except Exception as e:
        error_msg = f"Ошибка при конвертации страниц: {e}"
        logger.error(error_msg, exc_info=True)
        if log_callback:
            log_callback(error_msg)
        return
    
    page_info = []
    for i in range(total_pages):
        check_stop()
        
        if i >= len(all_images):
            logger.warning(f"Изображение для страницы {i+1} отсутствует")
            page_info.append((False, i))
            continue
        
        image = all_images[i]
        avg_rgb = get_average_color_rgb(image)
        is_green = is_greenish_hue(avg_rgb, threshold)
        
        page_info.append((is_green, i))
        del image
        page_type = "АКФК" if is_green else "иной документ"
        if log_callback:
            log_callback(f"Сканирование страницы {i+1} ({page_type})")
        if progress_callback:
            progress_callback(i + 1, total_pages)
    
    writer = None
    file_index = 1
    saved_files = 0
    for i, (is_green, page_num) in enumerate(page_info):
        check_stop()
        
        if page_num is None:
            continue
        if is_green:
            if writer:
                output_path = os.path.join(output_dir, f"output_{file_index}.pdf")
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
    candidates = []
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    candidates.append(os.path.join(base_path, 'vendor', 'poppler', 'bin'))
    base_path2 = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    candidates.append(os.path.join(base_path2, 'vendor', 'poppler', 'bin'))
    if shutil.which('pdftoppm') or shutil.which('pdftoppm.exe'):
        candidates.append(None)
    if getattr(sys, 'frozen', False):
        exe_path = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_path, 'poppler', 'bin'))
    for path in candidates:
        if path is None:
            return None
        if os.path.exists(path) and any(
            os.path.isfile(os.path.join(path, exe)) for exe in ['pdftoppm.exe', 'pdftoppm']):
            return path
    raise RuntimeError('Poppler не найден! Проверьте, что poppler установлен в vendor/poppler/bin или добавлен в PATH.')