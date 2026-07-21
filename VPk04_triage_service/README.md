# VPk04.1 Triage Service

ИИ-сервис для первичной обработки обращений: классификация, черновик ответа, эскалация.

## 📌 Функциональность

- Принимает текст обращения, канал и ID клиента.
- Классифицирует по категориям: `billing`, `support`, `complaint`, `other`.
- Генерирует черновик ответа (1–6 предложений).
- Оценивает уверенность (`high`/`medium`/`low`).
- При низкой уверенности или ошибке LLM – эскалирует оператору (`escalate: true`).
- Сохраняет все запросы и ответы в SQLite (аудит).
- Ограничивает частоту запросов (10 в минуту на `client_id`).

## 🚀 Быстрый старт (локально)

### 1. Клонируйте репозиторий
```bash
git clone https://github.com/ваш-логин/VPk04_triage_service.git
cd VPk04_triage_service
2. Создайте виртуальное окружение
bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
3. Установите зависимости
bash
pip install -r requirements.txt
4. Настройте переменные окружения
Создайте файл .env (скопируйте из .env.example или создайте вручную):

env
OPENAI_API_KEY=sk-ваш-ключ
OPENAI_BASE_URL=https://openai.api.proxyapi.ru/v1
RATE_LIMIT_PER_MINUTE=10
DEFAULT_MODEL=gpt-4o-mini
5. Запустите сервис
bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
Сервис будет доступен по адресу: http://localhost:8000

📡 API
POST /api/v1/triage
Пример запроса:

bash
curl -X POST http://localhost:8000/api/v1/triage \
  -H "Content-Type: application/json" \
  -d '{"text": "Не могу оплатить заказ", "channel": "email", "client_id": "user123"}'
Пример ответа (успех):

json
{
  "category": "billing",
  "draft_reply": "Здравствуйте! Проверьте баланс карты или свяжитесь с банком.",
  "confidence": "high",
  "escalate": false
}
Пример ответа (ошибка LLM, эскалация):

json
{
  "category": "other",
  "draft_reply": "передано оператору",
  "confidence": "low",
  "escalate": true
}
🗄️ Просмотр базы данных (SQLite)
После первого запроса в папке проекта создаётся файл tickets.db.
Просмотреть все записи:

bash
sqlite3 tickets.db "SELECT * FROM tickets;"
Или в удобном формате:

bash
sqlite3 tickets.db "SELECT id, client_id, category, confidence, escalate, draft_reply FROM tickets;"
📋 Логирование
Логи сервиса выводятся в консоль (при ручном запуске) или в systemd (при развёртывании).
Для просмотра логов в systemd:

bash
journalctl -u triage.service -f
🌐 Развёртывание на сервере (опционально)
Сервис развёрнут на VPS Reg.ru:
Публичный адрес: http://80.78.247.11/api/v1/triage

Пример запроса к продакшн-версии:

bash
curl -X POST http://80.78.247.11/api/v1/triage \
  -H "Content-Type: application/json" \
  -d '{"text": "Проблема с оплатой", "channel": "email", "client_id": "test"}'
📦 Технологии
Python 3.14+

FastAPI

OpenAI (ProxyAPI)

SQLite

Uvicorn

Nginx (на сервере)

📄 Лицензия
MIT