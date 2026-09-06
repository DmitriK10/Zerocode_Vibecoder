markdown
# OrderPort — Система приёма и обработки заказов

OrderPort — это защищённый веб-стек для сбора заявок от клиентов с автоматическим сбором метрик и интеграцией с GPT через прокси-сервис. Проект представляет собой готовое к деплою решение на базе FastAPI, PostgreSQL, Nginx и Docker Compose. Все сервисы изолированы в контейнерах, бэкенд не доступен извне, данные клиентов хранятся локально.

## Возможности

- Приём заявок через публичную форму (имя, телефон, email, ниша бизнеса, размер компании, бюджет и др.)
- Авторизация администратора через JWT-токены (логин/пароль, регистрация первого админа)
- Панель администратора с CRUD-операциями для услуг (добавление, редактирование, удаление)
- Просмотр заявок с интеллектуальной приоритизацией (на основе ниши, размера компании, объёма задачи, бюджета)
- Сбор поведенческих метрик: время на странице, клики, прокрутка, координаты курсора (heatmap)
- Интеграция с OpenAI GPT через прокси (модель строго ограничена `gpt-3.5-turbo-16k`)
- Контейнеризация через Docker Compose (PostgreSQL, Backend, Nginx)
- Модульные тесты (pytest + pytest-asyncio)

## Технологический стек

| Компонент | Технология |
|-----------|------------|
| Backend | Python 3.11, FastAPI, SQLAlchemy (async) |
| База данных | PostgreSQL 15 (Docker) / SQLite (локально) |
| Прокси-сервер | Nginx (проксирует API и отдаёт статику) |
| Контейнеризация | Docker + Docker Compose |
| Аутентификация | JWT (python-jose), пароли хешируются (pbkdf2_sha256) |
| GPT-интеграция | proxyapi.ru (OpenAI-совместимый прокси) |
| Фронтенд | Vanilla HTML + CSS + JavaScript |
| Тестирование | pytest, pytest-asyncio, SQLite in-memory |

## Структура проекта
OrderPort/
├── app/
│ ├── init.py
│ ├── main.py # Точка входа FastAPI (lifespan)
│ ├── config.py # Настройки из .env (pydantic-settings)
│ ├── database.py # Подключение к БД (SQLAlchemy async)
│ ├── models.py # Модели SQLAlchemy (Lead, AdminSettings, BehaviorMetrics, Admin)
│ ├── schemas.py # Pydantic-схемы
│ ├── dependencies.py # DI для GPT-клиента и текущего администратора
│ ├── api/
│ │ └── v1/
│ │ ├── init.py
│ │ ├── endpoints.py # Все эндпоинты /api/v1/
│ │ └── auth.py # Эндпоинты /api/auth/
│ ├── services/
│ │ ├── init.py
│ │ ├── lead_service.py # CRUD для заявок + приоритизация
│ │ ├── admin_settings_service.py # CRUD для услуг
│ │ ├── behavior_metrics_service.py # CRUD для метрик
│ │ ├── auth_service.py # Хеширование паролей, JWT
│ │ └── gpt_proxy_service.py # Взаимодействие с GPT-прокси
│ └── static/
│ ├── index.html # Главная страница с формой заявки
│ └── admin.html # Админ-панель
├── tests/
│ ├── conftest.py # Фикстуры и подмена движка БД
│ ├── test_api.py # Тесты API-эндпоинтов
│ ├── test_auth.py # Тесты аутентификации
│ ├── test_admin_settings.py # Тесты сервиса услуг
│ ├── test_behavior_metrics.py # Тесты сервиса метрик
│ ├── test_gpt_proxy.py # Тесты GPT-прокси
│ └── test_lead.py # Тесты LeadService
├── docker-compose.yml # Оркестрация сервисов
├── Dockerfile # Сборка образа бэкенда
├── nginx/
│ └── nginx.conf # Конфигурация Nginx (прокси + статика + безопасность)
├── requirements.txt # Зависимости Python
├── .env.example # Шаблон переменных окружения
└── README.md

text

## Установка и запуск

### Локальный запуск (без Docker)

Требования: Python 3.11+, виртуальное окружение.

