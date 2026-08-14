"""
google_sheets.py
Модуль для работы с Google Sheets через сервисный аккаунт.
Содержит классы:
- CredentialsProvider: загружает и предоставляет учётные данные.
- SheetsClient: реализует CRUD-операции и форматирование таблицы.
Соблюдены принципы SRP и DIP.
"""

import os
import json
from typing import List, Optional, Any, Dict, Union
from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Для удобства работы с переменными окружения
from dotenv import load_dotenv

load_dotenv()


class CredentialsProvider:
    """
    Класс-провайдер учётных данных.
    Единственная ответственность: загрузить credentials из JSON-файла.
    """
    def __init__(self, credentials_path: str):
        """
        :param credentials_path: полный путь к JSON-файлу с ключами сервисного аккаунта.
        """
        self._path = Path(credentials_path)
        if not self._path.exists():
            raise FileNotFoundError(f"Файл с ключами не найден: {self._path}")

    def get_credentials(self, scopes: Optional[List[str]] = None) -> Credentials:
        """
        Возвращает объект Credentials для заданных scopes.
        По умолчанию используются scopes для Google Sheets и Drive (чтение/запись).
        """
        if scopes is None:
            scopes = ['https://www.googleapis.com/auth/spreadsheets',
                      'https://www.googleapis.com/auth/drive']
        return Credentials.from_service_account_file(
            str(self._path), scopes=scopes
        )


