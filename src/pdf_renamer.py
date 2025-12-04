"""Модуль для переименования PDF файлов"""
import os
import sys
import shutil
import logging
import platform
import pytesseract
from pdf2image import convert_from_path
from pytesseract import image_to_string
from src.utils_data_manager import DataManager
from src.pdf_splitter import get_poppler_path

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

def check_tesseract_dependencies():
    """Проверяет зависимости Tesseract"""
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
    """Извлекает текст из первой страницы PDF"""
    try:
        # Детальное логирование для режима отладки
        if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
            logging.info(f"Начинаем извлечение текста из: {pdf_path}")
        
        if poppler_path is None:
            poppler_path = get_poppler_path()
            if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                logging.info(f"Используем Poppler путь: {poppler_path}")
        
        # Глобальный перехватчик subprocess уже работает, просто вызываем convert_from_path
        if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
            logging.info("Конвертируем PDF в изображение...")
        
        images = convert_from_path(
            pdf_path,
            first_page=1,
            last_page=1,
            poppler_path=poppler_path,
            hide_annotations=True
        )
        if not images:
            raise RuntimeError("Не удалось получить изображение из PDF")
        
        image = images[0]
        if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
            logging.info(f"Получено изображение размером: {image.size}")
        
        # Фиксированная область, как в вашей рабочей версии
        left, top, right, bottom = 0, 700, 1600, 1000
        if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
            logging.info(f"Обрезаем область: ({left}, {top}, {right}, {bottom})")
        
        cropped_image = image.crop((left, top, right, bottom))
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
        
        if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
            logging.info(f"Конфигурация Tesseract: {custom_config}")
        
        # Настройки для скрытия консоли Tesseract на Windows
        if platform.system() == "Windows":
            if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                logging.info("Настраиваем Tesseract для Windows...")
            
            # Скрываем консоль Tesseract
            import os
            os.environ['TESSERACT_CMD'] = os.path.join(TESSERACT_PATH, 'tesseract.exe')
            # Флаг --quiet не поддерживается в данной версии Tesseract
            # custom_config += ' --quiet'
                    
            # Дополнительно скрываем консоль Tesseract через переменные окружения
            os.environ['TESSERACT_CREATE_NO_WINDOW'] = '1'
                    
        if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
            logging.info("Запускаем OCR...")
        
        text = image_to_string(cropped_image, lang="eng", config=custom_config)
        
        if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
            logging.info(f"OCR завершен. Извлеченный текст: '{text.strip()}'")
        
        if not text.strip():
            logging.warning(f"Не удалось извлечь текст из {pdf_path}")
            return None
        return text
    except Exception as e:
        if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
            logging.error(f"Ошибка при извлечении текста: {e}")
        
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

