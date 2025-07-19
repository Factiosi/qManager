import os
import json

class SettingsManager:
    def __init__(self):
        """
        Инициализация менеджера настроек: определяет путь к файлу настроек и создаёт директорию при необходимости.
        """
        self.settings_path = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), 'qManager', 'settings.json')
        # Создаём директорию, если её нет
        os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
        self.default_settings = {
            'splitter_input': '',
            'splitter_output': '',
            'renamer_input': '',
            'renamer_output': '',
            'organizer_input': '',
            'organizer_output': '',
            'threshold': 2.3,
            'excel_file': '',
            'organizer_excel_file': '',
            'excel_mode': 'logos',
        }

    @staticmethod
    def _get_settings_path():
        """
        Возвращает путь к файлу settings.json в директории %APPDATA%.
        """
        appdata_dir = os.getenv('APPDATA', os.path.expanduser('~'))
        settings_dir = os.path.join(appdata_dir, 'qManager')
        os.makedirs(settings_dir, exist_ok=True)
        return os.path.join(settings_dir, 'settings.json')

    def load_settings(self):
        """
        Загружает настройки из файла. Если файл отсутствует или повреждён, возвращает значения по умолчанию.
        Возвращает:
            dict: Словарь с настройками.
        """
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    return {**self.default_settings, **json.load(f)}
        except Exception as e:
            print(f"[ERROR] Ошибка загрузки настроек: {e}")
        return self.default_settings

    def save_settings(self, settings):
        """
        Сохраняет настройки в файл settings.json.
        Аргументы:
            settings (dict): Словарь с настройками для сохранения.
        """
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Ошибка сохранения настроек: {e}")
