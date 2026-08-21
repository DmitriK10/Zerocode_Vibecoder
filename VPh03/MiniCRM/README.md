📊 Мини-CRM
Мини-CRM — это настольное приложение для управления клиентами, сделками и задачами с возможностью автоматической выгрузки аналитических отчётов в Google Sheets. Проект построен на Python с использованием FastAPI (бэкенд) и Tkinter (графический интерфейс), интегрирован с Google Drive API и Google Sheets API через OAuth2 и сервисный аккаунт.

✨ Основные возможности
Управление клиентами (CRUD)

Управление сделками (CRUD)

Управление задачами (CRUD)

Выгрузка отчётов по клиентам, сделкам и задачам в Google Sheets

Автоматическая аналитика в отчётах (количество, суммы, статусы)

Локальное хранение данных в SQLite

REST API с документацией Swagger

Десктопный интерфейс на Tkinter

Логирование всех ключевых операций в файл и консоль

Защищённое хранение OAuth-токенов (в папке ~/.crm/)

🛠️ Стек технологий
Компонент	Технология
Backend	Python 3.11+, FastAPI, SQLAlchemy, SQLite
Frontend	Tkinter (десктопное GUI)
Интеграция с Google	Google API Client (Drive, Sheets), OAuth2, сервисный аккаунт
Тестирование	pytest
Логирование	Python logging (в файл и консоль)
Контейнеризация	Docker / Podman (опционально)
Управление зависимостями	pip + requirements.txt
📁 Структура проекта
text
MiniCRM/
├── backend/                     # Бэкенд (FastAPI)
│   ├── __init__.py
│   ├── main.py                 # Точка входа, эндпоинты
│   ├── models.py               # SQLAlchemy модели
│   ├── schemas.py              # Pydantic схемы
│   ├── crud.py                 # CRUD-операции
│   ├── database.py             # Настройка БД
│   ├── repositories.py         # Репозитории (доступ к данным)
│   └── services.py             # Бизнес-логика
├── gui/                         # Графический интерфейс (Tkinter)
│   ├── __init__.py
│   ├── main_window.py          # Главное окно
│   ├── clients_window.py       # Окно клиентов
│   ├── deals_window.py         # Окно сделок
│   ├── tasks_window.py         # Окно задач
│   ├── settings_window.py      # Настройки Google
│   ├── base_table_window.py    # Базовый класс для таблиц
│   ├── forms.py                # Диалоговые формы
│   ├── api_client.py           # HTTP-клиент для бэкенда
│   ├── google_reporter.py      # Выгрузка отчётов
│   └── google_config.py        # Загрузка настроек Google
├── google_integration/          # Интеграция с Google API
│   ├── __init__.py
│   ├── auth.py                 # Аутентификация (OAuth2 + сервисный аккаунт)
│   ├── drive_client.py         # Клиент для Google Drive
│   ├── sheets_client.py        # Клиент для Google Sheets
│   └── google_drive.py         # (устаревший, оставлен для совместимости)
├── tests/                       # Тесты (pytest)
│   ├── test_backend.py
│   ├── unit/
│   │   ├── test_crud.py
│   │   ├── test_repositories.py
│   │   └── test_google_drive.py
│   └── integration/
│       └── fill_test_data.py   # Генерация тестовых данных
├── data/                        # Папка для SQLite БД (создаётся автоматически)
├── logs/                        # Папка для логов (создаётся автоматически)
├── config.py                    # Конфигурация (загрузка .env)
├── logger.py                    # Настройка логирования
├── run_gui.py                   # Точка входа для GUI
├── start_backend.py             # Точка входа для бэкенда
├── run_all_tests.py             # Запуск всех тестов
├── fill_test_data.py            # Генерация тестовых данных
├── requirements.txt             # Зависимости
├── .env.example                 # Шаблон переменных окружения
├── .env                         # Переменные окружения (создаётся вручную)
└── README.md                    # Этот файл
🚀 Установка и запуск
1. Клонирование репозитория
bash
git clone https://github.com/your-username/mini-crm.git
cd mini-crm
2. Создание виртуального окружения
bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate          # Windows
3. Установка зависимостей
bash
pip install -r requirements.txt
4. Настройка Google Cloud
Создайте проект в Google Cloud Console.

