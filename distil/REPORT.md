# Отчёт по выпускному проекту
## Distil — персональный помощник «от текста до действия»

---

## 1. Название выбранного проекта

**Distil** — система, которая превращает неструктурированный текст (письма,
заметки, расшифровки встреч) в структурированные действия с ответственным,
сроком и приоритетом, а также с честной ручной проверкой там, где модель
не уверена.

**Публичный стенд:** <https://distil.ddns.net> *(Basic Auth: логин/пароль
по запросу)*

**Репозиторий:** `<repo-url>` *(будет заполнено после публикации на GitHub)*

---

## 2. Ценность (для кого и зачем)

**Для кого:**
- **Фрилансеры и консультанты** — с потоком 15–20 писем в день.
- **Тимлиды после созвонов** — с расшифровками встреч на 40+ минут.
- **Менеджеры и проджекты** — ведущие договорённости в трекеры (Jira,
  Notion, Trello).

**Зачем:**
- Разбор письма на задачи вручную — **10–15 минут** на текст.
- В существующих трекерах задачи нужно сначала **сформулировать**.
- LLM без контроля качества **«уверенно врёт»** — выдумывает сроки,
  ответственных и цитаты.

**Что даёт Distil:**
- Экономия **~80% времени** на разбор текста.
- Ничего не теряется: даже неуверенные действия попадают в систему
  с флагом `needs_review`.
- **Прозрачность:** у каждого действия есть `source_quote` — цитата
  из исходного текста.
- **Честность:** система не делает вид, что уверена. Там, где нужен
  человек, она просит проверить.

---

## 3. Три сценария пользователя

### Сценарий A. Письмо → задачи
Пользователь вставляет письмо из почты → система извлекает 4–5 действий
→ пользователь проверяет за 1–2 минуты → экспорт в CSV/JSON.

### Сценарий B. Расшифровка созвона → договорённости
Пользователь вставляет расшифровку встречи (с шумом, «эээ», повторами)
→ часть действий помечается `needs_review=true` с причиной «не указан
исполнитель» → пользователь дочищает за 3–5 минут.

### Сценарий C. Поток заметок
Пользователь загружает несколько коротких заметок через импорт JSONL
→ витрина с фильтром `has_review_required=true` → массовая дочистка
и экспорт.

---

## 4. Точки доступа API

Минимум 3 точки как требует ТЗ — реализовано 15:

| Метод | Путь | Назначение |
|---|---|---|
| POST | `/api/texts` | **Создать текст** |
| GET | `/api/texts` | **Витрина** со счётчиками действий |
| POST | `/api/extract` | **ИИ-обработка** со строгим JSON |
| GET | `/api/texts/{id}` | Карточка текста с действиями |
| DELETE | `/api/texts/{id}` | Удалить текст (каскадно) |
| GET | `/api/actions/{id}` | Получить действие |
| PATCH | `/api/actions/{id}` | Редактировать (ручная проверка) |
| POST | `/api/actions/{id}/confirm` | Подтвердить |
| POST | `/api/actions/{id}/reject` | Отклонить |
| DELETE | `/api/actions/{id}` | Удалить действие |
| GET | `/api/audit` | **Журнал аудита** |
| GET | `/api/audit/{id}` | Одна запись аудита |
| GET | `/export/actions.csv` / `.json` | Экспорт действий |
| GET | `/export/texts.csv` / `.json` | Экспорт текстов |
| GET | `/health` | Healthcheck (БД + LLM) |

**Интерактивная документация:** <https://distil.ddns.net/docs>

---

## 5. Схема данных

### `texts` — исходные тексты
```sql
CREATE TABLE texts (
    id              BIGSERIAL PRIMARY KEY,
    source          VARCHAR(20) NOT NULL,   -- email | meeting | note
    raw_text        TEXT NOT NULL,
    status          VARCHAR(20) NOT NULL,   -- new | extracted | failed
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (source IN ('email','meeting','note')),
    CHECK (status IN ('new','extracted','failed')),
    CHECK (length(raw_text) BETWEEN 10 AND 20000)
);
```

