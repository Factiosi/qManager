import os
import re
import logging
from datetime import datetime
from PyPDF2 import PdfMerger

from src.utils_data_manager import DataManager
from src.utils_common import get_unique_filename

logger = logging.getLogger(__name__)


def _sanitize_filename(name: str) -> str:
    name = re.sub(r"[\\/:*?<>|\"]", "_", name)
    name = name.rstrip(" .")
    return name or "file"


def _format_containers_for_filename(containers, max_items: int = 6) -> str:
    containers = list(containers or [])
    if not containers:
        return ""
    if len(containers) <= max_items:
        return ", ".join(containers)
    head = ", ".join(containers[:max_items])
    tail_count = len(containers) - max_items
    return f"{head} +{tail_count}"


def _shrink_filename_to_fit(folder_path: str, filename: str, max_path_len: int = 240) -> str:
    filename = _sanitize_filename(filename)
    full = os.path.join(folder_path, filename)
    if len(full) <= max_path_len:
        return filename

    name, ext = os.path.splitext(filename)
    over = len(full) - max_path_len
    keep = max(20, len(name) - over - 3)
    name = name[:keep].rstrip(" .")
    return _sanitize_filename(f"{name}...{ext}")


def _load_data(data_manager, mode, excel_path, filter_mode, filter_date_from, filter_date_to, log_callback):
    if mode == "sheets":
        log_callback("Загрузка данных из Google Sheets...")
        try:
            data_manager.load_sheets_data(
                filter_mode=filter_mode,
                filter_date_from=filter_date_from,
                filter_date_to=filter_date_to,
                log_callback=log_callback
            )
            log_callback("Данные из Google Sheets успешно загружены")
            return True
        except Exception as e:
            error_msg = f"Ошибка при загрузке Google Sheets: {e}"
            logger.error(error_msg, exc_info=True)
            log_callback(error_msg)
            return False
    elif excel_path and os.path.exists(excel_path):
        log_callback("Чтение файла Excel...")
        try:
            data_manager.load_excel_data(
                excel_path,
                filter_mode=filter_mode,
                filter_date_from=filter_date_from,
                filter_date_to=filter_date_to
            )
            log_callback("Данные из Excel успешно загружены")
            return True
        except Exception as e:
            error_msg = f"Ошибка при загрузке Excel: {e}"
            logger.error(error_msg, exc_info=True)
            log_callback(error_msg)
            return False
    else:
        error_msg = f"Не указан путь к Excel-файлу или файл не найден: {excel_path}"
        logger.error(error_msg)
        log_callback(error_msg)
        return False


def _parse_filename_containers(filename):
    base_name = filename.split('.')[0]
    clean_name = base_name.split(' (')[0]
    if ',' in base_name:
        all_containers = [c.strip() for c in clean_name.split(',')]
    else:
        all_containers = [clean_name.strip()]
    return all_containers


def _get_unit_value(container_data, mode, merge_mode):
    if mode == "sheets":
        return container_data.get("bill") or "UNKNOWN_BILL"
    
    merge_by_bill = (str(merge_mode).lower() == "bl")
    if merge_by_bill:
        return container_data.get("bill") or "UNKNOWN_BILL"
    
    order = container_data.get("order") or ""
    vessel = container_data.get("vessel") or ""
    if order and vessel:
        return f"{order}|{vessel}"
    return order or "UNKNOWN_ORDER"


def _format_folder_name(mode, vessel_name, arrival_date, voyage):
    if mode == "sheets":
        if voyage:
            return f"{vessel_name} {voyage.replace('/', '-')}"
        return vessel_name
    
    try:
        date_obj = datetime.strptime(arrival_date.split()[0], "%Y-%m-%d")
        arrival_date_str = date_obj.strftime("%d.%m.%Y")
    except Exception:
        arrival_date_str = re.sub(r"[\\/:*?<>|\"]", "_", arrival_date.split()[0] if arrival_date else "")
    
    return f"{vessel_name} {arrival_date_str}"


def _group_pdfs_by_unit(input_folder, output_folder, data_manager, mode, merge_mode, log_callback, progress_callback, worker):
    def check_stop():
        if worker and hasattr(worker, 'check_stop'):
            worker.check_stop()
    
    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith(".pdf")]
    total_files = len(pdf_files)
    
    if total_files == 0:
        log_callback("PDF файлы не найдены во входной папке")
        return {}
    
    processed_units = {}
    
    for index, filename in enumerate(pdf_files, 1):
        check_stop()
        log_callback(f"Обнаружен файл: {filename}")
        
        file_path = os.path.join(input_folder, filename)
        all_containers = _parse_filename_containers(filename)
        first_container = all_containers[0]
        
        log_callback(f"Контейнеры в файле {filename}: {all_containers}")
        
        container_data = data_manager.get_container_data(first_container)
        
        if container_data:
            unit_value = _get_unit_value(container_data, mode, merge_mode)
            log_callback(f"Файл {filename} связан с ключом: {unit_value}")
            
            if unit_value not in processed_units:
                processed_units[unit_value] = []
            
            vessel_name = container_data.get("vessel") or ""
            arrival_date = container_data.get("date") or ""
            voyage = container_data.get("voyage") or ""
            
            folder_name = _format_folder_name(mode, vessel_name, arrival_date, voyage)
            folder_name = re.sub(r"[\\/:*?<>|\"]", "_", folder_name)
            
            folder_path = os.path.join(output_folder, folder_name)
            
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                log_callback(f"Создана папка: {folder_path}")
            
            processed_units[unit_value].append((file_path, folder_path, all_containers))
        else:
            log_callback(f"Контейнер {first_container} отсутствует в данных")
        
        if progress_callback:
            progress_callback(index, total_files)
    
    return processed_units


