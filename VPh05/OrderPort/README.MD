OrderPort — Система приёма и обработки заказов
https://img.shields.io/badge/FastAPI-0.115.6-009688?logo=fastapi
https://img.shields.io/badge/Python-3.11-3776AB?logo=python
https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql
https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker

OrderPort — это защищённый веб-стек для сбора заявок от клиентов с автоматическим сбором метрик и интеграцией с GPT через прокси-сервис. Проект представляет собой готовое к деплою решение на базе FastAPI, PostgreSQL, Nginx и Docker Compose. Все сервисы изолированы в контейнерах, бэкенд не доступен извне, данные клиентов хранятся локально.

Серверная версия развёрнута и доступна по адресу:
➡️ http://157.228.140.78
📚 Swagger: http://157.228.140.78/docs
🐘 pgAdmin: http://157.228.140.78:5050 (логин/пароль из .env)

🧰 Технологический стек
Компонент	Технология
Backend	Python 3.11, FastAPI, SQLAlchemy (async)
База данных	PostgreSQL 15
Прокси	Nginx (проксирует запросы на бэкенд)
Контейнеризация	Docker + Docker Compose
Администрирование БД	pgAdmin
Регистр образов	Локальный Docker Registry
Внешний API	proxypi.ru (GPT‑3.5‑turbo‑16k)
Тестирование	pytest, pytest-asyncio, SQLite in-memory
Сборка фронтенда	Vanilla HTML + CSS + JavaScript
📁 Структура проекта
text
OrderPort/
├── docker-compose.yml          # Оркестрация всех сервисов
├── .env.example                 # Шаблон переменных окружения
├── Dockerfile                   # Сборка образа бэкенда
├── requirements.txt             # Зависимости Python
├── README.md                    # Документация
├── nginx/
│   └── nginx.conf               # Конфигурация Nginx (прокси на бэкенд)
├── app/
│   ├── __init__.py
│   ├── main.py                  # Точка входа FastAPI (lifespan)
│   ├── config.py                # Загрузка настроек из .env
│   ├── database.py              # Подключение к БД (SQLAlchemy async)
│   ├── models.py                # Модели SQLAlchemy
│   ├── schemas.py               # Pydantic-схемы
│   ├── dependencies.py          # DI для GPT-клиента
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints.py     # Все эндпоинты /api/v1/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── lead_service.py      # CRUD для заявок
│   │   ├── admin_settings_service.py  # CRUD для услуг
│   │   ├── behavior_metrics_service.py # CRUD для метрик
│   │   └── gpt_proxy_service.py # Взаимодействие с proxypi.ru
│   └── static/
│       └── index.html           # Главная страница с формой
└── tests/                       # Модульные тесты
    ├── conftest.py              # Фикстуры и подмена движка БД
    ├── test_api.py              # Тесты эндпоинтов
    ├── test_gpt_proxy.py        # Тесты GPT-сервиса
    └── test_lead.py             # Тесты LeadService
🚀 Установка и запуск (локально)
Требования
Docker ≥ 24.x и Docker Compose ≥ 2.x

Git (опционально)

1. Клонирование репозитория
bash
git clone <url-репозитория> OrderPort
cd OrderPort
2. Настройка переменных окружения
Скопируйте .env.example в .env и отредактируйте:

bash
cp .env.example .env
nano .env
Обязательно задайте:

POSTGRES_PASSWORD — надёжный пароль для БД

OPENAI_API_KEY — ваш ключ для доступа к proxypi.ru

PGADMIN_DEFAULT_PASSWORD — пароль для pgAdmin

3. Запуск контейнеров
bash
docker compose up -d --build
После запуска будут доступны:

Сайт: http://localhost

Swagger: http://localhost/docs

pgAdmin: http://localhost:5050

4. Проверка работоспособности
bash
curl http://localhost/api/v1/leads/
# [] (пустой массив)

curl -X POST http://localhost/api/v1/leads/ \
  -H "Content-Type: application/json" \
  -d '{"contact_data":{"name":"Тест","phone":"123"}}'
# {"id":1,"contact_data":{...}}
⚙️ Переменные окружения (.env)
Переменная	Описание	Пример
POSTGRES_USER	Пользователь БД	postgres
POSTGRES_PASSWORD	Пароль БД	secure_password
POSTGRES_DB	Имя базы	orderport
POSTGRES_HOST	Хост БД (внутри Docker)	postgres
POSTGRES_PORT	Порт БД	5432
APP_HOST	Хост приложения	0.0.0.0
APP_PORT	Порт приложения	8000
DEBUG	Режим отладки	False
OPENAI_API_BASE	URL GPT-прокси	https://proxypi.ru/v1
OPENAI_API_KEY	Ключ для прокси	sk-...
OPENAI_MODEL	Модель GPT	gpt-3.5-turbo-16k
OPENAI_MAX_TOKENS	Лимит токенов	4000
PGADMIN_DEFAULT_EMAIL	Логин pgAdmin	admin@example.com
PGADMIN_DEFAULT_PASSWORD	Пароль pgAdmin	admin
DATABASE_URL (необяз.)	Полная строка подключения	postgresql+asyncpg://...
🔌 API Эндпоинты
Базовый префикс: /api/v1

