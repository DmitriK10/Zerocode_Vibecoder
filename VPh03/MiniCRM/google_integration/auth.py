"""
Модуль аутентификации для Google API.
"""

import os
import pickle
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import settings
from logger import logger


class GoogleAuthManager:
    SCOPES = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets",
    ]

    def __init__(
        self,
        service_account_file: Optional[str] = None,
        oauth_client_file: Optional[str] = None,
        token_pickle_file: Optional[str] = None,
    ):
        self.service_account_file = service_account_file or settings.GOOGLE_SERVICE_ACCOUNT_FILE
        self.oauth_client_file = oauth_client_file or settings.GOOGLE_OAUTH_CLIENT_FILE
        self.token_pickle_file = token_pickle_file or settings.GOOGLE_TOKEN_PICKLE_FILE
        logger.debug("AuthManager инициализирован, token path: %s", self.token_pickle_file)

    def get_service_account_creds(self) -> ServiceAccountCredentials:
        if not self.service_account_file or not os.path.exists(self.service_account_file):
            logger.error("Файл сервисного аккаунта не найден: %s", self.service_account_file)
            raise FileNotFoundError(f"Service account file not found: {self.service_account_file}")
        logger.info("Загружены учётные данные сервисного аккаунта")
        return ServiceAccountCredentials.from_service_account_file(
            self.service_account_file, scopes=self.SCOPES
        )

    def get_user_oauth_creds(self) -> Credentials:
        creds = None
        if self.token_pickle_file and os.path.exists(self.token_pickle_file):
            with open(self.token_pickle_file, "rb") as token:
                creds = pickle.load(token)
                logger.debug("Токен загружен из файла")

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Обновление токена по refresh_token")
                creds.refresh(Request())
            else:
                logger.info("Запуск OAuth-потока для получения нового токена")
                if not self.oauth_client_file or not os.path.exists(self.oauth_client_file):
                    logger.error("Файл OAuth клиента не найден: %s", self.oauth_client_file)
                    raise FileNotFoundError(f"OAuth client file not found: {self.oauth_client_file}")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.oauth_client_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Сохраняем токен
            if self.token_pickle_file:
                os.makedirs(os.path.dirname(self.token_pickle_file), exist_ok=True)
                with open(self.token_pickle_file, "wb") as token:
                    pickle.dump(creds, token)
                logger.info("Токен сохранён в %s", self.token_pickle_file)
        return creds

    def build_drive_service(self, use_user_auth: bool = False):
        creds = self.get_user_oauth_creds() if use_user_auth else self.get_service_account_creds()
        logger.debug("Сервис Drive создан (user_auth=%s)", use_user_auth)
        return build("drive", "v3", credentials=creds)

    def build_sheets_service(self, use_user_auth: bool = False):
        creds = self.get_user_oauth_creds() if use_user_auth else self.get_service_account_creds()
        logger.debug("Сервис Sheets создан (user_auth=%s)", use_user_auth)
        return build("sheets", "v4", credentials=creds)