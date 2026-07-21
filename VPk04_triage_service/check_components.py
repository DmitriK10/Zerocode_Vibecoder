"""Утилита для проверки работоспособности компонентов сервиса."""
import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path, чтобы импорты работали
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings
from app.llm.proxyapi_client import ProxyAPILLMClient
from app.repository.ticket_repo import TicketRepository
from app.services.rate_limiter import RateLimiter
from app.core.exceptions import LLMServiceError

async def check_env():
    """Проверка загрузки переменных окружения."""
    print("[1/4] Проверка .env...")
    assert settings.OPENAI_API_KEY, "OPENAI_API_KEY не задан"
    assert settings.OPENAI_BASE_URL, "OPENAI_BASE_URL не задан"
    print(f"      OPENAI_BASE_URL = {settings.OPENAI_BASE_URL}")
    print("      OK\n")

async def check_llm():
    """Проверка подключения к ProxyAPI через простой запрос."""
    print("[2/4] Проверка LLM-клиента...")
    client = ProxyAPILLMClient(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )
    try:
        # Простейший тестовый запрос
        result = await client.triage("Тестовое обращение")
        print(f"      Ответ модели: {result}")
        print("      OK\n")
    except LLMServiceError as e:
        print(f"      ОШИБКА: {e}")
        sys.exit(1)

def check_db():
    """Проверка создания таблицы и записи в SQLite."""
    print("[3/4] Проверка SQLite...")
    repo = TicketRepository(db_path="test_check.db")
    # Попробуем сохранить тестовую запись
    repo.save_ticket(
        client_id="check",
        channel="form",
        text="Проверка",
        category="support",
        confidence="high",
        escalate=False,
        draft_reply="Ответ",
        error=None,
    )
    print("      Запись добавлена (файл test_check.db)")
    print("      OK\n")
    # Удалим тестовый файл, чтобы не мусорить
    Path("test_check.db").unlink(missing_ok=True)

def check_rate_limiter():
    """Проверка работы in-memory лимитера."""
    print("[4/4] Проверка Rate Limiter...")
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    assert limiter.is_allowed("client1"), "Первый запрос должен быть разрешён"
    assert limiter.is_allowed("client1"), "Второй запрос должен быть разрешён"
    assert limiter.is_allowed("client1"), "Третий запрос должен быть разрешён"
    assert not limiter.is_allowed("client1"), "Четвёртый запрос должен быть заблокирован"
    # Другой клиент не заблокирован
    assert limiter.is_allowed("client2"), "Запрос от другого клиента должен быть разрешён"
    print("      OK\n")

async def main():
    await check_env()
    await check_llm()
    check_db()
    check_rate_limiter()
    print("🎉 Все компоненты работают корректно!")

if __name__ == "__main__":
    asyncio.run(main())