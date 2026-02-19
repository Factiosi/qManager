import os
import re
import sys
import logging
import traceback
from pathlib import Path

logger = logging.getLogger(__name__)

SPREADSHEET_ID = os.environ.get('QMANAGER_SPREADSHEET_ID', '1iP2M1rvP1cGTU0l9x-tAJ2x5927eUewZVNTOtUd6szo')
RANGE_NAME = os.environ.get('QMANAGER_SHEETS_RANGE', 'Кнтр!A2:W')
CREDENTIALS_FILENAME = os.environ.get('QMANAGER_CREDENTIALS_FILE', 'ancient-voltage-448710-s6-d883e82884d7.json')
SHEETS_CHUNK_SIZE = int(os.environ.get('QMANAGER_SHEETS_CHUNK_SIZE', '2000'))
SHEETS_MAX_CHUNKS = int(os.environ.get('QMANAGER_SHEETS_MAX_CHUNKS', '1'))
SHEETS_TIMEOUT = int(os.environ.get('QMANAGER_SHEETS_TIMEOUT', '60'))

def get_credentials_path():
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent
    
    credentials_path = base_path / 'resources' / CREDENTIALS_FILENAME
    
    if not credentials_path.exists():
        credentials_path = base_path / CREDENTIALS_FILENAME
    
    return str(credentials_path)

class GoogleSheetsManager:
    def __init__(self, credentials_file=None, spreadsheet_id=None):
        self.credentials_file = credentials_file or get_credentials_path()
        self.spreadsheet_id = spreadsheet_id or SPREADSHEET_ID
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        try:
            from google.oauth2 import service_account
            from googleapiclient import discovery
            from google_auth_httplib2 import AuthorizedHttp
            import httplib2
            
            if not os.path.exists(self.credentials_file):
                error_msg = f"Файл credentials не найден: {self.credentials_file}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
            
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )

            http = httplib2.Http(timeout=SHEETS_TIMEOUT)
            auth_http = AuthorizedHttp(creds, http=http)
            self.service = discovery.build(
                'sheets',
                'v4',
                http=auth_http,
                cache_discovery=False,
                static_discovery=False
            )
            logger.info(f"Успешная аутентификация в Google Sheets API")
        except Exception as e:
            error_msg = f"Ошибка аутентификации в Google Sheets: {e}"
            logger.error(error_msg)
            traceback.print_exc()
            raise

    @staticmethod
    def _parse_a1_range(range_name: str):
        if not range_name or "!" not in range_name:
            return None
        sheet_part, cells = range_name.split("!", 1)
        sheet_name = sheet_part.strip().strip("'")
        match = re.match(r"^([A-Z]+)(\d+):([A-Z]+)$", cells.strip(), re.IGNORECASE)
        if not match:
            return None
        col_from, row_from, col_to = match.group(1).upper(), int(match.group(2)), match.group(3).upper()
        return sheet_name, col_from, row_from, col_to

    @staticmethod
    def _quote_sheet_name(sheet_name: str) -> str:
        escaped = sheet_name.replace("'", "''")
        return f"'{escaped}'"

    def _get_last_data_row(self, sheet_name: str, anchor_col: str, row_from: int, max_retries: int = 2):
        range_for_probe = f"{self._quote_sheet_name(sheet_name)}!{anchor_col}{row_from}:{anchor_col}"
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=range_for_probe,
            valueRenderOption='UNFORMATTED_VALUE',
            fields='values'
        ).execute(num_retries=max_retries)
        values = result.get("values", [])
        if not values:
            return None
        return row_from + len(values) - 1

    def _build_tail_ranges(self, range_name: str):
        parsed = self._parse_a1_range(range_name)
        if not parsed:
            return [range_name]

        sheet_name, col_from, row_from, col_to = parsed
        if SHEETS_CHUNK_SIZE <= 0 or SHEETS_MAX_CHUNKS <= 0:
            return [range_name]

        last_data_row = self._get_last_data_row(sheet_name, col_from, row_from)
        if not last_data_row or last_data_row < row_from:
            return [range_name]

        ranges = []
        current_end = int(last_data_row)
        chunks_added = 0
        while current_end >= row_from and chunks_added < SHEETS_MAX_CHUNKS:
            current_start = max(row_from, current_end - SHEETS_CHUNK_SIZE + 1)
            ranges.append(
                f"{self._quote_sheet_name(sheet_name)}!{col_from}{current_start}:{col_to}{current_end}"
            )
            current_end = current_start - 1
            chunks_added += 1

        ranges.reverse()
        return ranges
    
    def get_data(self, range_name=None, max_retries=3):
        if self.service is None:
            raise RuntimeError("Сервис Google Sheets не инициализирован")
        
        try:
            range_to_use = range_name or RANGE_NAME
            sheet = self.service.spreadsheets()
            tail_ranges = self._build_tail_ranges(range_to_use)

            logger.info(
                f"Google Sheets: чтение {len(tail_ranges)} чанков "
                f"(chunk_size={SHEETS_CHUNK_SIZE}, max_chunks={SHEETS_MAX_CHUNKS})"
            )

            if len(tail_ranges) == 1:
                result = sheet.values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=tail_ranges[0],
                    valueRenderOption='UNFORMATTED_VALUE',
                    dateTimeRenderOption='FORMATTED_STRING',
                    fields='values'
                ).execute(num_retries=max_retries)
                values = result.get('values', [])
            else:
                result = sheet.values().batchGet(
                    spreadsheetId=self.spreadsheet_id,
                    ranges=tail_ranges,
                    valueRenderOption='UNFORMATTED_VALUE',
                    dateTimeRenderOption='FORMATTED_STRING',
                    fields='valueRanges(values)'
                ).execute(num_retries=max_retries)

                values = []
                for value_range in result.get('valueRanges', []):
                    values.extend(value_range.get('values', []))

            logger.info(f"Получено {len(values)} строк из Google Sheets")
            return values
        except Exception as e:
            error_msg = f"Ошибка при загрузке Google Sheets: {e}"
            logger.error(error_msg, exc_info=True)
            traceback.print_exc()
            raise