### `actions` — извлечённые действия
```sql
CREATE TABLE actions (
    id              BIGSERIAL PRIMARY KEY,
    text_id         BIGINT NOT NULL REFERENCES texts(id) ON DELETE CASCADE,
    title           VARCHAR(200) NOT NULL,
    assignee        VARCHAR(120),
    due_date        DATE,
    due_date_raw    VARCHAR(120),
    priority        VARCHAR(10) NOT NULL,   -- low | medium | high
    source_quote    TEXT NOT NULL,          -- verbatim-цитата
    confidence      FLOAT NOT NULL,         -- 0.0 .. 1.0
    needs_review    BOOLEAN NOT NULL DEFAULT false,
    review_reason   TEXT,
    review_severity VARCHAR(10),            -- soft | critical
    review_status   VARCHAR(20) NOT NULL DEFAULT 'pending',
    reviewed_at     TIMESTAMPTZ,
    reviewed_by     VARCHAR(120),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (priority IN ('low','medium','high')),
    CHECK (review_status IN ('pending','confirmed','edited','rejected')),
    CHECK (review_severity IS NULL OR review_severity IN ('soft','critical')),
    CHECK (confidence BETWEEN 0.0 AND 1.0)
);
```

### `audit_runs` — журнал операций
```sql
CREATE TABLE audit_runs (
    id                  BIGSERIAL PRIMARY KEY,
    action              VARCHAR(40) NOT NULL,  -- create_text | extract_actions | manual_review | ...
    status              VARCHAR(10) NOT NULL,  -- ok | error
    input               JSONB,
    output              JSONB,
    needs_review_count  INTEGER NOT NULL DEFAULT 0,
    error               TEXT,
    duration_ms         INTEGER NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (status IN ('ok','error')),
    CHECK (duration_ms >= 0)
);
```

**Ключевое архитектурное решение:** `audit_runs.status ∈ {ok, error}` — это
**операционный** статус. **Бизнес**-состояние («требует проверки») живёт
в `actions.review_status`. Это разделение убирает путаницу при фильтрации.

---

## 6. ИИ-операция

### Схема JSON (строгая)
```json
{
  "actions": [
    {
      "title": "string (1..200)",
      "assignee": "string | null",
      "due_date_raw": "string | null",
      "due_date_iso": "YYYY-MM-DD | null",
      "priority": "low | medium | high",
      "source_quote": "verbatim substring",
      "confidence": 0.0,
      "needs_review": false,
      "review_reason": null,
      "review_severity": null
    }
  ]
}
```

Валидация через **Pydantic v2** с `extra="forbid"` — любое лишнее поле
вызывает ошибку. Это защита от prompt injection: попытка добавить
поле «role» или «system» провалится на этапе парсинга.

### Температура
**`temperature = 0.1`** — минимальный креатив. Модель не должна
«додумывать» — она извлекает.

### Когда нужна ручная проверка

| Условие | `review_severity` | `review_reason` |
|---|---|---|
| Нет исполнителя | `soft` | «Не указан исполнитель» |
| Нет срока в тексте | `soft` | «Не указан срок» |
| Срок неоднозначный («до 25-го») | `critical` | «Срок указан в неоднозначной форме» |
| `confidence < 0.7` | `critical` | «Низкая уверенность модели» |
| Цитата не подтверждена (fuzzy < 0.85) | `critical` | «Цитата не подтверждена» |
| Модель сама пометила как неуверенное | `soft`/`critical` | причина модели |

**`soft`** — можно подтвердить оптом.
**`critical`** — обязательная ручная правка.

---

## 7. Память / контекст

В MVP **не используется**. Каждый запрос — независимая операция.
Обоснование: проект решает разовую задачу «разобрать текст», а не ведёт
долгоживущий диалог.

**В плане развития:**
- Кэш результатов по хешу текста.
- Векторный поиск по архиву действий.
- Метрика точности через сравнение с эталонной разметкой.

---

## 8. Контроль качества

### На входе
- Длина текста: `10 ≤ length ≤ 20 000`.
- `source ∈ {email, meeting, note}`.
- **Детектор prompt injection** — 9 regex-паттернов
  (`ignore previous`, `system:`, `forget everything`, …).
  При срабатывании — флаг в аудите.

### На выходе LLM
- **Pydantic `extra="forbid"`** — лишние поля запрещены.
- Обязательные поля: `title`, `source_quote`, `confidence`,
  `needs_review`.
- `confidence ∈ [0.0, 1.0]`.
- `priority ∈ {low, medium, high}`.
- **Fuzzy-проверка `source_quote`** — порог 0.85 через `rapidfuzz`.
- Если `needs_review=true`, `review_reason` непустой.
- Если `review_severity=critical`, авто-подтверждение запрещено.

