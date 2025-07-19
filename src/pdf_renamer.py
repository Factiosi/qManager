"""
Модуль для переименования PDF файлов на основе извлеченного текста.
"""
import os
import sys
import shutil
import logging
import pytesseract
from pdf2image import convert_from_path
from pytesseract import image_to_string
from src.utils_data_manager import DataManager
from src.pdf_splitter import get_poppler_path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_tesseract_dependencies():
    """
    Проверяет наличие всех необходимых DLL для Tesseract в нескольких местах и выводит путь для отладки.
    Возвращает:
        str: Путь к tesseract.exe, если найден.
    Исключения:
        RuntimeError: Если не найдены необходимые файлы или языковые данные.
    """
    candidates = []
    # 1. vendor/Tesseract-OCR относительно src
    base_dir_src = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vendor', 'Tesseract-OCR'))
    candidates.append(base_dir_src)
    # 2. vendor/Tesseract-OCR относительно корня проекта
    base_dir_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'vendor', 'Tesseract-OCR'))
    candidates.append(base_dir_root)
    # 3. frozen exe
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, 'Tesseract-OCR'))
    # 4. В системном PATH    if shutil.which('tesseract') or shutil.which('tesseract.exe'):
        return shutil.which('tesseract')# Проверяем кандидатов
    for tesseract_dir in candidates:
        if os.path.exists(tesseract_dir) and os.path.isfile(os.path.join(tesseract_dir, 'tesseract.exe')):
            # Добавляем путь к Tesseract в PATH
            if tesseract_dir not in os.environ['PATH']:
                os.environ['PATH'] = tesseract_dir + os.pathsep + os.environ['PATH']
            # Проверяем наличие необходимых файлов
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

# Инициализация Tesseract
try:
    TESSERACT_PATH = check_tesseract_dependencies()
    pytesseract.tesseract_cmd = os.path.join(TESSERACT_PATH, 'tesseract.exe')
except Exception as e:
    logging.error(f"Ошибка инициализации Tesseract: {e}")
    sys.exit(1)

def extract_text_from_first_page(pdf_path, poppler_path=None):
    """
    Извлекает текст из фиксированной области первой страницы PDF (строго по координатам).
    Аргументы:
        pdf_path (str): Путь к PDF-файлу.
        poppler_path (str, optional): Путь к Poppler, если требуется.
    Возвращает:
        str или None: Извлечённый текст или None при ошибке.
    Исключения:
        FileNotFoundError: Если PDF не найден.
        RuntimeError: Если не удалось получить изображение из PDF.
    """
    try:
        if poppler_path is None:
            poppler_path = get_poppler_path()
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF файл не найден: {pdf_path}")
        images = convert_from_path(
            pdf_path,
            first_page=1,
            last_page=1,
            poppler_path=poppler_path
        )
        if not images:
            raise RuntimeError("Не удалось получить изображение из PDF")
        image = images[0]
        # Фиксированная область, как в вашей рабочей версии
        left, top, right, bottom = 0, 700, 1600, 1000
        cropped_image = image.crop((left, top, right, bottom))
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
        text = image_to_string(cropped_image, lang="eng", config=custom_config)
        if not text.strip():
            logging.warning(f"Не удалось извлечь текст из {pdf_path}")
            return None
        return text
    except Exception as e:
        error_code = None
        if hasattr(e, 'winerror'):
            error_code = e.winerror
        logging.error(f"Ошибка при обработке файла {pdf_path}: ({error_code}, '{str(e)}')")
        return None

def extract_container_numbers(text, valid_containers):
    """
    Ищет номера контейнеров в тексте.
    Аргументы:
        text (str): Текст для поиска.
        valid_containers (list): Список валидных номеров контейнеров.
    Возвращает:
        list: Список найденных номеров контейнеров.
    """
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

def get_unique_filename(base_path, original_name):
    """Генерирует уникальное имя файла, добавляя индекс к дубликатам"""
    if not os.path.exists(base_path):
        return original_name
    
    name, ext = os.path.splitext(original_name)
    counter = 2
    new_name = original_name
    
    while os.path.exists(os.path.join(base_path, new_name)):
        new_name = f"{name} ({counter}){ext}"
        counter += 1
    
    return new_name

def process_pdfs(input_folder, output_folder, excel_path=None, log_callback=None, progress_callback=None):
    """
    Переименовывает PDF файлы на основе найденных номеров контейнеров
    
    Args:
        input_folder: исходная папка с PDF
        output_folder: папка для сохранения
        excel_path: путь к Excel файлу (опционально)
        log_callback: функция логирования
        progress_callback: функция отображения прогресса
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    data_manager = DataManager()
    poppler_path = get_poppler_path()

    if excel_path and os.path.exists(excel_path):
        if log_callback:
            log_callback(f"Загрузка данных из Excel: {excel_path}")
        try:
            data_manager.load_excel_data(excel_path)
            if log_callback:
                log_callback("Данные из Excel успешно загружены")
        except Exception as e:
            if log_callback:
                log_callback(f"Ошибка при загрузке Excel: {e}")
            return
    else:
        if log_callback:
            log_callback("Не указан путь к Excel-файлу или файл не найден. Операция прервана.")
        return

    valid_containers = set(data_manager.latest_container_data.keys())
    if log_callback:
        log_callback(f"Загружено {len(valid_containers)} валидных контейнеров")

    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith(".pdf")]
    total_files = len(pdf_files)
    not_renamed_files = []
    
    for index, filename in enumerate(pdf_files, 1):
        file_path = os.path.join(input_folder, filename)
        if log_callback:
            log_callback(f"Обрабатывается: {filename}")
        
        try:
            text = extract_text_from_first_page(file_path, poppler_path)
            if text:
                container_numbers = extract_container_numbers(text, valid_containers)
                if container_numbers:
                    new_name = f"{', '.join(container_numbers)}.pdf"
                    new_name = get_unique_filename(output_folder, new_name)
                    new_path = os.path.join(output_folder, new_name)
                    os.rename(file_path, new_path)
                    if log_callback:
                        log_callback(f"Файл переименован: {new_name}")
                else:
                    new_name = get_unique_filename(output_folder, filename)
                    new_path = os.path.join(output_folder, new_name)
                    os.rename(file_path, new_path)
                    if log_callback:
                        log_callback(f"Файл перемещен без переименования: {new_name}")
                    not_renamed_files.append(filename)
            else:
                if log_callback:
                    log_callback(f"Не удалось извлечь текст из файла {filename}")
                not_renamed_files.append(filename)
        except Exception as e:
            if log_callback:
                log_callback(f"Ошибка обработки файла {filename}: {e}")
            not_renamed_files.append(filename)
        
        if progress_callback:
            progress_callback(index, total_files)
    
    if log_callback:
        log_callback("Операция переименования PDF завершена")
        if not_renamed_files:
            log_callback(f"Не удалось переименовать {len(not_renamed_files)} файлов из {total_files}:")
            for filename in not_renamed_files:
                log_callback(f"- {filename}")
        else:
            log_callback("Все файлы успешно переименованы")
