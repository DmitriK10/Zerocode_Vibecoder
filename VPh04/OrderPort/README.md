OrderPort — Система приёма и обработки заказов (MVP)
OrderPort — это защищённый веб-стек для сбора заявок от клиентов с автоматическим сбором метрик и интеграцией с GPT через прокси-сервис. Проект представляет собой готовое к деплою решение на базе FastAPI, PostgreSQL, Nginx и Docker Compose. Все сервисы изолированы в контейнерах, бэкенд не доступен извне, данные клиентов хранятся локально.

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
📦 Требования к окружению
Сервер: Ubuntu 22.04 / 24.04 (или аналогичный Linux)

Установленные пакеты:

Docker (≥ 24.x) и Docker Compose (≥ 2.x)

Git (опционально)

Открытые порты (по умолчанию):

80 — HTTP (сайт)

5050 — pgAdmin

5000 — локальный Docker Registry (внутри сети, можно не публиковать наружу)

Домен/IP для доступа к сайту.

🚀 Быстрый старт
1. Клонирование репозитория
bash
git clone <url-репозитория> OrderPort
cd OrderPort
2. Настройка переменных окружения
Скопируйте шаблон .env.example в .env и отредактируйте его:

bash
cp .env.example .env
nano .env
Обязательно задайте:

POSTGRES_PASSWORD — надёжный пароль для БД.

OPENAI_API_KEY — ваш ключ для доступа к прокси (proxypi.ru).

PGADMIN_DEFAULT_PASSWORD — пароль для входа в pgAdmin.

3. Запуск контейнеров
bash
docker compose up -d
После запуска будут доступны:

Сайт: http://<ваш-сервер>/

pgAdmin: http://<ваш-сервер>:5050/ (логин/пароль из .env)

Docker Registry: http://<ваш-сервер>:5000/v2/ (внутри сети)

4. Проверка работоспособности
bash
curl http://<ваш-сервер>/api/v1/leads/
# Должен вернуться пустой массив []

curl -X POST http://<ваш-сервер>/api/v1/leads/ \
  -H "Content-Type: application/json" \
  -d '{"contact_data":{"name":"Тест","phone":"123"}}'
# Ожидаемый ответ: {"id":1,"contact_data":{...}}
📁 Структура проекта
text
OrderPort/
├── docker-compose.yml          # Оркестрация всех сервисов
├── .env.example                 # Шаблон переменных окружения
├── Dockerfile                   # Сборка образа бэкенда
├── requirements.txt             # Зависимости Python
├── README.md                    # Документация (этот файл)
├── nginx/
│   └── nginx.conf               # Конфигурация Nginx (прокси на бэкенд)
├── app/
│   ├── __init__.py
│   ├── main.py                  # Точка входа FastAPI
│   ├── config.py                # Настройки приложения (загрузка из .env)
│   ├── database.py              # Подключение к БД (SQLAlchemy async)
│   ├── models.py                # Модели SQLAlchemy
│   ├── schemas.py               # Pydantic-схемы для валидации/сериализации
│   ├── dependencies.py          # Фабрики зависимостей (например, GPT-сервис)
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints.py     # Эндпоинты /api/v1/leads/ и /analyze
│   ├── services/
│   │   ├── __init__.py
│   │   ├── lead_service.py      # CRUD для заявок
│   │   └── gpt_proxy_service.py # Взаимодействие с proxypi.ru
│   └── static/
│       └── index.html           # Главная страница с формой сбора заявок
└── tests/                       # Модульные тесты
    ├── conftest.py              # Фикстуры и подмена движка БД
    ├── test_api.py              # Тесты эндпоинтов
    ├── test_gpt_proxy.py        # Тесты GPT-сервиса
    └── test_lead.py             # Тесты LeadService
⚙️ Конфигурация (переменные окружения)
Файл .env содержит все настройки приложения. Ниже приведён полный список переменных:

Переменная	Описание	Пример
POSTGRES_USER	Пользователь БД	postgres
POSTGRES_PASSWORD	Пароль БД	secure_password
POSTGRES_DB	Имя базы данных	orderport
POSTGRES_HOST	Хост БД (внутри Docker-сети)	postgres
POSTGRES_PORT	Порт БД	5432
APP_HOST	Хост для приложения (внутри контейнера)	0.0.0.0
APP_PORT	Порт приложения (внутри контейнера)	8000
DEBUG	Режим отладки (True/False)	False
OPENAI_API_BASE	Базовый URL для GPT-прокси	https://proxypi.ru/v1
OPENAI_API_KEY	Ключ для доступа к прокси	sk-...
OPENAI_MODEL	Модель (принудительно ограничена)	gpt-3.5-turbo-16k
OPENAI_MAX_TOKENS	Лимит токенов на ответ	4000
PGADMIN_DEFAULT_EMAIL	Логин для pgAdmin	admin@example.com
PGADMIN_DEFAULT_PASSWORD	Пароль для pgAdmin	admin
DATABASE_URL (необязательно)	Полная строка подключения (переопределяет компоненты)	postgresql+asyncpg://...
🔌 API эндпоинты
Базовый префикс: /api/v1

Метод	Путь	Описание	Тело запроса	Ответ
POST	/leads/	Создание новой заявки	LeadCreate (см. schemas.py)	LeadResponse (id, контакты, дата)
GET	/leads/	Получение списка всех заявок	–	List[LeadResponse]
GET	/leads/{lead_id}	Получение одной заявки по ID	–	LeadResponse или 404
POST	/leads/{lead_id}/analyze	Анализ заявки через GPT	–	{"lead_id": ..., "analysis": ...}
Все эндпоинты возвращают JSON.

🧪 Тестирование
Для запуска тестов (локально, с SQLite in-memory):

bash
# Активируйте виртуальное окружение (если создано)
source venv/bin/activate  # или .\venv\Scripts\activate для Windows

# Установите тестовые зависимости
pip install -r requirements.txt

# Запустите тесты
pytest tests/ -v
Все тесты должны проходить успешно.

🛠 Дополнительные сервисы
pgAdmin
Веб-интерфейс для управления PostgreSQL доступен по адресу: http://<ваш-сервер>:5050/.
Логин/пароль задаются в .env. После входа добавьте сервер с параметрами:

Host: postgres

Port: 5432

Maintenance database: orderport

Username: postgres

Пароль: (из .env)

Локальный Docker Registry
Регистр образов работает внутри сети контейнеров на порту 5000.
Для использования (например, для автодеплоя) соберите образ бэкенда и запушите его:

bash
docker build -t localhost:5000/orderport_backend:latest .
docker push localhost:5000/orderport_backend:latest
Затем в docker-compose.yml можно заменить build на image: localhost:5000/orderport_backend:latest.

Watchtower (опционально)
Сервис для автоматического обновления контейнеров при появлении новых образов. Включён в docker-compose.yml, но может быть отключён или удалён по желанию.

🔒 Безопасность
Backend не доступен извне: порт 8000 не опубликован на хост.

Все запросы идут через Nginx, который выступает обратным прокси.

Данные клиентов не покидают сервер: вся информация хранится в локальной БД.

Пароли и ключи хранятся только в .env (не включены в репозиторий).

GPT-прокси использует внешний сервис, но все данные передаются по HTTPS.

📝 Лицензия
Проект разработан в рамках учебного задания и не предназначен для коммерческого использования. Все права принадлежат автору.

👥 Автор
Разработано в рамках курса «Вайбкодер» (ZeroCoder).

https://github.com/DmitriK10/Zerocode_Vibecoder

