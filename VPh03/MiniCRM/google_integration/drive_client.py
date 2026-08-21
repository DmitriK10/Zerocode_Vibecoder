"""
Абстрактный клиент для Google Drive с реализацией через googleapiclient.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from googleapiclient.errors import HttpError

from google_integration.auth import GoogleAuthManager


class DriveClient(ABC):
    """Абстрактный интерфейс для работы с Google Drive."""

    @abstractmethod
    def list_files(self, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def create_file(
        self, name: str, mime_type: str, folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def delete_file(self, file_id: str) -> None:
        pass

    @abstractmethod
    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        pass


class GoogleDriveClient(DriveClient):
    """Реализация клиента для Google Drive с использованием AuthManager."""

    def __init__(self, auth_manager: GoogleAuthManager, use_user_auth: bool = False):
        self.auth_manager = auth_manager
        self.use_user_auth = use_user_auth
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = self.auth_manager.build_drive_service(self.use_user_auth)
        return self._service

    def list_files(self, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            query = []
            if folder_id:
                query.append(f"'{folder_id}' in parents")
            query.append("trashed = false")
            q = " and ".join(query) if query else "trashed = false"

            results = (
                self.service.files()
                .list(q=q, fields="files(id, name, mimeType, createdTime, modifiedTime)")
                .execute()
            )
            return results.get("files", [])
        except HttpError as e:
            raise RuntimeError(f"Google Drive API error: {e}")

    def create_file(
        self, name: str, mime_type: str, folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        file_metadata = {"name": name, "mimeType": mime_type}
        if folder_id:
            file_metadata["parents"] = [folder_id]

        try:
            file = (
                self.service.files()
                .create(body=file_metadata, fields="id, name, webViewLink")
                .execute()
            )
            return file
        except HttpError as e:
            raise RuntimeError(f"Failed to create file: {e}")

    def delete_file(self, file_id: str) -> None:
        try:
            self.service.files().delete(fileId=file_id).execute()
        except HttpError as e:
            raise RuntimeError(f"Failed to delete file: {e}")

    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        try:
            return (
                self.service.files()
                .get(fileId=file_id, fields="id, name, mimeType, parents, webViewLink")
                .execute()
            )
        except HttpError as e:
            raise RuntimeError(f"Failed to get file metadata: {e}")