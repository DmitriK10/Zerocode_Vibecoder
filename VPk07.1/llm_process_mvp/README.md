# LLM Process MVP — Автоматизация обработки обращений (кейс A)

Мини-сервис, который превращает входящие обращения клиентов в
структурированные задачи: **вход → LLM → контроль качества → действие**.

Процесс: `POST /ingest` → LLM (через proxyapi.ru) → строгая валидация JSON
по схеме → правило эскалации → журнал аудита в SQLite.

## Стек

- Python 3.10+
- FastAPI + Uvicorn
- Pydantic v2 + pydantic-settings (валидация схемы и конфига)
- SQLite (журнал аудита + результат)
- openai>=1.0, ChatCompletion через `https://api.proxyapi.ru/openai/v1`

## Структура проекта

```
llm_process_mvp\
├── .env.example              # шаблон окружения (скопировать в .env)
├── .gitignore                # .env, data/, venv/ — не попадают в репозиторий
├── pyproject.toml            # конфиг pytest (pythonpath, testpaths)
├── requirements.txt          # зависимости
├── README.md                 # этот файл
├── smoke_test.py             # CLI: 1 запрос к работающему серверу
├── run_batch.py              # CLI: 10 контрольных входов → CSV + JSON
├── inputs\                   # входные .txt для batch-прогона
├── data\                     # создаётся автоматически, в .gitignore
│   ├── processing.db         # журнал аудита (SQLite)
│   ├── results.csv           # сводка batch-прогона
│   └── results\*.json        # полный JSON по каждому кейсу
├── src\                      # пакет с бизнес-логикой
│   ├── config.py             # pydantic-settings, единая точка настроек
│   ├── bootstrap.py          # composition root: сборка адаптеров из Settings
│   ├── domain\               # модели (Pydantic) и порты (Protocol)
│   ├── services\             # оркестратор процесса + промпты
│   ├── infrastructure\       # адаптеры: OpenAI-прокси, SQLite
│   └── api\                  # FastAPI, singleton-обёртки над bootstrap
└── tests\                    # pytest-тесты (без сети)
```

## Модель

Основная модель проекта — **`gpt-4o-mini`**:

- точнее gpt-3.5-turbo-16k на классификации, меньше ложных эскалаций;
- дешевле: $0.15/1M input и $0.60/1M output против $0.50/$1.50 у 3.5;
- быстрее при сопоставимой задержке.

### Whitelist моделей

Поддерживаемые модели заданы явным списком `SUPPORTED_MODELS` в
`src/infrastructure/llm_client.py`. При старте модель из `.env` сверяется с
whitelist'ом: если её там нет — `ValueError`, приложение не поднимается.

Это не ограничение сверху, а **защита от опечаток**: `gpt-4o-minni` упадёт
с понятной ошибкой, а не превратится в загадочный 500 от API при первом
запросе. Чтобы добавить новую модель — расширь `SUPPORTED_MODELS`.

## Установка

```bat
cd C:\Users\ADATA\Documents\Zerocoder_Vibecoder\VPk07.1\llm_process_mvp
python -m venv venv --upgrade-deps
venv\Scripts\activate
pip install -r requirements.txt
```

## Настройка окружения

Скопируй `.env.example` в `.env` рядом с ним и заполни `PROXY_API_KEY`:

```powershell
Copy-Item .env.example .env
notepad .env
```

Обязательна только `PROXY_API_KEY`. Остальное имеет рабочие дефолты
(см. `src/config.py`). `.env` в `.gitignore` — секрет в репозиторий
не попадёт.

## Запуск сервера

```powershell
venv\Scripts\activate
uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```

Проверка живости:

```powershell
curl.exe http://127.0.0.1:8000/health
# {"status":"ok"}
```

## Отправка входа

Рекомендуется — smoke-тест (нет проблем с экранированием в PowerShell):

```powershell
python smoke_test.py "Не пришёл счёт за март, заказ 42"
python smoke_test.py "Привет"          # проверка эскалации
```

Прямой curl (Windows 10+, `curl.exe`, не алиас PowerShell):

