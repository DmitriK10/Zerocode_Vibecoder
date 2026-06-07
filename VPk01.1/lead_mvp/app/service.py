from typing import Dict, Any

from .database import DatabaseRepository
from .notifier import FileNotifier
from .exceptions import DatabaseError, LoggingError, LeadSaveError


class LeadService:
    """Бизнес-логика: сохранение заявки + уведомление"""

    def __init__(self, db_repo: DatabaseRepository, notifier: FileNotifier):
        self.db_repo = db_repo
        self.notifier = notifier

    def process_lead(self, lead_data: Dict[str, Any]) -> int:
        """
        Обрабатывает заявку:
        1. Сохраняет в БД
        2. Отправляет уведомление
        3. Возвращает ID записи
        """
        try:
            lead_id = self.db_repo.save_lead(lead_data)
        except DatabaseError as e:
            raise LeadSaveError(f"Не удалось сохранить заявку в БД: {e}")

        try:
            self.notifier.notify(lead_id, lead_data)
        except LoggingError as e:          # перехватываем новое исключение
            raise LeadSaveError(f"Не удалось записать уведомление: {e}")

        return lead_id