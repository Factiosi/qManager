import os
import sys
import shutil
import logging
import platform
import pytesseract
import numpy as np
try:
    import cv2
except Exception:
    cv2 = None
from pdf2image import convert_from_path
from pytesseract import image_to_string

from src.utils_data_manager import DataManager
from src.pdf_splitter import get_poppler_path
from src.utils_common import get_unique_filename, safe_move_file

logger = logging.getLogger(__name__)

OCR_CROP_REGION = (0, 700, 1600, 1000)
TESSERACT_CONFIG = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'


def _binarize_image(image, threshold_value):
    if cv2 is None:
        logger.warning("OpenCV не найден: бинаризация недоступна")
        return None
    try:
        grayscale = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        _, binary = cv2.threshold(grayscale, threshold_value, 255, cv2.THRESH_BINARY)
        return binary
    except Exception as exc:
        logger.debug(f"Не удалось применить бинаризацию: {exc}")
        return None


def check_tesseract_dependencies():
    candidates = []
    base_dir_src = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vendor', 'Tesseract-OCR'))
    candidates.append(base_dir_src)
    base_dir_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'vendor', 'Tesseract-OCR'))
    candidates.append(base_dir_root)
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, 'Tesseract-OCR'))
    if shutil.which('tesseract') or shutil.which('tesseract.exe'):
        tesseract_path = shutil.which('tesseract') or shutil.which('tesseract.exe')
        tesseract_dir = os.path.dirname(tesseract_path)
        if tesseract_dir not in candidates:
            candidates.append(tesseract_dir)
    
    for tesseract_dir in candidates:
        if os.path.exists(tesseract_dir) and os.path.isfile(os.path.join(tesseract_dir, 'tesseract.exe')):
            if tesseract_dir not in os.environ['PATH']:
                os.environ['PATH'] = tesseract_dir + os.pathsep + os.environ['PATH']
            required_files = [
                'tesseract.exe',
                'libtesseract-5.dll',
                'libpng16-16.dll',
                'zlib1.dll',
                'libleptonica-6.dll'
            ]
            missing_files = [file for file in required_files if not os.path.exists(os.path.join(tesseract_dir, file))]
            if missing_files:
                raise RuntimeError(f"Отсутствуют необходимые файлы Tesseract: {', '.join(missing_files)}")
            tessdata_dir = os.path.join(tesseract_dir, 'tessdata')
            if not os.path.exists(os.path.join(tessdata_dir, 'eng.traineddata')):
                raise RuntimeError("Отсутствуют языковые данные для английского языка")
            return tesseract_dir
    raise RuntimeError('Tesseract не найден! Проверьте, что он установлен в vendor/Tesseract-OCR или добавлен в PATH.')


try:
    TESSERACT_PATH = check_tesseract_dependencies()
    pytesseract.tesseract_cmd = os.path.join(TESSERACT_PATH, 'tesseract.exe')
except Exception as e:
    logging.error(f"Ошибка инициализации Tesseract: {e}")
    sys.exit(1)


def _get_cropped_page_image(pdf_path, poppler_path):
    # OCR crop region проверена за 3+ года работы, не менять без тестирования
    images = convert_from_path(
        pdf_path,
        first_page=1,
        last_page=1,
        poppler_path=poppler_path,
        hide_annotations=True,
    )
    if not images:
        raise RuntimeError("Не удалось получить изображение из PDF")
    left, top, right, bottom = OCR_CROP_REGION
    return images[0].crop((left, top, right, bottom))


def _ocr(image) -> str | None:
    if platform.system() == "Windows":
        os.environ['TESSERACT_CMD'] = os.path.join(TESSERACT_PATH, 'tesseract.exe')
        os.environ['TESSERACT_CREATE_NO_WINDOW'] = '1'
    text = image_to_string(image, lang="eng", config=TESSERACT_CONFIG)
    return text if text.strip() else None


def extract_text_from_first_page(pdf_path, poppler_path=None, binary_threshold=None):
    try:
        if poppler_path is None:
            poppler_path = get_poppler_path()
        cropped = _get_cropped_page_image(pdf_path, poppler_path)
        if binary_threshold is not None:
            ocr_input = _binarize_image(cropped, binary_threshold)
            if ocr_input is None:
                return None
        else:
            ocr_input = cropped
        text = _ocr(ocr_input)
        if text is None:
            logging.warning(f"Не удалось извлечь текст из {pdf_path}")
        return text
    except Exception as e:
        error_code = getattr(e, 'winerror', None)
        logging.error(f"Ошибка при обработке файла {pdf_path}: ({error_code}, '{e}')")
        return None


def extract_text_basic(pdf_path, poppler_path=None):
    return extract_text_from_first_page(pdf_path, poppler_path)


def extract_container_numbers(text, valid_containers):
    try:
        text = text.replace(" ", "").replace("\n", "")
        found_containers = []
        
        container_suffixes = {}
        for container in valid_containers:
            suffix = container[-7:]
            if suffix not in container_suffixes:
                container_suffixes[suffix] = []
            container_suffixes[suffix].append(container)
        
        for i in range(len(text) - 6):
            possible_suffix = text[i:i+7]
            if possible_suffix.isdigit() and possible_suffix in container_suffixes:
                for container in container_suffixes[possible_suffix]:
                    if container not in found_containers:
                        found_containers.append(container)
    
        return found_containers
    except Exception as e:
        logging.error(f"Ошибка при обработке текста: {e}")
        return []


