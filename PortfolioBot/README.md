# Portfolio Telegram Bot

Промышленный Telegram-бот для демонстрации портфолио, разработанный на Python (aiogram 3).  
Проект демонстрирует соблюдение принципов **SRP** (Single Responsibility Principle) и **DIP** (Dependency Inversion Principle), а также устойчивую интеграцию с LLM через прокси-сервис.

## 🛠 Стек технологий

- **Python 3.11+**
- **aiogram 3** (Асинхронный фреймворк для Telegram Bot API)
- **httpx** (Современный асинхронный HTTP-клиент)
- **pytest** + **pytest-asyncio** (Модульное тестирование)
- **python-dotenv** (Безопасное управление переменными окружения)

## 📂 Структура проекта

Проект имеет четкое разделение ответственности:
- `main.py` — Точка входа, инициализация зависимостей и динамическое определение абсолютных путей.
- `src/interfaces.py` — Абстракции (интерфейсы) для соблюдения DIP.
- `src/repository.py` — Слой доступа к данным (чтение `projects.json`).
- `src/ai_service.py` — Интеграция с LLM (proxyapi.ru) с обработкой сетевых ошибок (Graceful Degradation).
- `src/bot_handlers.py` — Слой представления (логика ответов бота, HTML-рендеринг).
- `src/github_service.py` — Сервис для получения актуальных данных из GitHub API.
- `tests/` — Модульные тесты, покрывающие успешные сценарии и краевые случаи.

## 🚀 Запуск проекта

1. **Создайте виртуальное окружение и активируйте его:**
   ```powershell
   python -m venv venv --upgrade-deps
   .\venv\Scripts\Activate.ps1