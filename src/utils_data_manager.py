from datetime import datetime, timedelta
import pandas as pd
import logging

# Маппинг столбцов Google Sheets (индексы)
SHEETS_COLUMN_INDICES = {
    'date': 3,      # Столбец D
    'vessel': 5,    # Столбец F
    'voyage': 6,    # Столбец G
    'bill': 8,      # Столбец I
    'container': 14,# Столбец O
    'company': 18   # Столбец S
}

class DataManager:
    EXCEL_COLUMN_MAPPINGS = {
        'container': ['Номер конт / тс'],
        'order': ['Номер заказа (заказ)'],
        'vessel': ['Судно / номер ТС (поставка)'],
        'date': ['Факт дата прибытия порт/свх (поставка)'],
        'bill': ['Коносамент / CMR (поставка)']
    }
    EXCEL_COLUMN_MAPPINGS_REPORT = {
        'container': ['Контейнер'],
        'order': ['Номер Заказа'],
        'vessel': ['Судно'],
        'date': ['Дата прибытия'],
        'bill': ['Коносамент']
    }

    def __init__(self, mode="logos", merge_mode: str = "order"):
        """Инициализация менеджера данных
        mode: режим чтения Excel (logos/report/sheets)
        merge_mode: ключ объединения контейнеров (order/bl)
        """
        self.mode = mode
        self.merge_mode = (str(merge_mode).lower() if merge_mode else "order")
        self.latest_container_data = {}
        self.containers_by_unit = {}
        self.logger = logging.getLogger(f'DataManager.{mode}')

    def _find_column_index(self, columns, possible_names):
        """Поиск индекса столбца"""
        self.logger.debug(f"Поиск столбца среди возможных имен: {possible_names}")
        for name in possible_names:
            matches = [i for i, col in enumerate(columns) if str(col).strip().lower() == name.lower()]
            if matches:
                self.logger.debug(f"Найден столбец '{name}' по индексу {matches[0]}")
                return matches[0]
        self.logger.warning(f"Столбец не найден для имен: {possible_names}")
        return None

    def _parse_date(self, date_str):
        """Парсит строку с датой"""
        self.logger.debug(f"Парсинг даты: '{date_str}'")
        formats = [
            "%d.%m.%Y",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y-%m-%d %H:%M:%S",  # поддержка формата с временем
            "%d.%m.%Y %H:%M:%S"
        ]
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(str(date_str).strip(), fmt)
                self.logger.debug(f"Дата успешно распарсена в формате '{fmt}': {parsed_date}")
                return parsed_date
            except ValueError:
                self.logger.debug(f"Формат '{fmt}' не подходит для '{date_str}'")
                continue
        self.logger.warning(f"Не удалось распарсить дату: '{date_str}'")
        return None

    def _extract_container_number(self, container_str):
        """Извлекает номер контейнера"""
        self.logger.debug(f"Извлечение номера контейнера из: '{container_str}'")
        if not container_str or pd.isna(container_str):
            self.logger.debug("Контейнер пустой или NaN")
            return None
        digits = ''.join(c for c in str(container_str) if c.isdigit())
        if len(digits) >= 7:
            result = digits[-7:]
            self.logger.debug(f"Извлечен номер контейнера: {result}")
            return result
        self.logger.debug(f"Недостаточно цифр в номере контейнера: {len(digits)} < 7")
        return None

    def load_excel_data(self, excel_path, filter_mode='unlimited', filter_date_from=None, filter_date_to=None):
        """Загружает данные из Excel
        
        Args:
            excel_path: путь к Excel файлу
            filter_mode: режим фильтрации ('unlimited' или 'period')
            filter_date_from: дата начала периода (datetime или None)
            filter_date_to: дата конца периода (datetime или None)
        """
        self.logger.info(f"Начало загрузки Excel файла: {excel_path}")
        try:
            with pd.ExcelFile(excel_path) as excel_file:
                self.logger.debug(f"Excel файл открыт, листы: {excel_file.sheet_names}")
                
                df = pd.read_excel(excel_file)
                self.logger.info(f"Excel прочитан: {len(df)} строк × {len(df.columns)} столбцов")
                self.logger.debug(f"Заголовки столбцов: {list(df.columns)}")
                
                columns = df.columns.tolist()
                column_indices = {}
                if self.mode == "report":
                    mappings = self.EXCEL_COLUMN_MAPPINGS_REPORT
                    self.logger.debug("Используется режим 'Отчёт'")
                else:
                    mappings = self.EXCEL_COLUMN_MAPPINGS
                    self.logger.debug("Используется режим 'Logos'")
                
                for key, possible_names in mappings.items():
                    idx = self._find_column_index(columns, possible_names)
                    if idx is None:
                        raise ValueError(f"Не найден столбец для {key}. Возможные имена: {possible_names}")
                    column_indices[key] = idx
                    self.logger.debug(f"Столбец '{key}' найден по индексу {idx}")
                
                # Детальное логирование для режима отладки
                if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                    logging.info(f"Начинаем обработку {len(df)} строк Excel")
                    logging.info(f"Найдены столбцы: {column_indices}")
                
                # Обработка данных
                valid_rows = 0
                valid_containers = 0
                start_row = None
                end_row = None
                
                if self.mode == "report":
                    # Для режима "Отчёт" читаем от новых к старым с фильтрацией по датам
                    filter_info = "период" if filter_mode == 'period' else "последние 60 дней"
                    if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                        logging.info(f"Режим 'Отчёт': читаем {filter_info}")
                    
                    # Итерируемся в обратном порядке для поиска последних данных
                    for i in range(len(df) - 1, -1, -1):
                        row = df.iloc[i]
                        date_str = str(row.iloc[column_indices['date']])
                        
                        if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                            logging.debug(f"Обработка строки {i+1}")
                        
                        parsed_date = self._parse_date(date_str)
                        if parsed_date:
                            # Фильтрация по датам
                            if filter_mode == 'period':
                                # Нормализуем даты для сравнения (только дата без времени)
                                parsed_date_normalized = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
                                if filter_date_from:
                                    filter_date_from_normalized = filter_date_from.replace(hour=0, minute=0, second=0, microsecond=0)
                                    if parsed_date_normalized < filter_date_from_normalized:
                                        if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                                            logging.debug(f"Строка {i+1}: дата {parsed_date} раньше начала периода, пропускаем")
                                        continue
                                if filter_date_to:
                                    filter_date_to_normalized = filter_date_to.replace(hour=0, minute=0, second=0, microsecond=0)
                                    if parsed_date_normalized > filter_date_to_normalized:
                                        if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                                            logging.debug(f"Строка {i+1}: дата {parsed_date} позже конца периода, пропускаем")
                                        continue
                            else:
                                # Проверяем, не слишком ли старая дата (60 дней)
                                days_ago = (datetime.now() - parsed_date).days
                                if days_ago > 60:
                                    if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                                        logging.info(f"Строка {i+1}: дата {parsed_date} слишком старая, прекращаем обработку")
                                    break
                            
                            if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                                logging.debug(f"Строка {i+1}: дата {parsed_date} подходит")
                            
                            # Обрабатываем строку
                            container_str = str(row.iloc[column_indices['container']])
                            container_number = self._extract_container_number(container_str)
                            
                            if container_number:
                                if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                                    logging.debug(f"Строка {i+1}: номер контейнера '{container_str}' -> суффикс '{container_number}'")
                                
                                # Извлекаем данные
                                order = str(row.iloc[column_indices['order']]) if column_indices['order'] is not None else None
                                vessel = str(row.iloc[column_indices['vessel']]) if column_indices['vessel'] is not None else None
                                date = str(row.iloc[column_indices['date']]) if column_indices['date'] is not None else None
                                bill = str(row.iloc[column_indices['bill']]) if column_indices['bill'] is not None else None
                                if bill is not None:
                                    bill = bill.replace(" ", "")
                                
                                if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                                    logging.debug(f"Строка {i+1}: order='{order}', vessel='{vessel}', date='{date}', bill='{bill}'")
                                
                                # Группируем по суффиксу контейнера
                                if container_number not in self.containers_by_unit:
                                    self.containers_by_unit[container_number] = []
                                    if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                                        logging.debug(f"Создан новый список для суффикса '{container_number}'")
                                
                                self.containers_by_unit[container_number].append({
                                    'container': container_str,
                                    'order': order,
                                    'vessel': vessel,
                                    'date': date,
                                    'bill': bill
                                })
                                
                                if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                                    logging.debug(f"Строка {i+1}: успешно обработана, добавлена в суффикс '{container_number}'")
                                
                                valid_rows += 1
                                valid_containers += 1
                                
                                if start_row is None:
                                    start_row = i + 1
                                end_row = i + 1
                            else:
                                if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                                    logging.debug(f"Строка {i+1}: невалидный номер контейнера")
                        else:
                            if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                                logging.debug(f"Строка {i+1}: не удалось распарсить дату")
                    
                    if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                        logging.info(f"Обработка завершена: {valid_rows} строк, {valid_containers} контейнеров")
                    
                    # Очищаем кэш
                    self.latest_container_data.clear()
                    if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                        logging.debug("Очищен кэш latest_container_data")
                    
                    # Обрабатываем суффиксы
                    for suffix, containers in self.containers_by_unit.items():
                        if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                            logging.debug(f"Обработка суффикса '{suffix}': {len(containers)} записей")
                        
                        # Берем первый контейнер для каждого суффикса (самый свежий, т.к. читаем от новых к старым)
                        latest_container = containers[0]
                        self.latest_container_data[latest_container['container']] = {
                            'company': 'GRAND-TRADE' if latest_container['order'] else 'OTHER',
                            'order': latest_container['order'],
                            'vessel': latest_container['vessel'],
                            'date': latest_container['date'],
                            'bill': latest_container['bill']
                        }
                    
                    if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                        logging.info(f"Данные сохранены: {len(self.latest_container_data)} уникальных контейнеров")
                    
                    return {
                        'total_rows': len(df),
                        'valid_rows_range': (start_row, end_row),
                        'valid_containers': valid_containers
                    }
                else:
                    # Для режима "Logos" - обратный порядок с фильтрацией по датам
                    filter_info = "период" if filter_mode == 'period' else "последние 60 дней"
                    if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                        logging.info(f"Режим 'Logos': читаем от новых к старым, {filter_info}")
                    
                    # Итерируемся в обратном порядке для поиска последних данных
                    for i in range(len(df) - 1, -1, -1):
                        row = df.iloc[i]
                        date_str = str(row.iloc[column_indices['date']])
                        
                        if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                            logging.debug(f"Обработка строки {i+1}")
                        
                        parsed_date = self._parse_date(date_str)
                        if parsed_date:
                            # Фильтрация по датам
                            if filter_mode == 'period':
                                # Проверяем, попадает ли дата в указанный период
                                if filter_date_from and parsed_date < filter_date_from:
                                    if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                                        logging.debug(f"Строка {i+1}: дата {parsed_date} раньше начала периода, пропускаем")
                                    continue
                                if filter_date_to and parsed_date > filter_date_to:
                                    if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                                        logging.debug(f"Строка {i+1}: дата {parsed_date} позже конца периода, пропускаем")
                                    continue
                            else:
                                # Проверяем, не слишком ли старая дата (60 дней)
                                days_ago = (datetime.now() - parsed_date).days
                                if days_ago > 60:
                                    if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                                        logging.info(f"Строка {i+1}: дата {parsed_date} слишком старая, прекращаем обработку")
                                    break
                        
                        container_str = str(row.iloc[column_indices['container']])
                        container_number = self._extract_container_number(container_str)
                        
                        if container_number:
                            if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                                logging.debug(f"Строка {i+1}: номер контейнера '{container_str}' -> суффикс '{container_number}'")
                            
                            # Извлекаем данные
                            order = str(row.iloc[column_indices['order']]) if column_indices['order'] is not None else None
                            vessel = str(row.iloc[column_indices['vessel']]) if column_indices['vessel'] is not None else None
                            date = str(row.iloc[column_indices['date']]) if column_indices['date'] is not None else None
                            bill = str(row.iloc[column_indices['bill']]) if column_indices['bill'] is not None else None
                            if bill is not None:
                                bill = bill.replace(" ", "")
                            
                            if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                                logging.debug(f"Строка {i+1}: order='{order}', vessel='{vessel}', date='{date}', bill='{bill}'")
                            
                            # Группируем по суффиксу контейнера
                            if container_number not in self.containers_by_unit:
                                self.containers_by_unit[container_number] = []
                                if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                                    logging.debug(f"Создан новый список для суффикса '{container_number}'")
                            
                            self.containers_by_unit[container_number].append({
                                'container': container_str,
                                'order': order,
                                'vessel': vessel,
                                'date': date,
                                'bill': bill
                            })
                            
                            if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                                logging.debug(f"Строка {i+1}: успешно обработана, добавлена в суффикс '{container_number}'")
                            
                            valid_rows += 1
                            valid_containers += 1
                            
                            if start_row is None:
                                start_row = i + 1
                            end_row = i + 1
                        else:
                            if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                                logging.debug(f"Строка {i+1}: невалидный номер контейнера")
                
                if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                    logging.info(f"Обработка завершена: {valid_rows} строк, {valid_containers} контейнеров")
                
                # Очищаем кэш
                self.latest_container_data.clear()
                if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                    logging.debug("Очищен кэш latest_container_data")
                    
                    # Обрабатываем суффиксы
                    for suffix, containers in self.containers_by_unit.items():
                        if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                            logging.debug(f"Обработка суффикса '{suffix}': {len(containers)} записей")
                        
                        # Берем первый контейнер для каждого суффикса (самый свежий, т.к. читаем от новых к старым)
                        latest_container = containers[0]
                        self.latest_container_data[latest_container['container']] = {
                            'company': 'GRAND-TRADE' if latest_container['order'] else 'OTHER',
                            'order': latest_container['order'],
                            'vessel': latest_container['vessel'],
                            'date': latest_container['date'],
                            'bill': latest_container['bill']
                        }
                    
                    if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                        logging.info(f"Данные сохранены: {len(self.latest_container_data)} уникальных контейнеров")
                    
                return {
                    'total_rows': len(df),
                    'valid_rows_range': (start_row, end_row),
                    'valid_containers': valid_containers
                }
                    
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке Excel: {e}", exc_info=True)
            raise

    def load_sheets_data(self, credentials_file=None, spreadsheet_id=None, range_name=None, filter_mode='unlimited', filter_date_from=None, filter_date_to=None):
        """Загружает данные из Google Sheets
        
        Args:
            credentials_file: путь к файлу credentials (опционально, используется хардкод)
            spreadsheet_id: ID таблицы (опционально, используется хардкод)
            range_name: диапазон ячеек (опционально, используется хардкод)
            filter_mode: режим фильтрации ('unlimited' или 'period')
            filter_date_from: дата начала периода (datetime или None)
            filter_date_to: дата конца периода (datetime или None)
        
        Returns:
            dict: статистика загрузки
        """
        self.logger.info("Начало загрузки данных из Google Sheets")
        try:
            from src.google_sheets_manager import GoogleSheetsManager
            
            # Используем хардкод параметров, если не указаны
            manager = GoogleSheetsManager(credentials_file, spreadsheet_id)
            data = manager.get_data(range_name)
            
            self.logger.info(f"Получено {len(data)} строк из Google Sheets")
            
            # Очищаем кэш
            self.latest_container_data.clear()
            
            valid_containers = 0
            filter_info = "период" if filter_mode == 'period' else "последние 60 дней"
            self.logger.info(f"Google Sheets: читаем от новых к старым, {filter_info}")
            
            # Обрабатываем строки в обратном порядке (с конца к началу)
            # Это гарантирует, что при дубликатах контейнеров используется последняя запись
            for i in range(len(data) - 1, -1, -1):
                row = data[i]
                row_idx = i + 2  # Диапазон начинается с A2, без заголовков
                try:
                    # Проверяем, что строка достаточно длинная
                    if len(row) <= max(SHEETS_COLUMN_INDICES.values()):
                        self.logger.debug(f"Строка {row_idx}: недостаточно данных, пропускаем")
                        continue
                    
                    # Извлекаем данные по индексам
                    container = str(row[SHEETS_COLUMN_INDICES['container']]).strip() if len(row) > SHEETS_COLUMN_INDICES['container'] else ""
                    if not container:
                        continue
                    
                    # Пропускаем, если контейнер уже обработан (т.к. идём с конца, первая встреча = последняя запись)
                    if container in self.latest_container_data:
                        self.logger.debug(f"Строка {row_idx}: контейнер '{container}' уже обработан (пропускаем более старую запись)")
                        continue
                    
                    # Извлекаем остальные данные
                    date = str(row[SHEETS_COLUMN_INDICES['date']]).strip() if len(row) > SHEETS_COLUMN_INDICES['date'] else ""
                    vessel = str(row[SHEETS_COLUMN_INDICES['vessel']]).strip() if len(row) > SHEETS_COLUMN_INDICES['vessel'] else ""
                    voyage = str(row[SHEETS_COLUMN_INDICES['voyage']]).strip() if len(row) > SHEETS_COLUMN_INDICES['voyage'] else ""
                    bill = str(row[SHEETS_COLUMN_INDICES['bill']]).strip() if len(row) > SHEETS_COLUMN_INDICES['bill'] else ""
                    company = str(row[SHEETS_COLUMN_INDICES['company']]).strip() if len(row) > SHEETS_COLUMN_INDICES['company'] else ""
                    
                    # Фильтрация по датам
                    if date:
                        parsed_date = self._parse_date(date)
                        if parsed_date:
                            if filter_mode == 'period':
                                # Нормализуем даты для сравнения (только дата без времени)
                                parsed_date_normalized = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
                                if filter_date_from:
                                    filter_date_from_normalized = filter_date_from.replace(hour=0, minute=0, second=0, microsecond=0)
                                    if parsed_date_normalized < filter_date_from_normalized:
                                        self.logger.debug(f"Строка {row_idx}: дата {parsed_date} раньше начала периода, пропускаем")
                                        continue
                                if filter_date_to:
                                    filter_date_to_normalized = filter_date_to.replace(hour=0, minute=0, second=0, microsecond=0)
                                    if parsed_date_normalized > filter_date_to_normalized:
                                        self.logger.debug(f"Строка {row_idx}: дата {parsed_date} позже конца периода, пропускаем")
                                        continue
                            else:
                                # Проверяем, не слишком ли старая дата (60 дней)
                                days_ago = (datetime.now() - parsed_date).days
                                if days_ago > 60:
                                    self.logger.info(f"Строка {row_idx}: дата {parsed_date} слишком старая, прекращаем обработку")
                                    break
                    
                    # Убираем пробелы из коносамента
                    if bill:
                        bill = bill.replace(" ", "")
                    
                    # Конвертируем в формат словаря, совместимый с Excel режимами
                    self.latest_container_data[container] = {
                        'company': company if company else 'OTHER',
                        'order': None,  # Для Google Sheets нет номера заказа
                        'vessel': vessel if vessel else '',
                        'date': date if date else '',
                        'bill': bill if bill else '',
                        'voyage': voyage if voyage else ''  # Дополнительное поле для voyage
                    }
                    
                    valid_containers += 1
                    self.logger.debug(f"Строка {row_idx}: контейнер '{container}' добавлен")
                    
                except Exception as e:
                    self.logger.error(f"Ошибка при обработке строки {row_idx} Google Sheets: {e}")
                    continue
            
            self.logger.info(f"Данные из Google Sheets загружены: {valid_containers} контейнеров")
            
            return {
                'total_rows': len(data),
                'valid_containers': valid_containers
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке Google Sheets: {e}", exc_info=True)
            raise

    def process_data(self):
        """
        Организует контейнеры по юнитам (заказ или коносамент) для дальнейшей обработки.
        """
        self.logger.info("Начало организации контейнеров по юнитам")
        self.containers_by_unit = {}
        
        for container, row in self.latest_container_data.items():
            try:
                self.logger.debug(f"Обработка контейнера '{container}'")
                
                company = row.get("company", "")
                
                # Для режима Google Sheets всегда используем коносамент
                if self.mode == "sheets":
                    unit = row.get("bill") or ""
                else:
                    # Для Excel режимов: bl -> bill; иначе: GRAND-TRADE -> order|vessel, остальные -> bill
                    if self.merge_mode == "bl":
                        unit = row.get("bill")
                    elif company == "GRAND-TRADE":
                        # Для заказов используем комбинацию "заказ|судно" для уникальности в пределах судна
                        order = row.get("order") or ""
                        vessel = row.get("vessel") or ""
                        unit = f"{order}|{vessel}" if order and vessel else order
                    else:
                        unit = row.get("bill")
                
                if not unit:
                    self.logger.debug(f"Контейнер '{container}': unit пустой, пропускаем")
                    continue
                
                if unit not in self.containers_by_unit:
                    self.containers_by_unit[unit] = []
                    self.logger.debug(f"Создан новый unit '{unit}'")
                
                if container not in self.containers_by_unit[unit]:
                    self.containers_by_unit[unit].append(container)
                    self.logger.debug(f"Контейнер '{container}' добавлен в unit '{unit}'")
                else:
                    self.logger.debug(f"Контейнер '{container}' уже есть в unit '{unit}'")
                    
            except Exception as e:
                self.logger.error(f"Ошибка при обработке контейнера '{container}': {e}")
                continue
        
        self.logger.info(f"Организация завершена: {len(self.containers_by_unit)} units")

    def get_container_data(self, container):
        """
        Получить словарь с данными по номеру контейнера.
        Аргументы:
            container (str): Полный номер контейнера.
        Возвращает:
            dict или None: Словарь с данными по контейнеру или None, если не найден.
        """
        self.logger.debug(f"Запрос данных для контейнера '{container}'")
        result = self.latest_container_data.get(container)
        if result:
            self.logger.debug(f"Контейнер '{container}' найден: {result}")
        else:
            self.logger.debug(f"Контейнер '{container}' не найден")
        return result

    def get_containers_by_unit(self, unit):
        """
        Получить список контейнеров, связанных с юнитом (заказом или коносаментом).
        Аргументы:
            unit (str): Идентификатор юнита (заказ или коносамент).
        Возвращает:
            list: Список номеров контейнеров для юнита или пустой список, если не найдено.
        """
        self.logger.debug(f"Запрос контейнеров для unit '{unit}'")
        result = self.containers_by_unit.get(unit)
        if not result:
            # Подстраховка: если по какой‑то причине unit не собран в process_data,
            # вычисляем на лету из latest_container_data, учитывая merge_mode.
            norm = (str(unit) if unit is not None else "")
            norm = norm.replace(" ", "")
            if self.merge_mode == "bl":
                result = [c for c, row in self.latest_container_data.items()
                          if (str(row.get('bill') or '').replace(' ', '')) == norm]
            else:
                # Проверяем, содержит ли unit разделитель "|" (формат "заказ|судно")
                if '|' in norm:
                    parts = norm.split('|', 1)
                    order_part = parts[0] if len(parts) > 0 else ""
                    vessel_part = parts[1] if len(parts) > 1 else ""
                    result = [c for c, row in self.latest_container_data.items()
                              if str(row.get('order') or '') == order_part and str(row.get('vessel') or '') == vessel_part]
                else:
                    # Старый формат без судна (для обратной совместимости)
                    result = [c for c, row in self.latest_container_data.items()
                              if str(row.get('order') or '') == norm]
        self.logger.debug(f"Unit '{unit}': найдено {len(result)} контейнеров: {result}")
        return result