Включите API: Google Drive API и Google Sheets API.

Создайте OAuth 2.0 клиент (тип "Desktop app"):

Скачайте client_secret.json и поместите в папку google_integration/.

Добавьте свой email в тестовые пользователи (OAuth consent screen → Test users).

Создайте сервисный аккаунт:

Скачайте credentials_service.json и поместите в google_integration/.

Дайте сервисному аккаунту доступ к папке на Google Drive (поделитесь папкой с email сервисного аккаунта с правами "Редактор").

Скопируйте ID папки для отчётов из адресной строки Google Drive.

5. Настройка переменных окружения
Скопируйте .env.example в .env и заполните:

env
# Google API
GOOGLE_SERVICE_ACCOUNT_FILE=./google_integration/credentials_service.json
GOOGLE_OAUTH_CLIENT_FILE=./google_integration/client_secret.json
GOOGLE_FOLDER_ID=your_google_drive_folder_id_here

# Backend
BACKEND_URL=http://localhost:8000

# Debug
DEBUG=False
Примечание: token.pickle автоматически создаётся в ~/.crm/token.pickle после первой авторизации OAuth2.

6. Запуск бэкенда
bash
python start_backend.py
Сервер будет доступен по адресу: http://localhost:8000
Swagger-документация: http://localhost:8000/docs

7. Запуск GUI (в другом терминале)
bash
python run_gui.py
Откроется главное окно приложения.

🖥️ Использование
Главное окно
Управление клиентами – добавление, редактирование, удаление клиентов.

Управление сделками – добавление, редактирование, удаление сделок.

Управление задачами – добавление, редактирование, удаление задач.

Настройки Google – указание путей к ключам и ID папки для отчётов.

Выгрузка отчётов
Откройте любое окно (Клиенты / Сделки / Задачи).

Нажмите кнопку «Выгрузить отчёт».

При первом запуске браузер запросит авторизацию в Google – войдите и разрешите доступ.

После успешной выгрузки откроется ссылка на новую Google Таблицу с аналитикой.

🧪 Тестирование
Запуск всех тестов:

bash
python run_all_tests.py
Или через pytest напрямую:

bash
pytest tests/ -v
📊 Логирование
Логи пишутся в:

Консоль (в реальном времени)

Файл ~/.crm/logs/app.log

Уровень логирования задаётся в logger.py (по умолчанию INFO).

🐳 Запуск через Docker / Podman
Если Docker установлен, можно запустить бэкенд в контейнере:

bash
docker-compose up --build
(Файлы Dockerfile и docker-compose.yml должны быть в корне проекта – их можно создать по необходимости.)

⚠️ Возможные проблемы и решения
Проблема	Решение
ModuleNotFoundError: No module named 'config'	Убедитесь, что config.py находится в корне проекта и sys.path содержит корневую папку (см. run_gui.py).
Ошибка OAuth: File not found: 1	Проверьте GOOGLE_FOLDER_ID в .env – он должен быть правильным ID папки на Google Диске.
Ошибка авторизации Google (браузер не открывается)	Убедитесь, что OAuth-клиент настроен с redirect_uris: ["http://localhost"] и проект добавлен в тестовые пользователи.
PermissionError при удалении временного файла в тестах	Это нормально – тесты создают временный SQLite файл, который удаляется при завершении процесса.
GUI не отображает данные	Проверьте, что бэкенд запущен и порт 8000 доступен.
🛣️ Планы по развитию
Улучшение интерфейса (кастомные формы, валидация, фильтрация)

Расширение аналитики в отчётах (графики, диаграммы)

Добавление календаря для задач

Поддержка многопользовательского режима

Интеграция с Telegram / Email для уведомлений

Использование OpenAI для генерации описаний и рекомендаций

📜 Лицензия
Проект распространяется под лицензией MIT. Подробнее см. файл LICENSE.

🙏 Благодарности
FastAPI, SQLAlchemy, Tkinter – за отличные инструменты.

Google Cloud Platform – за мощные API.

Всем пользователям и контрибьюторам!

📬 Контакты
Если у вас есть вопросы или предложения, создавайте Issue в репозитории или пишите на почту: dmitrkomov@gmail.com.
Github: https://github.com/DmitriK10/Zerocode_Vibecoder

Спасибо, что используете Мини-CRM! 🚀