```powershell
curl.exe -X POST http://127.0.0.1:8000/ingest `
  -H "Content-Type: application/json" `
  -d '{\"text\": \"Не пришёл счёт за март, заказ 42\"}'
```

Чтение журнала:

```powershell
curl.exe "http://127.0.0.1:8000/log?limit=20"
```

## Batch-прогон 10 контрольных входов

```powershell
python run_batch.py
```

Читает `inputs/*.txt`, обрабатывает каждый файл, пишет:

- `data/results.csv` — сводка (файл, статус, категория, приоритет, ошибка);
- `data/results/<name>.json` — полный JSON-результат по кейсу;
- `data/processing.db` — журнал аудита (пишется самим сервисом).

Перед прогоном старые JSON в `data/results/` удаляются, чтобы не
оставалось мусора от удалённых кейсов.

## Файлы данных

- БД: `C:\Users\ADATA\Documents\Zerocoder_Vibecoder\VPk07.1\llm_process_mvp\data\processing.db`
- CSV: `...\data\results.csv`
- JSON по кейсу: `...\data\results\<name>.json`

## Просмотр результатов в PowerShell

Файлы результатов записаны в UTF-8. PowerShell 5.1 по умолчанию читает их
в системной кодировке и показывает русский текст как «кракозябры»
(`РЎР°Р№С‚` вместо `Сайт`). Это артефакт отображения, данные на диске
корректны. Читай с явной кодировкой:

```powershell
Get-Content .\data\results\02_technical_outage.json -Raw -Encoding UTF8
```

Для CSV — либо `-Encoding UTF8`, либо открывай в Excel.

## Тесты

```powershell
pytest -q
```

Тесты работают **без сети** — LLM подменяется `FakeLLM` из
`tests/conftest.py`. Покрыты: доменные правила (эскалация при
`confidence=low`, запрет лишних полей), парсер JSON (markdown-забор,
текст вокруг), политика whitelist, оркестратор (happy path, ошибка LLM,
пустой вход, невалидный JSON), репозиторий (roundtrip, порядок, закрытие
соединений), конфиг (fail fast, границы температуры, дефолт модели),
промпт (дефолт escalate, четыре триггера, few-shot, маркеры юр. угрозы),
API (`/ingest` happy path + 422, `/log` чтение без LLM), CLI
(`smoke_test` env-резолверы, `run_batch` чистка старых результатов).

## Архитектура (кратко)

```
src/
├── config.py              # pydantic-settings, единая точка настроек
├── bootstrap.py           # composition root: сборка адаптеров из Settings
├── domain/                # модели (Pydantic) и порты (Protocol)
├── services/              # оркестратор процесса + промпты
├── infrastructure/        # адаптеры: OpenAI-прокси, SQLite
└── api/                   # FastAPI, singleton-обёртки над bootstrap
```

Сервис зависит только от протоколов `LLMClient` и `ProcessingRepository`
(DIP). Конкретные реализации внедряются через `src/bootstrap.py`, который
используют и FastAPI-путь (`src/api/app.py`), и batch-прогон
(`run_batch.py`).

### Про singleton репозитория

`src/api/app.py` **не использует** `bootstrap.build_service` напрямую,
потому что в API нужен **один** репозиторий на процесс — общий между
`/ingest` (пишет) и `/log` (читает). Поэтому там своя обёртка
`_build_service_singleton`, которая берёт репозиторий из
`_repo_singleton()`. Если добавляешь шаг инициализации в
`bootstrap.build_service`, проверь, что он не нужен и в
`_build_service_singleton`.

## План v2

- Идемпотентность `/ingest` по хэшу входа (защита от дублей).
- Дедупликация похожих обращений по эмбеддингам.
- Замена синхронного вызова LLM на async (httpx.AsyncClient).
- Метрики: распределение статусов, средняя задержка, доля эскалаций.
- Валидация схемы на стороне LLM через `response_format={"type":"json_object"}`.
- Логирование через `logging` вместо `print` в CLI-скриптах.