1. Клонируйте репозиторий и перейдите в папку проекта:
   ```bash
   git clone <url-репозитория> OrderPort
   cd OrderPort
Создайте виртуальное окружение и активируйте его:

bash
python -m venv venv --upgrade-deps
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows
Установите зависимости:

bash
pip install -r requirements.txt
Скопируйте .env.example в .env и отредактируйте:

bash
cp .env.example .env
Для локальной разработки с SQLite укажите DATABASE_URL=sqlite+aiosqlite:///./orderport.db

Для PostgreSQL настройте соответствующие переменные и DATABASE_URL.

Обязательно сгенерируйте надёжный SECRET_KEY (например, python -c "import secrets; print(secrets.token_hex(32))").

Запустите приложение:

bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
Откройте в браузере:

Главная страница: http://localhost:8000

Админ-панель: http://localhost:8000/admin.html

Swagger UI: http://localhost:8000/docs

Примечание: При первом запуске в админ-панели отобразится форма регистрации администратора. После создания первого админа кнопка регистрации исчезает.

Запуск через Docker Compose (рекомендуется для продакшена)
Требования: Docker ≥ 24.x и Docker Compose ≥ 2.x.

Скопируйте проект на сервер или клонируйте репозиторий.

Создайте .env на основе .env.example и заполните все поля (пароли, SECRET_KEY, ключ GPT-прокси).

Запустите контейнеры:

bash
docker compose up -d --build
Сервисы будут доступны:

Сайт: http://<IP-адрес>

Swagger: http://<IP-адрес>/docs

Внимание: В docker-compose.yml порт 8000 и 5432 не публикуются наружу — только Nginx (порт 80) доступен извне.

Переменные окружения (.env)
Переменная	Описание	Пример
POSTGRES_USER	Пользователь БД	postgres
POSTGRES_PASSWORD	Пароль БД	secure_password
POSTGRES_DB	Имя базы	orderport
POSTGRES_HOST	Хост БД (внутри Docker)	postgres
POSTGRES_PORT	Порт БД	5432
DATABASE_URL	Полная строка подключения (переопределяет отдельные параметры)	postgresql+asyncpg://postgres:pass@postgres:5432/orderport
APP_HOST	Хост приложения	0.0.0.0
APP_PORT	Порт приложения	8000
DEBUG	Режим отладки (в проде должен быть False)	False
SECRET_KEY	Секретный ключ для JWT (минимум 32 символа)	генерируется
ALGORITHM	Алгоритм подписи JWT	HS256
ACCESS_TOKEN_EXPIRE_MINUTES	Время жизни токена	30
OPENAI_API_BASE	Базовый URL GPT-прокси	https://proxypi.ru/v1
OPENAI_API_KEY	Ключ для GPT-прокси	sk-...
OPENAI_MODEL	Модель GPT (строго gpt-3.5-turbo-16k)	gpt-3.5-turbo-16k
OPENAI_MAX_TOKENS	Лимит токенов	4000
API Эндпоинты
Базовый префикс: /api/v1

Метод	Путь	Описание	Доступ
POST	/leads/	Создание заявки	Публичный
GET	/leads/	Список заявок (сортировка по приоритету опционально)	Только админ
GET	/leads/{lead_id}	Получить заявку	Только админ
POST	/leads/{lead_id}/analyze	Анализ заявки через GPT	Только админ
POST	/admin-settings/	Добавить услугу	Только админ
GET	/admin-settings/	Список услуг	Публичный
GET	/admin-settings/{id}	Получить услугу	Только админ
PUT	/admin-settings/{id}	Обновить услугу	Только админ
DELETE	/admin-settings/{id}	Удалить услугу	Только админ
POST	/behavior-metrics/	Сохранить метрики	Публичный
GET	/behavior-metrics/	Список метрик	Только админ
GET	/behavior-metrics/by-lead/{lead_id}	Метрики по заявке	Только админ
Эндпоинты авторизации (/api/auth):

POST /register — регистрация первого админа (доступна только если админов нет)

POST /login — вход (возвращает JWT)

GET /me — текущий админ

GET /check — проверка наличия админов

Полная документация доступна в Swagger UI (/docs).

Админ-панель
Заявки: таблица с приоритетом (горячие — вверху), кнопка «Просмотр» открывает детали.

Услуги: CRUD-таблица (добавление, редактирование, удаление).

Метрики: список поведенческих метрик + кнопка «Статистика» для просмотра heatmap.

Сбор метрик
Главная страница собирает:

время на странице (мс),

количество кликов,

глубину прокрутки (в %),

координаты курсора (не более 500 точек).

Каждые 100 мс добавляется точка текущей позиции мыши. При отправке заявки метрики передаются в POST /api/v1/behavior-metrics/.

Тестирование
Все тесты используют SQLite in-memory и не требуют внешней БД.

bash
# Активируйте виртуальное окружение
pytest tests/ -v
Покрытие:

API эндпоинты (создание/просмотр заявок, доступность по ролям)

Аутентификация (регистрация, логин, проверка токена)

Сервисы (LeadService, AdminSettingsService, BehaviorMetricsService)

GPT-прокси (успешный ответ, ошибки, ограничение модели)

Деплой на сервер
Подготовьте сервер с Docker и Docker Compose.

Скопируйте проект в /opt/OrderPort (или другую директорию).

Создайте .env и заполните все переменные.

Запустите:

bash
cd /opt/OrderPort
docker compose up -d --build
Убедитесь, что порты 80 (HTTP) открыты, а 8000 и 5432 закрыты извне.

HTTPS:** Если у вас есть домен, можно настроить Let's Encrypt через certbot.  
Для чистого IP-адреса Let's Encrypt не выдаёт сертификаты — используйте самоподписанный или облачный прокси (например, **Cloudflare**). Cloudflare предоставляет бесплатные SSL-сертификаты и не требует домена (работает через свой прокси).

Безопасность
Бэкенд и БД не доступны извне (только внутренняя сеть Docker).

Все запросы проходят через Nginx.

Пароли хешируются (PBKDF2-SHA256).

JWT-токены подписываются секретным ключом.

CORS разрешён для всех доменов (рекомендуется ограничить в проде).

Заголовки безопасности: X-Frame-Options, X-Content-Type-Options, Referrer-Policy и др.

Лицензия
Проект предназначен для учебных целей и не предназначен для коммерческого использования без доработок. Все права принадлежат автору.

Автор
Проект разработан в рамках курса «Вайбкодер» (ZeroCoder).
GitHub: DmitriK10/Zerocode_Vibecoder

