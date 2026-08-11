# Командный AI-бот для Telegram с Haystack и Pinecone

## Установка
1. Клонируйте репозиторий.
2. Создайте файл `.env` и заполните своими ключами (см. пример).
3. Установите зависимости: `pip install -r requirements.txt`

## Переменные окружения
Для работы бота необходимо создать файл `.env` в корне проекта со следующими переменными:

| Переменная | Описание |
|------------|----------|
| `TELEGRAM_BOT_TOKEN` | Токен вашего бота, полученный от @BotFather. |
| `OPENAI_API_KEY` | API-ключ OpenAI (или прокси). |
| `OPENAI_BASE_URL` | URL для API OpenAI (используйте прокси, например, `https://api.proxyapi.ru/openai/v1`). |
| `OPENAI_MODEL` | Модель для генерации текста (по умолчанию `gpt-3.5-turbo-16k`). |
| `EMBEDDING_MODEL` | Модель для создания эмбеддингов (по умолчанию `text-embedding-3-small`). |
| `PINECONE_API_KEY` | API-ключ Pinecone. |
| `PINECONE_INDEX_NAME` | Имя индекса в Pinecone. |
| `PINECONE_ENVIRONMENT` | Регион/окружение Pinecone (например, `gcp-starter`). |

## Запуск бота
```bash
python bot.py
Запуск тестов
bash
python run_tests.py
Функционал
Индексация всех сообщений в чате с метаданными.

Команды /start_listening и /stop_listening для записи сессии и получения резюме.

Упоминание бота с вопросом – поиск по истории чата.