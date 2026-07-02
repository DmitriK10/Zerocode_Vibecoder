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