def _create_merged_pdfs(processed_units, data_manager, mode, merge_mode, output_folder, log_callback, progress_callback, worker):
    def check_stop():
        if worker and hasattr(worker, 'check_stop'):
            worker.check_stop()
    
    total_units = len(processed_units)
    
    for unit_index, (unit_value, files_info) in enumerate(processed_units.items(), 1):
        check_stop()
        
        folders = {}
        for file_path, folder_path, containers in files_info:
            if folder_path not in folders:
                folders[folder_path] = []
            folders[folder_path].append((file_path, containers))
        
        for folder_path, files_data in folders.items():
            actual_containers = []
            for file_path, containers in files_data:
                actual_containers.extend(containers)
            
            actual_containers = sorted(list(set(actual_containers)))
            expected_containers = sorted(data_manager.get_containers_by_unit(unit_value))
            
            if not expected_containers:
                try:
                    if str(merge_mode).lower() == "bl":
                        norm = str(unit_value).replace(" ", "")
                        expected_containers = sorted([
                            c for c, row in data_manager.latest_container_data.items()
                            if str(row.get("bill") or "").replace(" ", "") == norm
                        ])
                    else:
                        unit_str = str(unit_value)
                        if '|' in unit_str:
                            parts = unit_str.split('|', 1)
                            order_part = parts[0] if len(parts) > 0 else ""
                            vessel_part = parts[1] if len(parts) > 1 else ""
                            expected_containers = sorted([
                                c for c, row in data_manager.latest_container_data.items()
                                if str(row.get("order") or "") == order_part and str(row.get("vessel") or "") == vessel_part
                            ])
                        else:
                            expected_containers = sorted([
                                c for c, row in data_manager.latest_container_data.items()
                                if str(row.get("order") or "") == unit_str
                            ])
                except Exception:
                    expected_containers = []
            
            log_callback(f"Обработка unit: {unit_value}")
            log_callback(f"Ожидаемые контейнеры: {expected_containers}")
            log_callback(f"Фактические контейнеры: {actual_containers}")
            
            if not actual_containers:
                continue
            
            container_data = data_manager.get_container_data(actual_containers[0])
            merge_by_bill = (mode == "sheets" or str(merge_mode).lower() == "bl")
            
            if merge_by_bill:
                display_value = container_data.get("bill")
            else:
                display_value = container_data.get("order") or ""
            
            company = container_data.get("company", "")
            
            if set(actual_containers) == set(expected_containers):
                new_name = f"{display_value} {company}.pdf"
            else:
                containers_part = _format_containers_for_filename(actual_containers, max_items=6)
                new_name = f"{display_value} {company} ({containers_part}).pdf"
            
            new_name = _shrink_filename_to_fit(folder_path, new_name, max_path_len=240)
            new_name = get_unique_filename(folder_path, new_name)
            new_path = os.path.join(folder_path, new_name)
            
            merger = PdfMerger()
            for file_path, _ in files_data:
                check_stop()
                merger.append(file_path)
                log_callback(f"Файл {os.path.basename(file_path)} добавлен в объединенный PDF")
            
            merger.write(new_path)
            merger.close()
            log_callback(f"Создан файл: {new_name}")
            
            if progress_callback:
                progress_callback(unit_index, total_units)


def organize_pdfs(input_folder, output_folder, excel_path=None, log_callback=None, progress_callback=None, mode="logos", worker=None, merge_mode: str = "order", filter_mode='unlimited', filter_date_from=None, filter_date_to=None, debug_mode=False):
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            logging.info(message)
    
    log("Начала операция организации")
    
    if not os.path.exists(input_folder):
        error_msg = f"Входная папка не существует: {input_folder}"
        logger.error(error_msg)
        log(error_msg)
        return
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        log(f"Создана выходная папка: {output_folder}")
    
    data_manager = DataManager(mode=mode, merge_mode=merge_mode)
    
    if not _load_data(data_manager, mode, excel_path, filter_mode, filter_date_from, filter_date_to, log):
        return
    
    data_manager.process_data()
    log(f"Обработано {len(data_manager.latest_container_data)} уникальных контейнеров")
    
    processed_units = _group_pdfs_by_unit(input_folder, output_folder, data_manager, mode, merge_mode, log, progress_callback, worker)
    
    if not processed_units:
        return
    
    _create_merged_pdfs(processed_units, data_manager, mode, merge_mode, output_folder, log, progress_callback, worker)
    
    log("Обработка завершена.")
