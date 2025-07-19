"""
Модуль для организации PDF-файлов по данным из Excel/Google Sheets.
Группирует и объединяет файлы по контейнерам, создаёт итоговые папки и PDF.
"""
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

def get_unique_filename(base_path, original_name):
    """
    Генерирует уникальное имя файла, добавляя номер копии в скобках, если файл уже существует.
    :param base_path: str
    :param original_name: str
    :return: str
    """
    if not os.path.exists(base_path):
        return original_name
    
    name, ext = os.path.splitext(original_name)
    counter = 2
    new_name = original_name
    
    while os.path.exists(os.path.join(base_path, new_name)):
        new_name = f"{name} ({counter}){ext}"
        counter += 1
    
    return new_name

def organize_pdfs(input_folder, output_folder, excel_path=None, log_callback=None, progress_callback=None):
    """
    Организует PDF-файлы по папкам на основе данных из Excel/Google Sheets.
    :param input_folder: Путь к папке с входными PDF-файлами
    :param output_folder: Путь к папке для сохранения организованных файлов
    :param excel_path: Путь к Excel-файлу (опционально)
    :param log_callback: Функция для логирования сообщений
    :param progress_callback: Функция для отображения прогресса
    """
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            logging.info(message)

    # Инициализация менеджера данных
    data_manager = DataManager()

    # Загрузка данных из источников
    if excel_path and os.path.exists(excel_path):
        log(f"Загрузка данных из Excel: {excel_path}")
        try:
            data_manager.load_excel_data(excel_path)
            log("Данные из Excel успешно загружены")
        except Exception as e:
            log(f"Ошибка при загрузке Excel: {e}")
            return
    else:
        log("Не указан путь к Excel-файлу или файл не найден. Операция прервана.")
        return

    # Обработка загруженных данных
    data_manager.process_data()
    log(f"Обработано {len(data_manager.latest_container_data)} уникальных контейнеров")

    # Обработка PDF-файлов
    processed_units = {}
    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith(".pdf")]
    total_files = len(pdf_files)
    
    for index, filename in enumerate(pdf_files, 1):
        log(f"Обнаружен файл: {filename}")
        file_path = os.path.join(input_folder, filename)
        
        # Извлекаем номера контейнеров из имени файла
        base_name = filename.split('.')[0]
        
        # Получаем все контейнеры из имени файла
        if ',' in base_name:
            # Удаляем возможные скобки и их содержимое
            clean_name = base_name.split(' (')[0]
            # Разделяем по запятой и удаляем пробелы
            all_containers = [c.strip() for c in clean_name.split(',')]
            first_container = all_containers[0]
        else:
            # Если один контейнер
            clean_name = base_name.split(' (')[0]
            first_container = clean_name.strip()
            all_containers = [first_container]
            
        log(f"Контейнеры в файле {filename}: {all_containers}")
        
        # Проверяем первый контейнер для определения unit
        container_data = data_manager.get_container_data(first_container)
        if container_data:
            company = container_data["company"]
            if company == "GRAND-TRADE":
                unit_value = container_data["order"] or "UNKNOWN_ORDER"
            else:
                unit_value = container_data["bill"] or "UNKNOWN_BILL"
            
            log(f"Файл {filename} связан с ключом: {unit_value}")

            if unit_value not in processed_units:
                processed_units[unit_value] = []

            vessel_name = container_data["vessel"]
            arrival_date = container_data["date"]
            # Оставляем только дату, убираем время, приводим к формату DD-MM-YYYY
            try:
                # Попытка распарсить дату
                date_obj = datetime.strptime(arrival_date.split()[0], "%d-%m-%Y")
                arrival_date_str = date_obj.strftime("%d-%m-%Y")
            except Exception:
                # Если не удалось, просто убираем время и запрещённые символы
                arrival_date_str = re.sub(r"[\\/:*?<>|\"]", "_", arrival_date.split()[0])
            folder_name = f"{vessel_name} {arrival_date_str}"
            folder_name = re.sub(r"[\\/:*?<>|\"]", "_", folder_name)
            folder_path = os.path.join(output_folder, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                log(f"Создана папка: {folder_path}")
            processed_units[unit_value].append((file_path, folder_path, all_containers))
        else:
            log(f"Контейнер {first_container} отсутствует в данных")
        
        if progress_callback:
            progress_callback(index, total_files)

    # Создание объединённых PDF
    total_units = len(processed_units)
    for unit_index, (unit_value, files_info) in enumerate(processed_units.items(), 1):
        folders = {}
        for file_path, folder_path, containers in files_info:
            if folder_path not in folders:
                folders[folder_path] = []
            folders[folder_path].append((file_path, containers))
        
        for folder_path, files_data in folders.items():
            # Собираем все контейнеры из файлов
            actual_containers = []
            for _, containers in files_data:
                actual_containers.extend(containers)
            actual_containers = sorted(list(set(actual_containers)))
            
            # Получаем все ожидаемые контейнеры для данного unit
            expected_containers = sorted(data_manager.get_containers_by_unit(unit_value))

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
            else:
                continue
            
            # Формируем имя файла
            if set(actual_containers) == set(expected_containers):
                new_name = f"{display_value} {company}.pdf"
            else:
                new_name = f"{display_value} {company} ({', '.join(actual_containers)}).pdf"

            new_name = get_unique_filename(folder_path, new_name)
            new_path = os.path.join(folder_path, new_name)
            
            # Создаем объединенный PDF
            merger = PdfMerger()
            for file_path, _ in files_data:
                merger.append(file_path)
                log(f"Файл {os.path.basename(file_path)} добавлен в объединенный PDF")

            merger.write(new_path)
            merger.close()
            log(f"Создан файл: {new_name}")
            
            if progress_callback:
                progress_callback(unit_index, total_units)

    log("Обработка завершена.")