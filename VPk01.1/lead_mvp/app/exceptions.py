# Кастомные исключения для чёткой обработки ошибок
class DatabaseError(Exception):
    """Ошибка при работе с базой данных"""
    pass


class LoggingError(Exception):
    """Ошибка при записи в лог-файл"""
    pass


class LeadSaveError(Exception):
    """Ошибка сохранения заявки"""
    pass