Метод	Путь	Описание	Тело запроса	Ответ
POST	/leads/	Создание заявки	LeadCreate	LeadResponse
GET	/leads/	Список заявок	–	List[LeadResponse]
GET	/leads/{lead_id}	Получить заявку	–	LeadResponse
POST	/leads/{lead_id}/analyze	Анализ через GPT	–	AnalysisResponse
POST	/admin-settings/	Добавить услугу	AdminSettingsCreate	AdminSettingsResponse
GET	/admin-settings/	Список услуг	–	List[AdminSettingsResponse]
GET	/admin-settings/{id}	Получить услугу	–	AdminSettingsResponse
PUT	/admin-settings/{id}	Обновить услугу	AdminSettingsCreate	AdminSettingsResponse
DELETE	/admin-settings/{id}	Удалить услугу	–	{"ok": true}
POST	/behavior-metrics/	Сохранить метрики	BehaviorMetricsCreate	BehaviorMetricsResponse
GET	/behavior-metrics/	Список метрик	–	List[BehaviorMetricsResponse]
GET	/behavior-metrics/by-lead/{lead_id}	Метрики по заявке	–	BehaviorMetricsResponse
Все схемы описаны в app/schemas.py и видны в Swagger.

🧪 Тестирование
Для запуска тестов (локально, с SQLite in-memory):

bash
# Активируйте виртуальное окружение
python -m venv venv
source venv/bin/activate  # или .\venv\Scripts\activate

# Установите зависимости
pip install -r requirements.txt

# Запустите тесты
pytest tests/ -v
Тесты покрывают:

CRUD операций (Lead, AdminSettings, BehaviorMetrics)

API-эндпоинты (проверка статусов и данных)

GPT-прокси (mock-запросы)

Обработку ошибок (404, 500)

🌐 Деплой на сервер
1. Подготовка сервера
Установите Docker и Docker Compose

Убедитесь, что порты 80, 5050 свободны

Установите Git (опционально)

2. Копирование проекта
bash
scp -r ./OrderPort root@<IP_сервера>:/opt/
3. Настройка .env и запуск
bash
cd /opt/OrderPort
cp .env.example .env
nano .env   # заполните реальными значениями
docker compose up -d --build
4. Проверка
bash
curl http://<IP_сервера>/api/v1/leads/
5. Обновление кода
bash
docker compose down
git pull   # или скопируйте новые файлы
docker compose up -d --build
🔒 Безопасность
Бэкенд не доступен извне (порт 8000 не открыт)

Все запросы идут через Nginx (прокси)

Данные клиентов хранятся локально

Пароли и ключи хранятся в .env (не включены в репозиторий)

GPT-прокси использует HTTPS

Рекомендуется отключить DEBUG в продакшене

📦 Дополнительные сервисы
pgAdmin — веб-интерфейс управления БД: http://<IP>:5050

Docker Registry — локальный реестр образов (порт 5000)

Watchtower — автоматическое обновление контейнеров (опционально)

📊 Модели данных
Lead (заявка)
id, contact_data (JSON), business_info, budget, preferred_contact, comments

user_agent, ip_address, referer, session_id, page_load_time

service_id (FK → admin_settings)

created_at, updated_at

AdminSettings (услуги)
id, services (название), budget_range

created_at, updated_at

BehaviorMetrics (поведенческие метрики)
id, lead_id (FK → leads, уникальный)

page_load_time, session_duration, clicks, scroll_depth, other_metrics (JSON)

created_at

🛠️ Возможные проблемы и их решения
Ошибка	Причина	Решение
502 Bad Gateway	Nginx не видит бэкенд	Убедитесь, что backend запущен; проверьте сеть
404 Not Found	Эндпоинт не зарегистрирован	Проверьте, что код обновлён и пересобран
ResponseValidationError	Поле created_at равно NULL	Добавьте DEFAULT NOW() в БД вручную
ModuleNotFoundError	Структура папок неверна	Проверьте Dockerfile (копируйте app/ ./app/)
👥 Автор
Проект разработан в рамках курса «Вайбкодер» (ZeroCoder).
GitHub: DmitriK10/Zerocode_Vibecoder

📝 Лицензия
Проект предназначен для учебных целей и не предназначен для коммерческого использования без доработок. Все права принадлежат автору.

Ссылка на серверную версию: http://157.228.140.78
Swagger: http://157.228.140.78/docs
pgAdmin: http://157.228.140.78:5050