def process_pdfs(input_folder, output_folder, excel_path=None, log_callback=None, progress_callback=None, mode="logos", worker=None):
    """
    Переименовывает PDF файлы на основе найденных номеров контейнеров
    
    Args:
        input_folder: исходная папка с PDF
        output_folder: папка для сохранения
        excel_path: путь к Excel файлу (опционально)
        log_callback: функция логирования
        progress_callback: функция отображения прогресса
        worker: Ссылка на WorkerThread для проверки остановки
    """
    def check_stop():
        """Проверяет, запрошена ли остановка"""
        if worker and hasattr(worker, 'check_stop'):
            worker.check_stop()
    
    # Детальное логирование для режима отладки
    if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
        logging.info(f"Начинаем переименование PDF файлов")
        logging.info(f"Входная папка: {input_folder}")
        logging.info(f"Выходная папка: {output_folder}")
        logging.info(f"Excel файл: {excel_path}")
        logging.info(f"Режим: {mode}")
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
            logging.info(f"Создана выходная папка: {output_folder}")

    if log_callback:
        log_callback("Начата операция переименования")

    data_manager = DataManager(mode=mode)
    poppler_path = get_poppler_path()
    
    if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
        logging.info(f"Poppler путь: {poppler_path}")

    # Загрузка данных (Excel или Google Sheets)
    if mode == "sheets":
        # Загрузка данных из Google Sheets
        if log_callback:
            log_callback("Загрузка данных из Google Sheets...")
        try:
            if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                logging.info("Загружаем данные из Google Sheets...")
            
            stats = data_manager.load_sheets_data()
            
            if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                logging.info(f"Google Sheets загружен. Статистика: {stats}")
            
            if log_callback:
                log_callback("Данные из Google Sheets успешно загружены")
                log_callback(f"Всего строк: {stats.get('total_rows', 0)}")
                log_callback(f"Валидных контейнеров: {stats.get('valid_containers', 0)}")
        except Exception as e:
            error_msg = f"Ошибка при загрузке Google Sheets: {e}"
            logger.error(error_msg, exc_info=True)
            if log_callback:
                log_callback(error_msg)
            return
    elif excel_path and os.path.exists(excel_path):
        # Загрузка данных из Excel
        if log_callback:
            log_callback("Чтение файла Excel...")
        try:
            if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                logging.info("Загружаем данные из Excel...")
            
            stats = data_manager.load_excel_data(excel_path)
            
            if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                logging.info(f"Excel загружен. Статистика: {stats}")
            
            if log_callback:
                log_callback(f"Всего строк в файле: {stats['total_rows']}")
                if stats['valid_rows_range'][0] and stats['valid_rows_range'][1]:
                    log_callback(f"Валидные строки: {stats['valid_rows_range'][0]}–{stats['valid_rows_range'][1]}")
                log_callback(f"Валидных конейтнеров: {stats['valid_containers']}")
        except Exception as e:
            if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                logging.error(f"Ошибка при загрузке Excel: {e}")
            if log_callback:
                log_callback(f"Ошибка при чтении Excel: {e}")
            return
    else:
        if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
            logging.warning(f"Excel файл не найден: {excel_path}")
        if log_callback:
            log_callback("Не указан путь к Excel-файлу или файл не найден. Операция прервана.")
        return

    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith(".pdf")]
    total_files = len(pdf_files)
    
    if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
        logging.info(f"Найдено PDF файлов: {total_files}")
    
    not_renamed_files = []
    for index, filename in enumerate(pdf_files, 1):
        # Проверяем остановку
        check_stop()
        
        file_path = os.path.join(input_folder, filename)
        
        if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
            logging.info(f"Обрабатываем файл {index}/{total_files}: {filename}")
        
        if log_callback:
            log_callback(f"Чтение файла {os.path.splitext(filename)[0]}")
        
        try:
            if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                logging.info(f"Извлекаем текст из: {filename}")
            
            text = extract_text_from_first_page(file_path, poppler_path)
            
            if text:
                if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                    logging.info(f"Текст извлечен из {filename}: '{text.strip()}'")
                
                container_numbers = extract_container_numbers(text, set(data_manager.latest_container_data.keys()))
                
                if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                    logging.info(f"Найдены контейнеры в {filename}: {container_numbers}")
                
                if container_numbers:
                    new_name = f"{', '.join(container_numbers)}.pdf"
                    new_name = get_unique_filename(output_folder, new_name)
                    new_path = os.path.join(output_folder, new_name)
                    
                    if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                        logging.info(f"Переименовываем {filename} в {new_name}")
                    
                    os.rename(file_path, new_path)
                    if log_callback:
                        log_callback(f"Файл переименован в {os.path.splitext(new_name)[0]}")
                else:
                    if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                        logging.warning(f"Контейнеры не найдены в {filename}")
                    if log_callback:
                        log_callback(f"Контейнер не найден в файле {os.path.splitext(filename)[0]}")
                    # Перемещаем файл в выходную папку с оригинальным именем
                    unique_name = get_unique_filename(output_folder, filename)
                    new_path = os.path.join(output_folder, unique_name)
                    os.rename(file_path, new_path)
                    if log_callback:
                        log_callback(f"Файл перемещен с оригинальным именем: {os.path.splitext(unique_name)[0]}")
                    not_renamed_files.append(filename)
            else:
                if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                    logging.warning(f"Текст не извлечен из {filename}")
                if log_callback:
                    log_callback(f"Не удалось извлечь текст из файла {os.path.splitext(filename)[0]}")
                # Перемещаем файл в выходную папку с оригинальным именем
                unique_name = get_unique_filename(output_folder, filename)
                new_path = os.path.join(output_folder, unique_name)
                os.rename(file_path, new_path)
                if log_callback:
                    log_callback(f"Файл перемещен с оригинальным именем: {os.path.splitext(unique_name)[0]}")
                not_renamed_files.append(filename)
        except Exception as e:
            if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                logging.error(f"Ошибка при обработке {filename}: {e}")
            if log_callback:
                log_callback(f"Ошибка при обработке файла {os.path.splitext(filename)[0]}: {str(e)}")
            # Перемещаем файл в выходную папку с оригинальным именем даже при ошибке
            try:
                unique_name = get_unique_filename(output_folder, filename)
                new_path = os.path.join(output_folder, unique_name)
                os.rename(file_path, new_path)
                if log_callback:
                    log_callback(f"Файл перемещен с оригинальным именем: {os.path.splitext(unique_name)[0]}")
            except Exception as move_error:
                if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                    logging.error(f"Не удалось переместить файл {filename}: {move_error}")
            not_renamed_files.append(filename)
        
        if progress_callback:
            progress_callback(index, total_files)
    
    if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
        logging.info(f"Переименование завершено. Не переименовано файлов: {len(not_renamed_files)}")
    
    if not_renamed_files:
        if log_callback:
            log_callback(f"Не удалось переименовать {len(not_renamed_files)} файлов")
    else:
        if log_callback:
            log_callback("Все файлы успешно переименованы")
