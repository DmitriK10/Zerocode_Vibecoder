"""
google_integration/google_drive.py
Модуль для работы с Google Drive через OAuth2 (личный аккаунт).
Содержит класс GoogleDrive для создания, чтения и удаления файлов.
"""

import os
import pickle
from pathlib import Path
from typing import Optional, List, Dict, Any

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import HttpError

# Если OAuth2-клиентские данные хранятся в отдельном файле
# По умолчанию ищем client_secret.json в корне проекта
DEFAULT_CLIENT_SECRET = "client_secret.json"
DEFAULT_TOKEN_PATH = "token.pickle"

# Необходимые области доступа
SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets"
]


class GoogleDrive:
    """
    Клиент для Google Drive с OAuth2-аутентификацией.
    Отвечает за создание, чтение и удаление файлов/папок.
    """
    def __init__(self, client_secret_path: str = DEFAULT_CLIENT_SECRET,
                 token_path: str = DEFAULT_TOKEN_PATH):
        """
        :param client_secret_path: путь к JSON-файлу с OAuth2-клиентскими данными.
        :param token_path: путь для сохранения/загрузки токена (pickle).
        """
        self.client_secret_path = Path(client_secret_path)
        self.token_path = Path(token_path)
        self._service = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Загружает или обновляет учётные данные и создаёт сервис."""
        creds = None
        # Пытаемся загрузить токен из pickle
        if self.token_path.exists():
            with open(self.token_path, "rb") as token_file:
                creds = pickle.load(token_file)

        # Если токен недействителен или отсутствует, запускаем OAuth-поток
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.client_secret_path.exists():
                    raise FileNotFoundError(
                        f"Файл client_secret не найден: {self.client_secret_path}"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.client_secret_path), SCOPES
                )
                # Запускаем локальный сервер для авторизации
                creds = flow.run_local_server(port=0)
            # Сохраняем токен для будущих запусков
            with open(self.token_path, "wb") as token_file:
                pickle.dump(creds, token_file)

        self._service = build("drive", "v3", credentials=creds)

    def list_files(self, folder_id: Optional[str] = None,
                   page_size: int = 100) -> List[Dict[str, Any]]:
        """
        Возвращает список файлов в указанной папке (или корне).
        """
        query = f"'{folder_id}' in parents" if folder_id else "trashed = false"
        try:
            results = self._service.files().list(
                q=query,
                pageSize=page_size,
                fields="files(id, name, mimeType, webViewLink, createdTime)"
            ).execute()
            return results.get("files", [])
        except HttpError as e:
            raise RuntimeError(f"Ошибка при получении списка файлов: {e}")

    def create_google_spreadsheet(self, name: str,
                                  parent_folder_id: Optional[str] = None) -> str:
        """
        Создаёт новую Google Таблицу в указанной папке и возвращает её ID.
        """
        file_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.spreadsheet"
        }
        if parent_folder_id:
            file_metadata["parents"] = [parent_folder_id]

        try:
            file = self._service.files().create(body=file_metadata).execute()
            return file["id"]
        except HttpError as e:
            raise RuntimeError(f"Ошибка создания таблицы: {e}")

    def create_google_document(self, name: str,
                               parent_folder_id: Optional[str] = None) -> str:
        """
        Создаёт новый Google Документ и возвращает его ID.
        """
        file_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.document"
        }
        if parent_folder_id:
            file_metadata["parents"] = [parent_folder_id]

        try:
            file = self._service.files().create(body=file_metadata).execute()
            return file["id"]
        except HttpError as e:
            raise RuntimeError(f"Ошибка создания документа: {e}")

    def delete_file(self, file_id: str) -> None:
        """Удаляет файл по ID."""
        try:
            self._service.files().delete(fileId=file_id).execute()
        except HttpError as e:
            raise RuntimeError(f"Ошибка удаления файла {file_id}: {e}")

    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Возвращает метаданные файла по ID."""
        try:
            return self._service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, webViewLink, parents"
            ).execute()
        except HttpError as e:
            raise RuntimeError(f"Ошибка получения информации о файле {file_id}: {e}")

    def get_web_view_link(self, file_id: str) -> str:
        """Возвращает ссылку для просмотра файла в браузере."""
        info = self.get_file_info(file_id)
        return info.get("webViewLink", "")