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

def organize_pdfs(input_folder, output_folder, excel_path=None, log_callback=None, progress_callback=None, mode="logos"):
    """
    Организует PDF-файлы по папкам на основе данных из Excel/Google Sheets.
    :param input_folder: Путь к папке с входными PDF-файлами
    :param output_folder: Путь к папке для сохранения организованных файлов
    :param excel_path: Путь к Excel-файлу (опционально)
    :param log_callback: Функция для логирования сообщений
    :param progress_callback: Функция для отображения прогресса
    """
    if log_callback:
        log_callback("Начата операция организации")
    data_manager = DataManager(mode=mode)
    if excel_path and os.path.exists(excel_path):
        if log_callback:
            log_callback("Чтение файла Excel...")
        try:
            stats = data_manager.load_excel_data(excel_path)
            if log_callback:
                log_callback(f"Всего строк в файле: {stats['total_rows']}")
                if stats['valid_rows_range'][0] and stats['valid_rows_range'][1]:
                    log_callback(f"Валидные строки: {stats['valid_rows_range'][0]}–{stats['valid_rows_range'][1]}")
                log_callback(f"Валидных конейтнеров: {stats['valid_containers']}")
        except Exception as e:
            if log_callback:
                log_callback(f"Ошибка при чтении Excel: {e}")
            return
    else:
        if log_callback:
            log_callback("Не указан путь к Excel-файлу или файл не найден. Операция прервана.")
        return
    data_manager.process_data()
    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith(".pdf")]
    total_files = len(pdf_files)
    processed_folders = set()
    for index, filename in enumerate(pdf_files, 1):
        file_path = os.path.join(input_folder, filename)
        base_name = filename.split('.')[0]
        if ',' in base_name:
            clean_name = base_name.split(' (')[0]
            all_containers = [c.strip() for c in clean_name.split(',')]
            first_container = all_containers[0]
        else:
            clean_name = base_name.split(' (')[0]
            first_container = clean_name.strip()
            all_containers = [first_container]
        container_data = data_manager.get_container_data(first_container)
        if container_data:
            vessel_name = container_data["vessel"]
            arrival_date = container_data["date"]
            # Формат dd.mm.YYYY
            try:
                date_obj = datetime.strptime(arrival_date.split()[0], "%Y-%m-%d")
                arrival_date_str = date_obj.strftime("%d.%m.%Y")
            except Exception:
                arrival_date_str = re.sub(r"[\\/:*?<>|\"]", "_", arrival_date.split()[0])
            folder_name = f"{vessel_name} {arrival_date_str}"
            folder_name = re.sub(r"[\\/:*?<>|\"]", "_", folder_name)
            folder_path = os.path.join(output_folder, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            processed_folders.add(folder_name)
        if progress_callback:
            progress_callback(index, total_files)
    if log_callback:
        log_callback(f"Всего файлов организовано: {total_files}")
        if processed_folders:
            log_callback("Судозаходы:\n" + "\n".join(sorted(processed_folders)))
        log_callback("Операция завершена")