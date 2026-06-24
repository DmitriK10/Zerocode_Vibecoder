# ZerovPfo2Bot – Telegram AI бот с контекстом

## Описание
Бот с интеграцией OpenAI через ProxyAPI, поддерживает контекст диалога и работает через Cloudflare Worker.

## Команды
- `/start` – приветствие
- `/reset` – очистить контекст
- Любое текстовое сообщение – запрос к AI

## Настройка (файл `.env`)
```env
BOT_TOKEN=ваш_токен
OPENAI_API_KEY=ваш_ключ_ProxyAPI
OPENAI_BASE_URL=https://openai.api.proxyapi.ru/v1
TELEGRAM_API_BASE_URL=https://ваш-worker.workers.dev/bot

## Запуск
bash
pip install python-telegram-bot httpx openai python-dotenv requests
python bot.py

## Логирование
Логируются запросы пользователей и количество использованных токенов.

## Решение проблем
Таймауты увеличены до 60 секунд на подключение и 120 секунд на чтение.

Если возникает ошибка Invalid token, убедитесь, что TELEGRAM_API_BASE_URL заканчивается на /bot.

Для проверки Worker откройте в браузере https://ваш-worker.workers.dev – должна появиться страница приветствия.

text

---

## 🚀 Запуск

Выполните в терминале:

```bash
python bot.py
