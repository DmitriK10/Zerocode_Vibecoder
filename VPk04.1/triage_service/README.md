# 🤖 VPk04.1 Triage Service

[![CI Status](https://github.com/DmitriK10/Zerocode_Vibecoder/actions/workflows/triage-ci.yml/badge.svg)](https://github.com/DmitriK10/Zerocode_Vibecoder/actions/workflows/triage-ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)

**ИИ-сервис для первичной обработки обращений клиентов** с автоматической классификацией, генерацией черновиков ответов и эскалацией сложных случаев оператору.

---

## 📌 Функциональность

- ✅ **Классификация обращений** по категориям: `billing`, `support`, `complaint`, `other`
- ✅ **Генерация черновика ответа** (1–6 предложений) через LLM
- ✅ **Оценка уверенности** модели (`high`/`medium`/`low`)
- ✅ **Автоматическая эскалация** при низкой уверенности или ошибке LLM
- ✅ **Аудит всех операций** в SQLite (сохранение запросов и ответов)
- ✅ **Rate Limiting** (10 запросов в минуту на `client_id`)
- ✅ **Валидация данных** через Pydantic V2 с кастомными валидаторами

---

## 🏗️ Архитектура и технологии

### Стек
- **Backend**: FastAPI + Uvicorn
- **LLM**: OpenAI API (через ProxyAPI)
- **База данных**: SQLite (для аудита)
- **Контейнеризация**: Docker + Docker Compose
- **Тестирование**: pytest + pytest-cov
- **CI/CD**: GitHub Actions

### Структура проекта
VPk04.1
triage_service/
├── app/
│ ├── api/
│ │ └── routes.py # API эндпоинты
│ ├── core/
│ │ ├── config.py # Конфигурация
│ │ └── exceptions.py # Кастомные исключения
│ ├── llm/
│ │ └── llm_client.py # Интеграция с LLM
│ ├── models/
│ │ └── schemas.py # Pydantic модели
│ ├── repository/
│ │ └── db.py # Работа с БД
│ ├── services/
│ │ └── triage_service.py # Бизнес-логика
│ └── main.py # Точка входа
├── tests/
│ ├── conftest.py # Фикстуры pytest
│ └── test_api.py # API тесты
├── Dockerfile # Docker образ
├── docker-compose.yml # Оркестрация контейнеров
├── requirements.txt # Зависимости
└── README.md # Этот файл

### Вариант 1: Docker (Рекомендуемый)

**Преимущества:** Изолированное окружение, сохранение данных между перезапусками, готовность к продакшену.

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/DmitriK10/Zerocode_Vibecoder.git
cd Zerocode_Vibecoder/VPk04_triage_service

# 2. Создайте .env файл из шаблона
cp .env.example .env

# 3. Отредактируйте .env и добавьте ваш OPENAI_API_KEY
# nano .env  # или любой другой редактор

# 4. Запустите сервис
docker-compose up --build -d

# 5. Проверьте, что сервис работает
curl http://localhost:8000/docs

bash
docker-compose down

### Вариант 2: Локальный запуск (для разработки)
bash

Сервис будет доступен по адресу: http://localhost:8000
📡 API Документация
Эндпоинт: POST /api/v1/triage
Описание: Принимает текст обращения, классифицирует его и генерирует черновик ответа.
Запрос (Request)
Headers:

Body (JSON):
json

Поля:
text (string, required): Текст обращения (1–2000 символов, не может быть пустым)
channel (string, required): Канал обращения. Допустимые значения: "email", "form", "chat"
client_id (string, required): Уникальный ID клиента
Ответ (Response)
Успех (200 OK):
json

Поля:
category (string): Категория обращения (billing, support, complaint, other)
draft_reply (string): Черновик ответа (1–6 предложений)
confidence (string): Уверенность модели (high, medium, low)
escalate (boolean): Флаг эскалации оператору (true при низкой уверенности или ошибке)
Ошибки:
422 Unprocessable Entity — невалидные данные (пустой текст, неверный channel)
429 Too Many Requests — превышен rate limit (10 запросов/мин на client_id)
500 Internal Server Error — внутренняя ошибка сервера
🧪 Тестирование
Проект покрыт автотестами с использованием pytest.
bash

Тестовые сценарии:
✅ Успешная обработка запроса
✅ Валидация пустого текста (422)
✅ Rate Limiting (429)
🗄️ Работа с базой данных
После первого запроса создается файл tickets.db с таблицей аудита.
Просмотр всех записей:
bash

Структура таблицы:
sql

🏆 Инженерные стандарты проекта
✅ Строгая типизация: Pydantic V2 с field_validator для гарантии целостности данных
✅ Разделение ответственности: Четкое разделение на слои (API / Service / Repository / LLM)
✅ Автотесты: Покрытие ключевых сценариев через pytest + TestClient
✅ Контейнеризация: Готовый Dockerfile и docker-compose.yml с сохранением состояния
✅ CI/CD: Автоматический прогон тестов при каждом push через GitHub Actions
✅ Логирование: Структурированные логи с уровнем INFO
✅ Обработка ошибок: Кастомные исключения с понятными сообщениями
🌐 Развёртывание на сервере
Сервис готов к деплою на любой VPS с Docker.
Пример для Reg.ru / Timeweb / DigitalOcean:
bash

Публичный адрес примера: http://80.78.247.11/api/v1/triage
📝 Переменные окружения
Создайте файл .env на основе .env.example:
env

🐛 Troubleshooting
Проблема: sqlite3.OperationalError: unable to open database file
Решение: Проверьте права доступа к папке проекта. В Docker это решается автоматически через volumes.
Проблема: openai.APIConnectionError
Решение: Проверьте OPENAI_API_KEY и OPENAI_BASE_URL в .env файле.
Проблема: Порт 8000 уже занят
Решение: Измените порт в docker-compose.yml или при запуске uvicorn --port 8001.
📊 Метрики производительности
Среднее время ответа: 1.5–3 сек (зависит от LLM)
Пропускная способность: ~30 req/min (при rate limit 10/client)
Использование памяти: ~150 MB (Docker контейнер)
📜 Лицензия
MIT License. См. файл LICENSE в корне репозитория.
👨‍💻 Автор
Проект разработан в рамках курса "Профессия Вайб-кодер" от ZeroCoder.
Контакты:
GitHub: @DmitriK10
Email: d.kupriyanyuk@gmail.com