from datetime import datetime
from typing import Protocol

class DateTimeProvider(Protocol):
    def get_current_datetime(self) -> datetime:
        ...

class SystemDateTimeService:
    def get_current_datetime(self) -> datetime:
        return datetime.now()

class DateTimeService:
    def __init__(self, provider: DateTimeProvider):
        self._provider = provider

    def get_current_datetime_info(self) -> dict:
        now = self._provider.get_current_datetime()
        return {
            "current_datetime": now,
            "timestamp": now.timestamp()
        }