"""
Клиент для Google Sheets с абстракцией.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from googleapiclient.errors import HttpError

from google_integration.auth import GoogleAuthManager


class SheetsClient(ABC):
    @abstractmethod
    def create_spreadsheet(self, title: str, folder_id: Optional[str] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update_sheet(
        self, spreadsheet_id: str, range_name: str, values: List[List[Any]]
    ) -> None:
        pass

    @abstractmethod
    def get_sheet_values(self, spreadsheet_id: str, range_name: str) -> List[List[Any]]:
        pass


class GoogleSheetsClient(SheetsClient):
    def __init__(self, auth_manager: GoogleAuthManager, use_user_auth: bool = False):
        self.auth_manager = auth_manager
        self.use_user_auth = use_user_auth
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = self.auth_manager.build_sheets_service(self.use_user_auth)
        return self._service

    def create_spreadsheet(self, title: str, folder_id: Optional[str] = None) -> Dict[str, Any]:
        # Для создания таблицы в папке нужно сначала создать файл через Drive API,
        # но здесь мы создаём через Sheets API (он создаёт в корне, если не указать parents).
        # Поэтому лучше использовать DriveClient для создания, а затем обновлять.
        # Для простоты оставим создание через Drive, но здесь мы сделаем через Sheets.
        # На самом деле, стандартный способ: создать файл через Drive с mimeType=application/vnd.google-apps.spreadsheet
        # и затем получить его ID.
        # Для унификации используем DriveClient внутри.
        drive_client = GoogleDriveClient(self.auth_manager, self.use_user_auth)
        file_meta = drive_client.create_file(
            name=title,
            mime_type="application/vnd.google-apps.spreadsheet",
            folder_id=folder_id,
        )
        return file_meta

    def update_sheet(
        self, spreadsheet_id: str, range_name: str, values: List[List[Any]]
    ) -> None:
        body = {"values": values}
        try:
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            ).execute()
        except HttpError as e:
            raise RuntimeError(f"Failed to update sheet: {e}")

    def get_sheet_values(self, spreadsheet_id: str, range_name: str) -> List[List[Any]]:
        try:
            result = (
                self.service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id, range=range_name
                ).execute()
            )
            return result.get("values", [])
        except HttpError as e:
            raise RuntimeError(f"Failed to get sheet values: {e}")