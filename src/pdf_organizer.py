"""Модуль для организации PDF-файлов"""
import os
import re
import logging
from datetime import datetime
from PyPDF2 import PdfMerger

from src.utils_data_manager import DataManager
from src.pdf_splitter import get_poppler_path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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

def get_unique_filename(base_path, original_name):
    """Генерирует уникальное имя файла"""
    logger.debug(f"Генерация уникального имени для '{original_name}' в папке '{base_path}'")
    if not os.path.exists(base_path):
        logger.debug(f"Папка '{base_path}' не существует, возвращаем оригинальное имя")
        return original_name
    
    name, ext = os.path.splitext(original_name)
    counter = 2
    new_name = original_name
    
    while os.path.exists(os.path.join(base_path, new_name)):
        new_name = f"{name} ({counter}){ext}"
        logger.debug(f"Файл '{new_name}' уже существует, пробуем '{new_name}'")
        counter += 1
    
    logger.debug(f"Сгенерировано уникальное имя: '{new_name}'")
    return new_name

def organize_pdfs(input_folder, output_folder, excel_path=None, log_callback=None, progress_callback=None, mode="logos", worker=None):
    """Организует PDF-файлы по папкам"""
    logger.info(f"Начало операции организации PDF")
    logger.debug(f"Параметры: input_folder='{input_folder}', output_folder='{output_folder}', excel_path='{excel_path}', mode='{mode}'")
    
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            logging.info(message)
    
    def check_stop():
        """Проверяет остановку"""
        if worker and hasattr(worker, 'check_stop'):
            logger.debug("Проверка остановки worker")
            worker.check_stop()

    log("Начата операция организации")
    
    # Проверка входных параметров
    logger.debug(f"Проверка существования входной папки: {input_folder}")
    if not os.path.exists(input_folder):
        error_msg = f"Входная папка не существует: {input_folder}"
        logger.error(error_msg)
        log(error_msg)
        return
    
    logger.debug(f"Проверка существования выходной папки: {output_folder}")
    if not os.path.exists(output_folder):
        logger.info(f"Создание выходной папки: {output_folder}")
        os.makedirs(output_folder)
        log(f"Создана выходная папка: {output_folder}")
    
    # Загрузка Excel
    logger.info("Инициализация DataManager")
    data_manager = DataManager(mode=mode)
    logger.debug(f"DataManager создан в режиме '{mode}'")
    
    if excel_path and os.path.exists(excel_path):
        log("Чтение файла Excel...")
        logger.info(f"Загрузка данных из Excel: {excel_path}")
        try:
            result = data_manager.load_excel_data(excel_path)
            logger.info(f"Excel успешно загружен: {result}")
            log("Данные из Excel успешно загружены")
        except Exception as e:
            error_msg = f"Ошибка при загрузке Excel: {e}"
            logger.error(error_msg, exc_info=True)
            log(error_msg)
            return
    else:
        error_msg = f"Не указан путь к Excel-файлу или файл не найден: {excel_path}"
        logger.error(error_msg)
        log(error_msg)
        return

    # Обработка данных
    logger.info("Начало обработки данных")
    data_manager.process_data()
    logger.info(f"Данные обработаны: {len(data_manager.latest_container_data)} уникальных контейнеров")
    log(f"Обработано {len(data_manager.latest_container_data)} уникальных контейнеров")

    # Поиск PDF файлов
    logger.info("Поиск PDF файлов во входной папке")
    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith(".pdf")]
    total_files = len(pdf_files)
    logger.info(f"Найдено {total_files} PDF файлов: {pdf_files}")
    
    if total_files == 0:
        logger.warning("PDF файлы не найдены")
        log("PDF файлы не найдены во входной папке")
        return

    # Обработка PDF файлов
    processed_units = {}
    logger.info("Начало обработки PDF файлов")
    
    for index, filename in enumerate(pdf_files, 1):
        check_stop()
        
        logger.debug(f"Обработка файла {index}/{total_files}: {filename}")
        log(f"Обнаружен файл: {filename}")
        
        file_path = os.path.join(input_folder, filename)
        logger.debug(f"Полный путь к файлу: {file_path}")
        
        base_name = filename.split('.')[0]
        logger.debug(f"Базовое имя файла: {base_name}")
        
        if ',' in base_name:
            clean_name = base_name.split(' (')[0]
            logger.debug(f"Файл содержит несколько контейнеров, базовое имя: {clean_name}")
            # Разделяем по запятой и удаляем пробелы
            all_containers = [c.strip() for c in clean_name.split(',')]
            first_container = all_containers[0]
            logger.debug(f"Контейнеры в файле: {all_containers}, первый: {first_container}")
        else:
            # Если один контейнер
            clean_name = base_name.split(' (')[0]
            first_container = clean_name.strip()
            all_containers = [first_container]
            logger.debug(f"Файл содержит один контейнер: {first_container}")
            
        log(f"Контейнеры в файле {filename}: {all_containers}")
        
        # Проверяем первый контейнер для определения unit
        logger.debug(f"Поиск данных для первого контейнера: {first_container}")
        container_data = data_manager.get_container_data(first_container)
        
        if container_data:
            logger.debug(f"Данные найдены для контейнера {first_container}: {container_data}")
            
            company = container_data["company"]
            if company == "GRAND-TRADE":
                unit_value = container_data["order"] or "UNKNOWN_ORDER"
                logger.debug(f"Компания GRAND-TRADE, используем order: {unit_value}")
            else:
                unit_value = container_data["bill"] or "UNKNOWN_BILL"
                logger.debug(f"Компания {company}, используем bill: {unit_value}")
            
            log(f"Файл {filename} связан с ключом: {unit_value}")

            if unit_value not in processed_units:
                processed_units[unit_value] = []
                logger.debug(f"Создан новый unit: {unit_value}")

            vessel_name = container_data["vessel"]
            arrival_date = container_data["date"]
            logger.debug(f"Данные судна: {vessel_name}, дата: {arrival_date}")
            
            # Оставляем только дату, убираем время, приводим к формату dd.mm.YYYY
            try:
                # Попытка распарсить дату в формате YYYY-MM-DD
                logger.debug(f"Парсинг даты: {arrival_date}")
                date_obj = datetime.strptime(arrival_date.split()[0], "%Y-%m-%d")
                arrival_date_str = date_obj.strftime("%d.%m.%Y")
                logger.debug(f"Дата успешно распарсена: {arrival_date} -> {arrival_date_str}")
            except Exception as e:
                # Если не удалось, просто убираем время и запрещённые символы
                logger.warning(f"Не удалось распарсить дату '{arrival_date}': {e}")
                arrival_date_str = re.sub(r"[\\/:*?<>|\"]", "_", arrival_date.split()[0])
                logger.debug(f"Используем очищенную дату: {arrival_date_str}")
            
            # Формируем имя папки, оставляя vessel_name как есть, только дату приводим к формату
            folder_name = f"{vessel_name} {arrival_date_str}"
            logger.debug(f"Исходное имя папки: {folder_name}")
            
            folder_name = re.sub(r"[\\/:*?<>|\"]", "_", folder_name)
            logger.debug(f"Очищенное имя папки: {folder_name}")
            
            folder_path = os.path.join(output_folder, folder_name)
            logger.debug(f"Полный путь к папке: {folder_path}")
            
            if not os.path.exists(folder_path):
                logger.info(f"Создание папки: {folder_path}")
                os.makedirs(folder_path)
                log(f"Создана папка: {folder_path}")
            else:
                logger.debug(f"Папка уже существует: {folder_path}")
            
            processed_units[unit_value].append((file_path, folder_path, all_containers))
            logger.debug(f"Файл {filename} добавлен в unit {unit_value}")
            
        else:
            logger.warning(f"Контейнер {first_container} отсутствует в данных Excel")
            log(f"Контейнер {first_container} отсутствует в данных")
        
        if progress_callback:
            progress_callback(index, total_files)

    logger.info(f"Обработка PDF файлов завершена: {len(processed_units)} units")

    # Создание объединённых PDF
    total_units = len(processed_units)
    logger.info(f"Начало создания объединённых PDF для {total_units} units")
    
    for unit_index, (unit_value, files_info) in enumerate(processed_units.items(), 1):
        # Проверяем остановку
        check_stop()
        
        logger.debug(f"Обработка unit {unit_index}/{total_units}: {unit_value}")
        logger.debug(f"Файлы в unit: {files_info}")
        
        folders = {}
        for file_path, folder_path, containers in files_info:
            if folder_path not in folders:
                folders[folder_path] = []
                logger.debug(f"Создан новый список для папки: {folder_path}")
            folders[folder_path].append((file_path, containers))
            logger.debug(f"Файл {os.path.basename(file_path)} добавлен в папку {folder_path}")
        
        logger.debug(f"Папки для unit {unit_value}: {list(folders.keys())}")
        
        for folder_path, files_data in folders.items():
            logger.debug(f"Обработка папки: {folder_path}")
            
            # Собираем все контейнеры из файлов
            actual_containers = []
            for file_path, containers in files_data:
                actual_containers.extend(containers)
                logger.debug(f"Добавлены контейнеры из файла {os.path.basename(file_path)}: {containers}")
            
            actual_containers = sorted(list(set(actual_containers)))
            logger.debug(f"Уникальные контейнеры в папке: {actual_containers}")
            
            # Получаем все ожидаемые контейнеры для данного unit
            expected_containers = sorted(data_manager.get_containers_by_unit(unit_value))
            logger.debug(f"Ожидаемые контейнеры для unit {unit_value}: {expected_containers}")

            # Логируем для проверки
            log(f"Обработка unit: {unit_value}")
            log(f"Ожидаемые контейнеры: {expected_containers}")
            log(f"Фактические контейнеры: {actual_containers}")
            
            # Получаем данные для формирования имени файла
            if actual_containers:
                container_data = data_manager.get_container_data(actual_containers[0])
                company = container_data["company"]
                if company == "GRAND-TRADE":
                    display_value = container_data["order"]
                else:
                    display_value = container_data["bill"]
                logger.debug(f"Значение для отображения: {display_value} (компания: {company})")
            else:
                logger.warning(f"Нет контейнеров для unit {unit_value}")
                continue
            
            # Формируем имя файла
            if set(actual_containers) == set(expected_containers):
                new_name = f"{display_value} {company}.pdf"
                logger.debug(f"Все контейнеры совпадают, простое имя: {new_name}")
            else:
                new_name = f"{display_value} {company} ({', '.join(actual_containers)}).pdf"
                logger.debug(f"Контейнеры не совпадают, расширенное имя: {new_name}")

            new_name = get_unique_filename(folder_path, new_name)
            new_path = os.path.join(folder_path, new_name)
            logger.debug(f"Финальное имя файла: {new_name}")
            logger.debug(f"Полный путь: {new_path}")
            
            # Создаем объединенный PDF
            logger.info(f"Создание объединённого PDF: {new_name}")
            merger = PdfMerger()
            
            for file_path, _ in files_data:
                # Проверяем остановку
                check_stop()
                
                logger.debug(f"Добавление файла в PDF: {os.path.basename(file_path)}")
                merger.append(file_path)
                log(f"Файл {os.path.basename(file_path)} добавлен в объединенный PDF")

            logger.debug(f"Запись объединённого PDF: {new_path}")
            merger.write(new_path)
            merger.close()
            logger.info(f"PDF успешно создан: {new_name}")
            log(f"Создан файл: {new_name}")
            
            if progress_callback:
                progress_callback(unit_index, total_units)

    logger.info("Операция организации завершена успешно")
    log("Обработка завершена.")