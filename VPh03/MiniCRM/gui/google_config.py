"""
gui/google_config.py
Загрузка настроек Google из файла и создание репортера.
"""

import os
from pathlib import Path
from gui.api_client import CRMClient
from google_integration.auth import GoogleAuthManager
from gui.google_reporter import GoogleReporter
from logger import logger

SETTINGS_FILE = Path.home() / ".crm_google_settings.txt"

def load_google_settings():
    settings = {}
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    key, val = line.strip().split("=", 1)
                    settings[key] = val
        logger.debug("Настройки Google загружены из %s", SETTINGS_FILE)
    else:
        logger.warning("Файл настроек Google не найден")
    return settings

def get_reporter():
    settings = load_google_settings()
    client_secret = settings.get("client_secret")
    credentials = settings.get("credentials")
    folder_id = settings.get("folder_id")

    if not all([client_secret, credentials, folder_id]):
        logger.error("Не все настройки Google заполнены")
        raise ValueError("Не все настройки Google заполнены. Зайдите в Настройки Google и сохраните пути.")

    auth_manager = GoogleAuthManager(
        service_account_file=credentials,
        oauth_client_file=client_secret,
        token_pickle_file=None  # используется путь из config
    )
    api_client = CRMClient()
    logger.info("GoogleReporter создан с folder_id=%s", folder_id)
    return GoogleReporter(api_client, auth_manager, folder_id, use_user_auth=True)