### Честность системы
Ключевое отличие от «просто ChatGPT»: **система не выдумывает**.
Если цитата не подтверждена или модель неуверена — действие попадает
в раздел «Требует проверки», а не в финальный список.

---

## 9. План внедрения за 1 день

1. `git clone <repo-url> distil && cd distil`
2. `cp .env.example .env`
3. Вставить `LLM_API_KEY` (proxyapi.ru) в `.env`.
4. `docker compose up --build -d`
5. Дождаться `healthy` (оба контейнера) — 30 секунд.
6. Открыть `http://localhost:8000/` — витрина.

**Первый запуск занимает ~3 минуты** (сборка образа + миграции Alembic).

---

## 10. Мини-экономика

### До внедрения (ручной разбор)
- Разбор 1 текста: **10–15 минут**.
- Ошибки (пропущенное действие): ~5 минут последствий.
- **Итого: ~12–20 минут на текст.**

### После внедрения
- Вставка + «Извлечь»: **10 секунд**.
- Проверка и правка черновика: **2–4 минуты**.
- **Итого: ~2–4 минуты на текст.**

### Экономия на 100 текстов
| Показатель | До | После |
|---|---|---|
| Часы работы | ~20 ч | ~4 ч |
| **Экономия** | **~16 ч** | |
| В деньгах (1000 ₽/ч) | | **~16 000 ₽** |
| Затраты на LLM (gpt-4o-mini) | | **~40 ₽** |

**Вывод:** ценность очевидна. Стоимость LLM пренебрежимо мала
относительно экономии времени.

---

## 11. Риски и меры снижения (10 рисков)

| # | Риск | Мера |
|---|---|---|
| 1 | **LLM выдумывает цитаты** | Fuzzy-проверка `source_quote` (порог 0.85); при несовпадении → `critical` |
| 2 | **Неверные сроки** | `due_date_iso=null` при неоднозначности; `due_date_raw` сохраняется как есть |
| 3 | **Prompt injection** | System prompt с изоляцией данных + 9 regex-паттернов на бэкенде |
| 4 | **Утечка API-ключа** | `.env` вне git; редакция секретов в structlog |
| 5 | **Прокси недоступен** | Timeout 30 с; `status=error` в аудите; текст → `failed` |
| 6 | **Много ручных проверок** | Уровни `soft`/`critical`; `soft` подтверждается оптом |
| 7 | **SQLite под нагрузкой** | Выбран PostgreSQL + async SQLAlchemy |
| 8 | **Утечка секретов в логи** | structlog редактирует поля `*_key`, `password`, `token` |
| 9 | **Открытые порты в интернет** | Порты 8000/5432 закрыты на 127.0.0.1; UFW открывает только 22/80/443 |
| 10 | **Технический долг** | Repository + DIP + Alembic + 171 тест |

---

## 12. Три строки для портфолио

**Проблема:** Разбор писем и заметок на задачи отнимает 10–15 минут
на текст и не гарантирует полноту.

**Решение:** FastAPI + PostgreSQL + Repository + Alembic + `gpt-4o-mini`
через proxyapi.ru: строгий JSON, fuzzy-валидация цитат, защита от
prompt injection, статусная модель ручной проверки.

**Результат:** ~80% экономии времени, полный аудит каждого запуска,
воспроизводимый запуск через Docker за ≤ 10 минут, готовность к замене
БД и LLM без правок в сервисах.

---

## 13. Как запустить

**README:** `<repo-url>#readme` *(после публикации на GitHub)*

**Локально за ≤ 10 минут:**
```bash
git clone <repo-url> distil && cd distil
cp .env.example .env
# вставить LLM_API_KEY в .env
docker compose up --build -d
# открыть http://localhost:8000
```

**Публичный стенд:** <https://distil.ddns.net> *(Basic Auth — логин/пароль
по запросу)*

---

## 14. Демонстрация

**Публичный стенд:** <https://distil.ddns.net>

**Логин/пароль:** `admin` / по запросу куратору.

**Скриншоты** (папка `docs/screenshots/`):

