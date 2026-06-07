from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

from .config import EVENTS_LOG_PATH
from .exceptions import LoggingError  # изменён импорт


class FileNotifier:
    """Уведомление через запись в файл events.log"""

    def __init__(self, log_path: Path = EVENTS_LOG_PATH):
        self.log_path = log_path

    def notify(self, lead_id: int, lead_data: Dict[str, Any]) -> None:
        """Записывает событие 'New lead saved' в лог-файл"""
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            log_entry = f"[{timestamp}] New lead saved: id={lead_id}, contact={lead_data['contact']}\n"
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except OSError as e:
            # Используем специализированное исключение для ошибок лога
            raise LoggingError(f"Ошибка записи в лог-файл: {e}")