class LLMServiceError(Exception):
    """Ошибка при обращении к языковой модели."""
    pass


class RateLimitExceededError(Exception):
    """Превышен лимит запросов для client_id."""
    pass