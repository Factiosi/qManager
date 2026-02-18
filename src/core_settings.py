import os
import json
import logging

logger = logging.getLogger(__name__)

class SettingsManager:
    def __init__(self):
        appdata_dir = os.getenv('APPDATA', os.path.expanduser('~'))
        settings_dir = os.path.join(appdata_dir, 'qManager')
        os.makedirs(settings_dir, exist_ok=True)
        self.settings_path = os.path.join(settings_dir, 'settings.json')
        self.default_settings = {
            'splitter_input': '',
            'splitter_output': '',
            'threshold': 2.3,
            
            'renamer_input': '',
            'renamer_output': '',
            'excel_file': '',
            
            'organizer_input': '',
            'organizer_output': '',
            'organizer_excel_file': '',
            
            'excel_mode': 'logos',
            'excel_reader': 'openpyxl',
            
            'dark_mode': False,
            'window_size': [1024, 768],
            'window_position': [100, 100],
            'last_tab': 0,
            
            'debug_mode': False,
            'log_level': 'INFO',
            'operation_timeout': 30,
            
            'filter_mode': 'unlimited',
            'filter_date_from': None,
            'filter_date_to': None,
            
            'auto_run_renamer': False,
            
            'ocr_binarization': False
        }

    def load_settings(self):
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    return {**self.default_settings, **json.load(f)}
        except Exception as e:
            logger.error(f"Ошибка загрузки настроек: {e}")
        return self.default_settings

    def save_settings(self, settings):
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек: {e}")