class SheetsClient:
    """
    Клиент для работы с Google Sheets.
    Зависит от абстракции CredentialsProvider (DIP).
    SRP: отвечает только за взаимодействие с таблицей.
    """
    def __init__(self, credentials_provider: CredentialsProvider, spreadsheet_id: str):
        """
        :param credentials_provider: экземпляр провайдера учётных данных.
        :param spreadsheet_id: идентификатор Google Таблицы (из URL).
        """
        self._spreadsheet_id = spreadsheet_id
        self._service = build('sheets', 'v4', credentials=credentials_provider.get_credentials())
        self._sheets_api = self._service.spreadsheets()

    # ------------------- Чтение данных -------------------
    def read_range(self, range_name: str) -> List[List[Any]]:
        """
        Читает данные из заданного диапазона.
        :param range_name: например, 'Лист1!A1:C10'
        :return: список строк (каждая строка — список значений).
        """
        try:
            result = self._sheets_api.values().get(
                spreadsheetId=self._spreadsheet_id,
                range=range_name
            ).execute()
            return result.get('values', [])
        except HttpError as e:
            raise RuntimeError(f"Ошибка чтения диапазона {range_name}: {e}")

    def read_all_cells(self, sheet_name: Optional[str] = None) -> List[List[Any]]:
        """
        Читает все данные с указанного листа (по умолчанию первый лист).
        :param sheet_name: имя листа (если None, берётся первый).
        :return: список строк.
        """
        if sheet_name is None:
            sheet_names = self.get_sheet_names()
            if not sheet_names:
                return []
            sheet_name = sheet_names[0]
        return self.read_range(f"'{sheet_name}'!A1:ZZ")

    def get_sheet_names(self) -> List[str]:
        """
        Возвращает список имён всех листов в таблице.
        """
        try:
            metadata = self._sheets_api.get(spreadsheetId=self._spreadsheet_id).execute()
            sheets = metadata.get('sheets', [])
            return [s['properties']['title'] for s in sheets]
        except HttpError as e:
            raise RuntimeError(f"Ошибка получения списка листов: {e}")

    # ------------------- Запись данных -------------------
    def write_range(self, range_name: str, values: List[List[Any]],
                    value_input_option: str = 'RAW') -> None:
        """
        Записывает данные в заданный диапазон.
        :param range_name: диапазон для записи.
        :param values: данные (список строк).
        :param value_input_option: 'RAW' или 'USER_ENTERED'.
        """
        body = {'values': values}
        try:
            self._sheets_api.values().update(
                spreadsheetId=self._spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body
            ).execute()
        except HttpError as e:
            raise RuntimeError(f"Ошибка записи в диапазон {range_name}: {e}")

    def append_rows(self, sheet_name: str, rows: List[List[Any]],
                    value_input_option: str = 'USER_ENTERED') -> None:
        """
        Добавляет строки в конец указанного листа.
        """
        body = {'values': rows}
        try:
            self._sheets_api.values().append(
                spreadsheetId=self._spreadsheet_id,
                range=f"'{sheet_name}'!A1",
                valueInputOption=value_input_option,
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
        except HttpError as e:
            raise RuntimeError(f"Ошибка добавления строк на лист {sheet_name}: {e}")

    def add_sheet(self, title: str) -> None:
        """
        Создаёт новый лист с заданным именем.
        """
        requests = [{
            'addSheet': {
                'properties': {'title': title}
            }
        }]
        self._batch_update(requests)

    def delete_sheet(self, sheet_id: int) -> None:
        """
        Удаляет лист по его ID.
        """
        requests = [{
            'deleteSheet': {
                'sheetId': sheet_id
            }
        }]
        self._batch_update(requests)

    def get_sheet_id_by_name(self, name: str) -> Optional[int]:
        """
        Возвращает ID листа по его имени.
        """
        try:
            metadata = self._sheets_api.get(spreadsheetId=self._spreadsheet_id).execute()
            for sheet in metadata.get('sheets', []):
                props = sheet['properties']
                if props['title'] == name:
                    return props['sheetId']
            return None
        except HttpError as e:
            raise RuntimeError(f"Ошибка получения ID листа {name}: {e}")

    # ------------------- Форматирование -------------------
    def set_cell_format(self, sheet_name: str, start_row: int, end_row: int,
                        start_col: int, end_col: int,
                        format_dict: Dict[str, Any]) -> None:
        """
        Применяет форматирование к диапазону ячеек.
        :param sheet_name: имя листа.
        :param start_row, end_row: индексы строк (1-based).
        :param start_col, end_col: индексы столбцов (1-based).
        :param format_dict: словарь с параметрами формата (см. документацию Google Sheets API).
        """
        sheet_id = self.get_sheet_id_by_name(sheet_name)
        if sheet_id is None:
            raise ValueError(f"Лист {sheet_name} не найден")

        requests = [{
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': start_row - 1,
                    'endRowIndex': end_row,
                    'startColumnIndex': start_col - 1,
                    'endColumnIndex': end_col
                },
                'cell': {
                    'userEnteredFormat': format_dict
                },
                'fields': 'userEnteredFormat'
            }
        }]
        self._batch_update(requests)

    def merge_cells(self, sheet_name: str, start_row: int, end_row: int,
                    start_col: int, end_col: int) -> None:
        """
        Объединяет ячейки в заданном диапазоне.
        """
        sheet_id = self.get_sheet_id_by_name(sheet_name)
        if sheet_id is None:
            raise ValueError(f"Лист {sheet_name} не найден")

        requests = [{
            'mergeCells': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': start_row - 1,
                    'endRowIndex': end_row,
                    'startColumnIndex': start_col - 1,
                    'endColumnIndex': end_col
                },
                'mergeType': 'MERGE_ALL'
            }
        }]
        self._batch_update(requests)

    def set_column_width(self, sheet_name: str, column_index: int, width: int) -> None:
        """
        Устанавливает ширину столбца в пикселях.
        :param column_index: номер столбца (1-based).
        """
        sheet_id = self.get_sheet_id_by_name(sheet_name)
        if sheet_id is None:
            raise ValueError(f"Лист {sheet_name} не найден")

        requests = [{
            'updateDimensionProperties': {
                'range': {
                    'sheetId': sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': column_index - 1,
                    'endIndex': column_index
                },
                'properties': {
                    'pixelSize': width
                },
                'fields': 'pixelSize'
            }
        }]
        self._batch_update(requests)

    def _batch_update(self, requests: List[Dict]) -> None:
        """
        Внутренний метод для выполнения пакетного обновления.
        """
        try:
            self._sheets_api.batchUpdate(
                spreadsheetId=self._spreadsheet_id,
                body={'requests': requests}
            ).execute()
        except HttpError as e:
            raise RuntimeError(f"Ошибка batchUpdate: {e}")

    # ------------------- Утилиты -------------------
    def clear_sheet(self, sheet_name: str) -> None:
        """
        Очищает всё содержимое указанного листа (без удаления самого листа).
        """
        sheet_id = self.get_sheet_id_by_name(sheet_name)
        if sheet_id is None:
            raise ValueError(f"Лист {sheet_name} не найден")
        requests = [{
            'updateCells': {
                'range': {
                    'sheetId': sheet_id
                },
                'fields': 'userEnteredValue'
            }
        }]
        self._batch_update(requests)