"""Модуль для работы с Google Sheets API"""
import os
import sys
import logging
import traceback
from pathlib import Path

logger = logging.getLogger(__name__)

# Хардкод параметров Google Sheets
SPREADSHEET_ID = '1iP2M1rvP1cGTU0l9x-tAJ2x5927eUewZVNTOtUd6szo'
RANGE_NAME = 'Кнтр!A2:W'
CREDENTIALS_FILENAME = 'ancient-voltage-448710-s6-d883e82884d7.json'

def get_credentials_path():
    """Определяет путь к файлу credentials"""
    if getattr(sys, 'frozen', False):
        # Если приложение скомпилировано
        base_path = Path(sys.executable).parent
    else:
        # Если запущено из исходников
        base_path = Path(__file__).parent
    
    # Ищем в папке resources
    credentials_path = base_path / 'resources' / CREDENTIALS_FILENAME
    
    # Если не найден в resources, пробуем рядом с модулем
    if not credentials_path.exists():
        credentials_path = base_path / CREDENTIALS_FILENAME
    
    return str(credentials_path)

class GoogleSheetsManager:
    """Менеджер для работы с Google Sheets API"""
    
    def __init__(self, credentials_file=None, spreadsheet_id=None):
        """
        Инициализация менеджера Google Sheets
        
        Args:
            credentials_file: путь к файлу credentials (если None, используется хардкод)
            spreadsheet_id: ID таблицы (если None, используется хардкод)
        """
        self.credentials_file = credentials_file or get_credentials_path()
        self.spreadsheet_id = spreadsheet_id or SPREADSHEET_ID
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Аутентификация в Google Sheets API"""
        try:
            from google.oauth2 import service_account
            from googleapiclient import discovery
            
            if not os.path.exists(self.credentials_file):
                error_msg = f"Файл credentials не найден: {self.credentials_file}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
            
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            self.service = discovery.build('sheets', 'v4', credentials=creds)
            logger.info(f"Успешная аутентификация в Google Sheets API")
        except Exception as e:
            error_msg = f"Ошибка аутентификации в Google Sheets: {e}"
            logger.error(error_msg)
            traceback.print_exc()
            raise
    
    def get_data(self, range_name=None):
        """
        Получает данные из Google Sheets
        
        Args:
            range_name: диапазон ячеек (если None, используется хардкод)
        
        Returns:
            list: список строк данных
        """
        try:
            if self.service is None:
                raise RuntimeError("Сервис Google Sheets не инициализирован")
            
            range_to_use = range_name or RANGE_NAME
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_to_use
            ).execute()
            values = result.get('values', [])
            logger.info(f"Получено {len(values)} строк из Google Sheets")
            return values
        except Exception as e:
            error_msg = f"Ошибка при загрузке Google Sheets: {e}"
            logger.error(error_msg, exc_info=True)
            traceback.print_exc()
            raise

