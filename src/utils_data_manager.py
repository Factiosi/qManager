from datetime import datetime, timedelta
import pandas as pd
import logging

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

    def __init__(self, mode="logos"):
        """Инициализация менеджера данных"""
        self.mode = mode
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

    def load_excel_data(self, excel_path):
        """Загружает данные из Excel"""
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
                    # Для режима "Отчёт" читаем только последние 40 дней
                    if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                        logging.info("Режим 'Отчёт': читаем только последние 40 дней")
                    
                    # Итерируемся в обратном порядке для поиска последних данных
                    for i in range(len(df) - 1, -1, -1):
                        row = df.iloc[i]
                        date_str = str(row.iloc[column_indices['date']])
                        
                        if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                            logging.debug(f"Обработка строки {i+1}")
                        
                        parsed_date = self._parse_date(date_str)
                        if parsed_date:
                            # Проверяем, не слишком ли старая дата
                            days_ago = (datetime.now() - parsed_date).days
                            if days_ago > 40:
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
                        
                        # Берем последний контейнер для каждого суффикса
                        latest_container = containers[-1]
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
                    # Для режима "Logos" - стандартная обработка
                    if hasattr(logging.getLogger(), 'handlers') and any(hasattr(h, 'console_widget') for h in logging.getLogger().handlers):
                        logging.info("Режим 'Logos': стандартная обработка всех строк")
                    
                    for i, row in df.iterrows():
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
                        
                        # Берем последний контейнер для каждого суффикса
                        latest_container = containers[-1]
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

    def process_data(self):
        """
        Организует контейнеры по юнитам (заказ или коносамент) для дальнейшей обработки.
        """
        self.logger.info("Начало организации контейнеров по юнитам")
        self.containers_by_unit = {}
        
        for container, row in self.latest_container_data.items():
            try:
                self.logger.debug(f"Обработка контейнера '{container}'")
                
                company = row["company"]
                unit = row["order"] if company == "GRAND-TRADE" else row["bill"]
                
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
        result = self.containers_by_unit.get(unit, [])
        self.logger.debug(f"Unit '{unit}': найдено {len(result)} контейнеров: {result}")
        return result
