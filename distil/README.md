# Distil

> Превращает неструктурированный текст — письма, заметки, расшифровки
> встреч — в структурированный список действий со строгим JSON, честной
> ручной проверкой и полным аудитом каждого запуска.

[![Python](https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-gpt--4o--mini-412991?logo=openai&logoColor=white)](https://platform.openai.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-169%20passed-brightgreen)](tests/)
[![Ruff](https://img.shields.io/badge/lint-ruff%20clean-000000)](https://docs.astral.sh/ruff/)
[![mypy](https://img.shields.io/badge/types-mypy%20strict-blue)](https://mypy.readthedocs.io/)

**Публичный стенд:** <https://distil.ddns.net>
*(Basic Auth — логин/пароль по запросу)*

---

## Зачем это

Разбор одного письма или заметки на задачи — это **10–15 минут** вручную.
Из десяти действий одно-два теряются. Трекеры (Jira, Notion) требуют
уже готовой структуры, а её ещё надо собрать.

**Distil** решает это так:

1. Вы вставляете текст.
2. Система возвращает структурированные действия с ответственным,
   сроком и приоритетом — в строгом JSON.
3. Там, где модель не уверена, действие помечается `needs_review=true`
   с причиной: «не указан исполнитель», «цитата не подтверждена»,
   «низкая уверенность».
4. Каждый запуск попадает в `audit_runs`. Ничего не происходит «втихую».

**Ключевой принцип:** LLM — ассистент, а не оракул. Система не делает
вид, что уверена. Там, где нужен человек, она честно просит проверку.

---

## Содержание

- [Демонстрация](#демонстрация)
- [Стек](#стек)
- [Архитектура](#архитектура)
- [Быстрый старт (≤ 10 минут)](#быстрый-старт--10-минут)
- [Переменные окружения](#переменные-окружения)
- [API](#api)
- [Пример работы](#пример-работы)
- [Ручная проверка](#ручная-проверка)
- [Веб-панель](#веб-панель)
- [Тестирование](#тестирование)
- [Локальная разработка](#локальная-разработка)
- [Деплой на сервер](#деплой-на-сервер)
- [Roadmap](#roadmap)
- [Лицензия](#лицензия)

---

## Демонстрация

**Публичный стенд:** <https://distil.ddns.net> *(Basic Auth)*

### Скриншоты

**Витрина текстов** — список с фильтром и экспортом:

![Витрина](docs/screenshots/01_vitrina.png)

**Создание текста** — форма ввода:

![Создание текста](docs/screenshots/02_create_text.png)

**Карточка до извлечения** — текст есть, действий нет:

![До извлечения](docs/screenshots/03_before_extract.png)

**После извлечения** — 4 действия с ответственным, сроком, приоритетом
и цитатой из исходного текста:

![После извлечения](docs/screenshots/04_after_extract.png)

**Ручная проверка `soft`** — жёлтые плашки «не указан исполнитель»:

![Soft review](docs/screenshots/05_manual_review_soft.png)

**Ручная проверка `critical`** — красные плашки «неоднозначный срок»:

![Critical review](docs/screenshots/06_manual_review_critical.png)

**Подтверждение действия** — статус `confirmed`:

![Подтверждение](docs/screenshots/07_confirm_edit.png)

**Аудит** — цепочка `create_text → extract_actions → manual_review`
с полным `input`/`output` JSON:

![Аудит](docs/screenshots/08_audit.png)

**Экспорт в CSV** — открывается в Excel со всеми колонками:

![Экспорт CSV](docs/screenshots/09_export_csv.png)

**Swagger UI** — все API endpoints с Try-it-out:

![Swagger](docs/screenshots/10_swagger.png)

**HTTPS-верификация** — валидный сертификат Let's Encrypt:

![HTTPS verified](docs/screenshots/00_https_verified.png)

---

## Стек

| Слой                | Технология                                              |
| ------------------- | ------------------------------------------------------- |
| Язык                | Python 3.11                                             |
| Web                 | FastAPI, Uvicorn                                        |
| Валидация           | Pydantic v2, pydantic-settings                          |
| База данных         | PostgreSQL 16                                           |
| ORM                 | SQLAlchemy 2.0 (async, `asyncpg`)                       |
| Миграции            | Alembic                                                 |
| LLM                 | OpenAI SDK → `proxyapi.ru`, модель `gpt-4o-mini`        |
| Fuzzy-матчинг       | rapidfuzz                                               |
| Логи                | structlog (JSON, с редакцией секретов)                  |
| Rate limiting       | slowapi                                                 |
| Frontend            | Jinja2 + HTMX + Tailwind (CDN)                          |
| Тесты               | pytest, pytest-asyncio, httpx                           |
| Линт / типы         | ruff, mypy `--strict`                                   |
| Контейнеризация     | Docker, docker-compose                                  |
| Reverse proxy       | Caddy (HTTPS через Let's Encrypt)                       |
| CI                  | GitHub Actions                                          |

---

## Архитектура

```
┌──────────────────────────────────────────────────────────────┐
│              Веб-панель (Jinja2 + HTMX + Tailwind)           │
│      /              /texts/{id}              /audit          │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTP / HTMX
┌──────────────────────────▼───────────────────────────────────┐
│                       FastAPI                                │
│   /api/*   — JSON                                            │
│   /web/*   — HTML + HTMX-партиалы                            │
│   /export/* — CSV / JSON                                     │
│   /health   — healthcheck                                    │
└──────────────────────────┬───────────────────────────────────┘
                           │ Depends (DI)
┌──────────────────────────▼───────────────────────────────────┐
│                     Services (domain)                        │
│  TextService · ExtractionService · ReviewService             │
│  ValidationService · AuditService · ActionService            │
└──────────────────────────┬───────────────────────────────────┘
                           │ Protocol (DIP)
┌──────────────────────────▼───────────────────────────────────┐
│                   Repositories (Protocol)                    │
│   Postgres* (production)   │   Fake* (tests, in-memory)      │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│           PostgreSQL 16  +  Alembic migrations               │
└──────────────────────────────────────────────────────────────┘

              ┌───────────────────────────────────────┐
              │   LLM-клиент (Protocol)               │
              │   ProxyApiLLMClient (proxyapi.ru)     │
              │   FakeLLMClient (tests)               │
              └───────────────────────────────────────┘
```

**Принципы:**

- **Dependency Inversion** — сервисы зависят от `Protocol`, не от
  SQLAlchemy / OpenAI SDK. Замена БД или LLM — в одной точке проводки.
- **Repository pattern** — `Postgres*` для продакшна, `Fake*` для тестов.
  Оба удовлетворяют одному протоколу → LSP соблюдён.
- **Audit trail** — `audit_runs.status ∈ {ok, error}` (операционный),
  `actions.review_status ∈ {pending, confirmed, edited, rejected}`
  (бизнес-состояние). Разделены корректно.
- **Строгий JSON** — Pydantic `extra="forbid"`; LLM-ответ не может
  «добавить поле». Плюс fuzzy-проверка `source_quote` (порог 0.85).
- **Prompt injection** — изоляция данных маркерами + regex-детектор.
- **Ре-извлечение** — кнопка «Извлечь заново» полностью заменяет
  старые действия новыми (idempotent operation).

---

## Быстрый старт (≤ 10 минут)

### 1. Требования

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
  (Linux containers, WSL 2).
- Ключ `proxyapi.ru` — [получить](https://proxyapi.ru/).

### 2. Клонирование и `.env`

```bash
git clone <repo-url> distil
cd distil
cp .env.example .env
```

Открой `.env` и вставь реальный ключ:

```dotenv
LLM_API_KEY=sk-...ваш_ключ...
```

Больше ничего менять не нужно — `DATABASE_URL` в `.env.example` уже
указывает на PostgreSQL внутри `docker-compose`.

### 3. Запуск

```bash
docker compose up --build -d
```

Что произойдёт:
- Соберётся образ `distil-app` (multi-stage, non-root).
- Поднимется `postgres:16-alpine`.
- Применятся миграции Alembic (`alembic upgrade head`).
- Uvicorn стартует на `http://localhost:8000`.

Первый запуск — 2–3 минуты.

### 4. Проверка

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:

```json
{
  "status": "ok",
  "app_name": "distil",
  "version": "0.1.0",
  "env": "production",
  "db": "ok",
  "llm_model": "gpt-4o-mini"
}
```

### 5. Загрузка тестовых данных

```bash
docker compose exec app python -m scripts.seed
```

Скрипт идемпотентен: повторный запуск не создаст дубликатов.

**Готово.** Открывай:

| Что                | URL                                |
| ------------------ | ----------------------------------- |
| Веб-панель         | <http://localhost:8000/>            |
| Аудит              | <http://localhost:8000/audit>       |
| API-документация   | <http://localhost:8000/docs>        |

### Остановка

```bash
docker compose down        # остановить, оставить данные
docker compose down -v     # остановить и удалить том с БД
```

---

## Переменные окружения

Все переменные читаются из `.env` (см. `.env.example`).

| Переменная                | Обязательна | По умолчанию                                          | Описание                                    |
| ------------------------- | :---------: | ----------------------------------------------------- | ------------------------------------------- |
| `LLM_API_KEY`             |      ✅     | `replace-me`                                          | Ключ `proxyapi.ru`                          |
| `LLM_BASE_URL`            |      ✅     | `https://api.proxyapi.ru/openai/v1`                   | База прокси                                 |
| `LLM_MODEL`               |      ✅     | `gpt-4o-mini`                                         | Модель (из allowlist)                       |
| `LLM_ALLOWED_MODELS`      |      ✅     | `gpt-4o-mini`                                         | Список разрешённых моделей (через запятую)  |
| `DATABASE_URL`            |      ✅     | `postgresql+asyncpg://distil:distil@db:5432/distil`   | Строка подключения                          |
| `CORS_ORIGINS`            |      ➖     | `http://localhost:8000,...`                           | Разрешённые origin (через запятую)          |
| `APP_ENV`                 |      ➖     | `local`                                               | `local` / `test` / `production`             |
| `APP_DEBUG`               |      ➖     | `false`                                               | Отладка + reload                            |
| `TEXT_MIN_LENGTH`         |      ➖     | `10`                                                  | Мин. длина текста                           |
| `TEXT_MAX_LENGTH`         |      ➖     | `20000`                                               | Макс. длина текста                          |
| `AUDIT_RETENTION_DAYS`    |      ➖     | `30`                                                  | Срок хранения аудита                        |
| `RATE_LIMIT_PER_MINUTE`   |      ➖     | `60`                                                  | Лимит запросов на IP                        |
| `API_AUTH_ENABLED`        |      ➖     | `false`                                               | Включить Basic Auth на веб-панель           |
| `API_AUTH_USERNAME`       |      ➖     | —                                                     | Логин для Basic Auth                        |
| `API_AUTH_PASSWORD`       |      ➖     | —                                                     | Пароль (≥ 8 символов при включённой auth)   |

**Политика моделей.** Единственный источник правды — `LLM_ALLOWED_MODELS`.
Если `LLM_MODEL` не входит в список, приложение падает с `ValueError`
**до** первого запроса — fail-fast.

**Секреты нигде не логируются.** `structlog` редактирует поля
`*_key`, `password`, `token`, `authorization` перед записью.

**При включённой auth** (`API_AUTH_ENABLED=true`) приложение проверяет,
что заданы и `API_AUTH_USERNAME`, и `API_AUTH_PASSWORD`, иначе падает
на старте — fail-fast.

---

## API

### Endpoints

| Метод    | Путь                                | Назначение                                     |
| -------- | ----------------------------------- | ---------------------------------------------- |
| `GET`    | `/health`                           | Healthcheck (БД + конфиг)                      |
| `POST`   | `/api/texts`                        | Создать текст                                  |
| `GET`    | `/api/texts`                        | Витрина (с фильтрами и счётчиками)             |
| `GET`    | `/api/texts/{id}`                   | Карточка: текст + действия                     |
| `DELETE` | `/api/texts/{id}`                   | Удалить текст (каскадно с действиями)          |
| `POST`   | `/api/extract`                      | Запустить извлечение действий через LLM        |
| `GET`    | `/api/actions/{id}`                 | Получить действие                              |
| `PATCH`  | `/api/actions/{id}`                 | Отредактировать действие                       |
| `POST`   | `/api/actions/{id}/confirm`         | Подтвердить                                    |
| `POST`   | `/api/actions/{id}/reject`          | Отклонить                                      |
| `DELETE` | `/api/actions/{id}`                 | Удалить действие                               |
| `GET`    | `/api/audit`                        | Журнал запусков                                |
| `GET`    | `/api/audit/{id}`                   | Одна запись аудита                             |
| `GET`    | `/export/actions.csv` / `.json`     | Экспорт действий                               |
| `GET`    | `/export/texts.csv` / `.json`       | Экспорт текстов                                |

Полная интерактивная документация — <http://localhost:8000/docs>.

### Примеры curl

**Создать текст**

```bash
curl -X POST http://localhost:8000/api/texts \
  -H "Content-Type: application/json" \
  -d '{
    "source": "email",
    "raw_text": "Иван, привет! Нужно до пятницы подготовить отчёт по продажам. Это важно."
  }'
```

**Запустить извлечение**

```bash
curl -X POST http://localhost:8000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"text_id": 1}'
```

**Витрина (только требующие проверки)**

```bash
curl "http://localhost:8000/api/texts?has_review_required=true&limit=20"
```

**Аудит (только ошибки)**

```bash
curl "http://localhost:8000/api/audit?status=error&limit=50"
```

**Экспорт в CSV**

```bash
curl -O http://localhost:8000/export/actions.csv
```

**С Basic Auth** (если `API_AUTH_ENABLED=true`):

```bash
curl -u admin:<пароль> https://distil.ddns.net/
```

---

## Пример работы

**Вход** (текст из письма):

> Иван, привет! Нужно до пятницы подготовить отчёт по продажам и
> согласовать бюджет на Q3. Также свяжись с Марией по поводу логотипа —
> она обещала макеты к среде. И не забудь про налоги, срок до 25-го.

**Выход** (`POST /api/extract`):

```json
{
  "text_id": 1,
  "actions": [
    {
      "id": 1,
      "title": "Подготовить отчёт по продажам",
      "assignee": "Иван",
      "due_date": null,
      "due_date_raw": "до пятницы",
      "priority": "medium",
      "source_quote": "Нужно до пятницы подготовить отчёт по продажам",
      "confidence": 0.90,
      "needs_review": true,
      "review_reason": "Срок указан в неоднозначной форме и не был нормализован",
      "review_severity": "critical",
      "review_status": "pending"
    },
    {
      "id": 2,
      "title": "Согласовать бюджет на Q3",
      "assignee": "Иван",
      "due_date": null,
      "due_date_raw": "до пятницы",
      "priority": "medium",
      "source_quote": "согласовать бюджет на Q3",
      "confidence": 0.90,
      "needs_review": true,
      "review_reason": "Срок указан в неоднозначной форме и не был нормализован",
      "review_severity": "critical",
      "review_status": "pending"
    }
  ],
  "needs_review_count": 2,
  "duration_ms": 2159,
  "injection_detected": false
}
```

Обрати внимание: система **не выдумывает** конкретные даты. Относительный
срок «до пятницы» сохраняется как `due_date_raw`, а действие помечается
`critical` — потому что нормализовать его без даты разговора нельзя.
Пользователь сам решит, что это за пятница.

---

## Ручная проверка

Distil различает **два уровня** проверки:

| Уровень    | Когда                                                       | Что делать                        |
| ---------- | ----------------------------------------------------------- | --------------------------------- |
| `soft`     | Нет исполнителя / срока. Это нормально для заметки.         | Можно подтвердить оптом.          |
| `critical` | Галлюцинация, `confidence < 0.7`, неоднозначный срок.       | Обязательна ручная правка.        |

### Как воспроизвести

1. Создайте текст без исполнителя и срока:

   ```bash
   curl -X POST http://localhost:8000/api/texts \
     -H "Content-Type: application/json" \
     -d '{"source": "note", "raw_text": "Надо что-то сделать с документами, но пока непонятно что."}'
   ```

2. Запустите извлечение:

   ```bash
   curl -X POST http://localhost:8000/api/extract \
     -H "Content-Type: application/json" \
     -d '{"text_id": 2}'
   ```

3. В ответе будет `needs_review: true`, `review_severity: "soft"`,
   `review_reason: "Не указан исполнитель"`.

4. То же видно в веб-панели на `/texts/2` — действие подсвечено жёлтым,
   и его можно подтвердить, отредактировать или отклонить.

5. Все действия пользователя попадают в `audit_runs` с
   `action=manual_review`.

### Ре-извлечение

Кнопка **«Извлечь заново»** доступна на карточке текста в статусе
`extracted`. При нажатии:

1. Все старые действия этого текста **удаляются**.
2. LLM вызывается заново.
3. Создаётся свежий набор действий.

Это делает операцию **идемпотентной**: сколько раз ни нажимай —
дубликатов не появится.

**Тестовый файл:** `tests_data/inputs.jsonl` — 10 записей, из которых
минимум 2 гарантированно дают `needs_review=true`.

---

## Веб-панель

Три экрана:

| Экран          | URL              | Возможности                                                       |
| -------------- | ---------------- | ----------------------------------------------------------------- |
| **Витрина**    | `/`              | Список текстов, фильтр «только требует проверки», форма создания  |
| **Карточка**   | `/texts/{id}`    | Исходный текст + действия; HTMX-кнопки confirm / edit / reject    |
| **Аудит**      | `/audit`         | Все запуски с фильтром `status`, раскрытие `input`/`output` JSON  |

Экспорт доступен с витрины — кнопки `Texts CSV`, `Actions CSV`,
`Actions JSON`.

Всё построено на **Jinja2 + HTMX** без сборки и без JS-фреймворка:
- Кнопки делают `POST`/`PATCH`/`DELETE` и подменяют `<tr>` действия.
- Валидация формы — на бэкенде, ответ — готовый HTML-фрагмент.
- Состояние нигде не хранится на клиенте.

---

## Тестирование

```bash
python -m pytest -q
```

**Ожидаемый результат:** `169 passed` за ~5 секунд.

Тесты идут **без БД и без сети** — используются `Fake*Repository` и
`FakeLLMClient`. Это позволяет прогонять весь сьют на любой машине
за секунды.

### Что покрыто

| Категория                       | Файл                                        | Кол-во |
| ------------------------------- | ------------------------------------------- | ------ |
| Конфиг + политика модели        | `tests/test_config.py`                      | 7      |
| ORM-модели и CHECK-констрейнты  | `tests/test_models.py`                      | 11     |
| Postgres-репозитории            | `tests/test_repositories_postgres.py`       | 9      |
| Fake-репозитории                | `tests/test_repositories_fake.py`           | 5      |
| Fuzzy-матчинг `source_quote`    | `tests/test_llm_fuzzy.py`                   | 8      |
| System prompt + injection       | `tests/test_llm_prompts.py`                 | 7      |
| Парсер LLM-ответа               | `tests/test_llm_parser.py`                  | 17     |
| FakeLLMClient                   | `tests/test_llm_fake_client.py`             | 5      |
| ProxyApiLLMClient               | `tests/test_llm_proxyapi_client.py`         | 10     |
| Сервисы (5 файлов)              | `tests/test_service_*.py`                   | 32     |
| HTTP API (5 файлов)             | `tests/test_api_*.py`                       | 30     |
| Web / HTMX (3 файла)            | `tests/test_web_*.py`                       | 22     |

### Линт и типы

```bash
python -m ruff check app tests
python -m mypy app
```

Ожидаемо: `All checks passed!` и `Success: no issues found`.

### CI

GitHub Actions прогоняет тот же набор на каждый push и PR — см.
`.github/workflows/ci.yml`.

---

## Локальная разработка

### Без Docker

Нужен локальный PostgreSQL 16:

```sql
CREATE USER distil WITH PASSWORD 'distil';
CREATE DATABASE distil OWNER distil;
```

Установка зависимостей:

```bash
python -m venv venv --upgrade-deps
# Windows: .\venv\Scripts\Activate.ps1
# Linux/macOS: source venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
```

Правка `.env`: поменяй `DATABASE_URL` на `localhost`:

```dotenv
DATABASE_URL=postgresql+asyncpg://distil:distil@localhost:5432/distil
```

Миграции и запуск:

```bash
alembic upgrade head
python run.py
```

### Полезные команды

```bash
# Прогнать один тест
python -m pytest tests/test_llm_parser.py -v

# Прогнать тесты с покрытием
python -m pytest --cov=app --cov-report=term-missing

# Автоформат
python -m ruff check app tests --fix
python -m ruff format app tests

# Загрузка тестовых данных
python -m scripts.seed

# Миграция
alembic revision --autogenerate -m "add column X"
alembic upgrade head
alembic downgrade -1
```

---

## Деплой на сервер

Проект развёрнут на Ubuntu 24.04 VPS с доменом `distil.ddns.net` и
HTTPS через Let's Encrypt.

### Архитектура деплоя

```
[Интернет] → Caddy (443, HTTPS) → distil-app (127.0.0.1:8000) → distil-db (127.0.0.1:5432)
```

### Минимальные шаги

```bash
# 1. Установить Docker
curl -fsSL https://get.docker.com | sh

# 2. Клонировать и настроить
git clone <repo-url> /opt/distil
cd /opt/distil
cp .env.example .env
nano .env
```

**Что поменять в `.env` для продакшена:**

```dotenv
APP_ENV=production
APP_DEBUG=false
CORS_ORIGINS=https://distil.ddns.net
LLM_API_KEY=sk-...боевой_ключ...
API_AUTH_ENABLED=true
API_AUTH_USERNAME=admin
API_AUTH_PASSWORD=<сильный_пароль>
```

```bash
# 3. Запустить
chmod 600 .env
docker compose up -d --build
docker compose exec app python -m scripts.seed

# 4. Установить Caddy
apt-get install -y caddy
nano /etc/caddy/Caddyfile
```

**Caddyfile:**

```caddyfile
{
    email your-email@example.com
}

distil.ddns.net {
    encode gzip
    reverse_proxy localhost:8000
}
```

```bash
systemctl reload caddy
```

Caddy автоматически получит сертификат Let's Encrypt (30 секунд).

### Безопасность

В `docker-compose.yml` порты привязаны к loopback:

```yaml
ports:
  - "127.0.0.1:8000:8000"
  - "127.0.0.1:5432:5432"
```

Это значит, что приложение и БД **не видны из интернета**. Весь внешний
трафик идёт через Caddy на 443 → localhost:8000.

UFW открывает только 22 (SSH), 80 (ACME challenge), 443 (HTTPS).

### Обновление

```bash
cd /opt/distil
git pull
docker compose up -d --build
docker compose exec app alembic upgrade head  # если менялась схема
```

---

## Roadmap

- [ ] Импорт PDF/DOCX (`pypdf`, `python-docx`).
- [ ] Экспорт в Notion / Jira / Trello.
- [ ] Multi-user + RBAC.
- [ ] Кэш результатов по хешу текста.
- [ ] Векторный поиск по архиву действий.
- [ ] Метрика точности извлечения (сравнение с эталонной разметкой).
- [ ] Retention policy для `audit_runs`.
- [ ] Prometheus `/metrics`.
- [ ] Integration-тесты на реальном PostgreSQL в CI.

---

## Лицензия

Распространяется под лицензией **MIT** — см. [LICENSE](LICENSE.txt).

---

<p align="center">
  <sub>Distil — MVP с промышленной архитектурой. Готов к развитию в продукт.</sub>
</p>
