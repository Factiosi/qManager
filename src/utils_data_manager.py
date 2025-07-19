from datetime import datetime, timedelta
import pandas as pd

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
        """
        Инициализация менеджера данных: создаёт структуры для хранения контейнеров и их распределения по юнитам.
        mode: 'logos' (по умолчанию) или 'report'
        """
        self.mode = mode
        self.latest_container_data = {}
        self.containers_by_unit = {}

    def _log(self, message):
        """
        Внутренняя функция логирования.
        Аргументы:
            message (str): Сообщение для вывода в лог.
        """
        print(f"[LOG] {message}")

    def _find_column_index(self, columns, possible_names):
        """
        Поиск индекса столбца по возможным вариантам названия.
        Аргументы:
            columns (list): Список названий столбцов из Excel.
            possible_names (list): Возможные варианты названия столбца.
        Возвращает:
            int или None: Индекс найденного столбца или None, если не найден.
        """
        for name in possible_names:
            matches = [i for i, col in enumerate(columns) if str(col).strip().lower() == name.lower()]
            if matches:
                return matches[0]
        return None

    def _parse_date(self, date_str):
        """
        Пытается распарсить строку с датой в одном из нескольких форматов.
        Аргументы:
            date_str (str): Строка с датой.
        Возвращает:
            datetime или None: Объект даты или None, если не удалось распознать.
        """
        formats = [
            "%d.%m.%Y",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y"
        ]
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str).strip(), fmt)
            except ValueError:
                continue
        return None

    def _extract_container_number(self, container_str):
        """
        Извлекает числовую часть номера контейнера (последние 7 цифр).
        Аргументы:
            container_str (str): Номер контейнера в виде строки.
        Возвращает:
            str или None: Последние 7 цифр или None, если не найдено.
        """
        if not container_str or pd.isna(container_str):
            return None
        digits = ''.join(c for c in str(container_str) if c.isdigit())
        if len(digits) >= 7:
            return digits[-7:]
        return None

    def load_excel_data(self, excel_path):
        """
        Загружает и обрабатывает данные контейнеров из Excel-файла. Извлекаются только необходимые столбцы.
        Аргументы:
            excel_path (str): Путь к Excel-файлу.
        Исключения:
            ValueError: Если не найден хотя бы один обязательный столбец.
            Exception: Критические ошибки при обработке файла.
        """
        self._log(f"Загрузка Excel файла: {excel_path} (режим: {self.mode})")
        try:
            with pd.ExcelFile(excel_path) as excel_file:
                df = pd.read_excel(excel_file)
                self._log(f"Прочитано строк: {len(df)}")
                self._log(f"Колонки в файле: {df.columns.tolist()}")
                columns = df.columns.tolist()
                column_indices = {}
                if self.mode == "report":
                    mappings = self.EXCEL_COLUMN_MAPPINGS_REPORT
                else:
                    mappings = self.EXCEL_COLUMN_MAPPINGS
                for key, possible_names in mappings.items():
                    idx = self._find_column_index(columns, possible_names)
                    if idx is None:
                        self._log(f"ОШИБКА: Не найден столбец для {key}. Возможные имена: {possible_names}")
                        raise ValueError(f"Не найден столбец для {key}. Возможные имена: {possible_names}")
                    column_indices[key] = idx
                    self._log(f"Найден столбец {key}: {columns[idx]}")
                processed_rows = 0
                valid_containers = 0
                containers_data = {}
                # --- Фильтрация и порядок строк для режима 'report' ---
                if self.mode == "report":
                    now = datetime.now()
                    max_age = timedelta(days=40)
                    rows = list(df.iterrows())[::-1]  # С конца
                else:
                    rows = list(df.iterrows())
                for idx, row in rows:
                    try:
                        container_full = str(row[columns[column_indices['container']]]).strip()
                        if not container_full or pd.isna(container_full):
                            continue
                        # Для режима 'report' — фильтрация по дате прибытия
                        if self.mode == "report":
                            date_val = row[columns[column_indices['date']]]
                            if pd.isna(date_val) or not str(date_val).strip():
                                continue
                            date_obj = self._parse_date(date_val)
                            if not date_obj or (now - date_obj) > max_age:
                                continue
                        # Извлекаем последние 7 цифр номера контейнера
                        digits = ''.join(c for c in container_full if c.isdigit())
                        if len(digits) < 7:
                            continue
                        container_suffix = digits[-7:]
                        order = str(row[columns[column_indices['order']]]).strip()
                        order = order if order and not pd.isna(order) else "UNKNOWN_ORDER"
                        vessel = str(row[columns[column_indices['vessel']]]).strip()
                        vessel = vessel if vessel and not pd.isna(vessel) else "UNKNOWN_VESSEL"
                        date = str(row[columns[column_indices['date']]]).strip()
                        date = date if date and not pd.isna(date) else "UNKNOWN_DATE"
                        bill = str(row[columns[column_indices['bill']]]).strip()
                        bill = bill if bill and not pd.isna(bill) else "UNKNOWN_BILL"
                        data_row = {
                            "vessel": vessel,
                            "date": date,
                            "bill": bill,
                            "order": order,
                            "container": container_full,
                            "company": "GRAND-TRADE"
                        }
                        if container_suffix not in containers_data:
                            containers_data[container_suffix] = []
                        containers_data[container_suffix].append(data_row)
                        valid_containers += 1
                        processed_rows += 1
                    except Exception as e:
                        self._log(f"Ошибка при обработке строки {idx + 1}: {str(e)}")
                # Сохраняем последние данные по контейнерам (ключ — полный номер контейнера)
                self.latest_container_data.clear()
                for container_suffix, container_list in containers_data.items():
                    for data_row in container_list:
                        self.latest_container_data[data_row["container"]] = data_row
                self._log(f"\nИтоги обработки:")
                self._log(f"Всего обработано строк: {processed_rows}")
                self._log(f"Найдено валидных контейнеров: {valid_containers}")
                self._log(f"Уникальных контейнеров: {len(self.latest_container_data)}")
        except Exception as e:
            self._log(f"Критическая ошибка при обработке файла: {str(e)}")
            raise

    def process_data(self):
        """
        Организует контейнеры по юнитам (заказ или коносамент) для дальнейшей обработки.
        """
        self.containers_by_unit = {}
        for container, row in self.latest_container_data.items():
            try:
                company = row["company"]
                unit = row["order"] if company == "GRAND-TRADE" else row["bill"]
                if not unit:
                    continue
                if unit not in self.containers_by_unit:
                    self.containers_by_unit[unit] = []
                if container not in self.containers_by_unit[unit]:
                    self.containers_by_unit[unit].append(container)
            except Exception as e:
                self._log(f"Ошибка при обработке контейнера {container}: {e}")

    def get_container_data(self, container):
        """
        Получить словарь с данными по номеру контейнера.
        Аргументы:
            container (str): Полный номер контейнера.
        Возвращает:
            dict или None: Словарь с данными по контейнеру или None, если не найден.
        """
        return self.latest_container_data.get(container)

    def get_containers_by_unit(self, unit):
        """
        Получить список контейнеров, связанных с юнитом (заказом или коносаментом).
        Аргументы:
            unit (str): Идентификатор юнита (заказ или коносамент).
        Возвращает:
            list: Список номеров контейнеров для юнита или пустой список, если не найдено.
        """
        return self.containers_by_unit.get(unit, [])