| Файл | Что показывает |
|---|---|
| `00_https_verified.png` | Валидный SSL-сертификат Let's Encrypt |
| `01_vitrina.png` | Витрина текстов с фильтром и экспортом |
| `02_create_text.png` | Форма создания текста |
| `03_before_extract.png` | Карточка текста до извлечения |
| `04_after_extract.png` | Карточка с 4 извлечёнными действиями |
| `05_manual_review_soft.png` | Действия с `soft`-плашками |
| `06_manual_review_critical.png` | Действия с `critical`-плашками |
| `07_confirm_edit.png` | Подтверждение действия (`confirmed`) |
| `08_audit.png` | Аудит с раскрытым `input`/`output` JSON |
| `09_export_csv.png` | Экспорт в Excel — все колонки |
| `10_swagger.png` | Swagger UI со всеми endpoints |

**Видео-демонстрация:** отсутствует. Заменено публичным стендом +
11 скриншотами, покрывающими все ключевые сценарии.

---

## 15. Сложности и как решал

**1. Async SQLAlchemy + relationships.**
Столкнулся с `MissingGreenlet` при lazy-load в асинхронной сессии.
Решение: `selectinload` и явная загрузка — идиоматичный паттерн
в SQLAlchemy 2.0.

**2. Портативная типизация под SQLite.**
`BIGINT PRIMARY KEY` не автоинкрементируется в SQLite. Ввёл
`BigIntType = BigInteger().with_variant(Integer, "sqlite")` —
тесты быстрые, продакшн на Postgres.

**3. Prompt injection.**
Стандартных «жёстких промптов» недостаточно. Добавил два слоя:
маркеры `<<<USER_TEXT_START/END>>>` и regex-детектор на бэкенде
с флагом в аудите.

**4. Много ручных проверок убивает экономику.**
Изначально любая неуверенность уходила в `needs_review`. Ввёл два
уровня: `soft` (можно оптом) и `critical` (обязательная правка).

**5. Нормализация «до пятницы», «к среде».**
Модель часто не может преобразовать относительные сроки в ISO-дату.
Решение: сохранять `due_date_raw` (как написал автор) и ставить
`due_date_iso=null` с флагом `critical` — пользователь сам выберет
конкретную дату.

**6. Деплой с HTTPS.**
Caddy автоматически выпустил сертификат Let's Encrypt для
`distil.ddns.net`. Единственная сложность — домен от No-IP требует
подтверждения раз в 30 дней, учтено в плане.

**7. Закрытие портов от интернета.**
Docker пробрасывает порты раньше UFW. Решение: явное связывание
с `127.0.0.1` в `docker-compose.yml` (`127.0.0.1:8000:8000`).

---

## 16. План развития

- **Импорт PDF/DOCX** (`pypdf`, `python-docx`) — чтобы работать
  с документами, а не только с текстом.
- **Экспорт в Notion / Jira / Trello** — прямая интеграция вместо
  CSV/JSON.
- **Multi-user + RBAC** — разделение данных, роли.
- **Кэш результатов** по хешу текста — экономия на повторных запросах.
- **Векторный поиск** по архиву действий.
- **Метрика точности** извлечения — сравнение с эталонной разметкой.
- **Retention policy для `audit_runs`** — автоочистка через cron.
- **Prometheus `/metrics`** — наблюдаемость.
- **Integration-тесты на реальном PostgreSQL в CI.**

---

## 17. Стек и архитектура (для справки)

**Backend:** Python 3.11, FastAPI 0.115, Pydantic v2, SQLAlchemy 2.0
(async), Alembic, PostgreSQL 16.

**LLM:** OpenAI SDK → `proxyapi.ru`, модель `gpt-4o-mini` (allowlist
политика).

**Frontend:** Jinja2 + HTMX + Tailwind (CDN).

**Качество:** 171 тест (pytest), `ruff` (clean), `mypy --strict`
(no issues).

**Инфраструктура:** Docker multi-stage, docker-compose,
Caddy (HTTPS), UFW.

**Паттерны:**
- **Repository** — `TextRepositoryProtocol`, `ActionRepositoryProtocol`,
  `AuditRepositoryProtocol`.
- **Dependency Inversion** — сервисы зависят от Protocol'ов, не от
  SQLAlchemy / OpenAI SDK.
- **Domain layer** — frozen dataclass'ы без ORM.
- **Audit trail** — каждая операция в `audit_runs`.

---

## Итог

Проект — **MVP с промышленной архитектурой**. Развёрнут на публичном
сервере с HTTPS и Basic Auth. Покрыт 171 тестом, проходит `ruff`
и `mypy --strict`. Готов к развитию в продукт без переписывания ядра.

**Ключевой принцип:** LLM — ассистент, а не оракул. Там, где модель
не уверена, система честно просит ручную проверку.