def _try_ocr_with_binarization(cropped_image, valid_containers_set):
    """Два прохода бинаризации на уже обрезанном изображении (PDF не конвертируется повторно)."""
    for threshold in (127, 80):
        binary = _binarize_image(cropped_image, threshold)
        if binary is None:
            continue
        text = _ocr(binary)
        if text:
            containers = extract_container_numbers(text, valid_containers_set)
            if containers:
                return text, containers
    return None, []


def _load_data_for_renamer(data_manager, mode, excel_path, log_callback):
    if mode == "sheets":
        if log_callback:
            log_callback("Загрузка данных из Google Sheets...")
        try:
            stats = data_manager.load_sheets_data(log_callback=log_callback)
            if log_callback:
                log_callback("Данные из Google Sheets успешно загружены")
                log_callback(f"Всего строк: {stats.get('total_rows', 0)}")
                log_callback(f"Валидных контейнеров: {stats.get('valid_containers', 0)}")
            return True
        except Exception as e:
            error_msg = f"Ошибка при загрузке Google Sheets: {e}"
            logger.error(error_msg, exc_info=True)
            if log_callback:
                log_callback(error_msg)
            return False
    elif excel_path and os.path.exists(excel_path):
        if log_callback:
            log_callback("Чтение файла Excel...")
        try:
            stats = data_manager.load_excel_data(excel_path)
            if log_callback:
                log_callback(f"Всего строк в файле: {stats['total_rows']}")
                if stats['valid_rows_range'][0] and stats['valid_rows_range'][1]:
                    log_callback(f"Валидные строки: {stats['valid_rows_range'][0]}–{stats['valid_rows_range'][1]}")
                log_callback(f"Валидных контейнеров: {stats['valid_containers']}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при загрузке Excel: {e}", exc_info=True)
            if log_callback:
                log_callback(f"Ошибка при чтении Excel: {e}")
            return False
    else:
        if log_callback:
            log_callback("Не указан путь к Excel-файлу или файл не найден. Операция прервана.")
        return False


def process_pdfs(input_folder, output_folder, excel_path=None, log_callback=None, progress_callback=None, mode="logos", worker=None, ocr_binarization=False, debug_mode=False):
    def check_stop():
        if worker and hasattr(worker, 'check_stop'):
            worker.check_stop()
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if log_callback:
        log_callback("Начата операция переименования")

    data_manager = DataManager(mode=mode)
    poppler_path = get_poppler_path()
    
    if not _load_data_for_renamer(data_manager, mode, excel_path, log_callback):
        return

    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith(".pdf")]
    total_files = len(pdf_files)
    
    not_renamed_files = []
    for index, filename in enumerate(pdf_files, 1):
        check_stop()
        
        file_path = os.path.join(input_folder, filename)
        
        if log_callback:
            log_callback(f"Чтение файла {os.path.splitext(filename)[0]}")
        
        try:
            valid_containers_set = set(data_manager.latest_container_data.keys())

            try:
                cropped = _get_cropped_page_image(file_path, poppler_path)
            except Exception as e:
                logging.error(f"Ошибка при конвертации PDF {filename}: {e}")
                cropped = None

            text = _ocr(cropped) if cropped is not None else None
            container_numbers = extract_container_numbers(text, valid_containers_set) if text else []

            if not container_numbers and ocr_binarization and cropped is not None:
                logger.info(f"[BINARY] Базовый OCR не распознал контейнеры для {filename}, запускаем бинаризацию")
                if log_callback:
                    log_callback(f"Попытка через бинаризацию для {os.path.splitext(filename)[0]}")
                text, container_numbers = _try_ocr_with_binarization(cropped, valid_containers_set)
                if container_numbers:
                    logger.info(f"[BINARY] Бинаризация успешна для {filename}: {container_numbers}")

            if container_numbers:
                new_name = f"{', '.join(container_numbers)}.pdf"
                new_name = get_unique_filename(output_folder, new_name)
                new_path = os.path.join(output_folder, new_name)
                
                safe_move_file(file_path, new_path)
                
                if log_callback:
                    log_callback(f"Файл переименован в {os.path.splitext(new_name)[0]}")
            else:
                if text:
                    logger.warning(f"Файл {filename}: контейнеры не найдены")
                    if log_callback:
                        log_callback(f"Контейнер не найден в файле {os.path.splitext(filename)[0]}")
                else:
                    if log_callback:
                        log_callback(f"Не удалось извлечь текст из файла {os.path.splitext(filename)[0]}")

                unique_name = get_unique_filename(output_folder, filename)
                new_path = os.path.join(output_folder, unique_name)
                safe_move_file(file_path, new_path)
                if log_callback:
                    log_callback(f"Файл перемещен с оригинальным именем: {os.path.splitext(unique_name)[0]}")
                not_renamed_files.append(filename)
        except Exception as e:
            logger.error(f"Ошибка при обработке {filename}: {e}", exc_info=True)
            if log_callback:
                log_callback(f"Ошибка при обработке файла {os.path.splitext(filename)[0]}: {str(e)}")
            try:
                unique_name = get_unique_filename(output_folder, filename)
                new_path = os.path.join(output_folder, unique_name)
                safe_move_file(file_path, new_path)
                if log_callback:
                    log_callback(f"Файл перемещен с оригинальным именем: {os.path.splitext(unique_name)[0]}")
            except Exception as move_error:
                logger.error(f"Не удалось переместить файл {filename}: {move_error}")
            not_renamed_files.append(filename)
        
        if progress_callback:
            progress_callback(index, total_files)
    
    if not_renamed_files:
        if log_callback:
            log_callback(f"Не удалось переименовать {len(not_renamed_files)} файлов")
    else:
        if log_callback:
            log_callback("Все файлы успешно переименованы")
