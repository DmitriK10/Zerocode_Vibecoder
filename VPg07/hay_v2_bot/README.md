# 🤖 Персональный ассистент v2 (Haystack + Docling + Pinecone)

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![Haystack 3.0](https://img.shields.io/badge/Haystack-3.0-green.svg)
![Pinecone](https://img.shields.io/badge/Pinecone-vector%20DB-orange.svg)
![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

---

Умный Telegram-бот с долговременной памятью, поддержкой документов и RAG-ответами на базе **Haystack**, **Docling** и **Pinecone**.

---

## 📌 Оглавление

- [Возможности](#-возможности)
- [Технологии](#-технологии)
- [Структура проекта](#-структура-проекта)
- [Требования](#-требования)
- [Установка и настройка](#-установка-и-настройка)
- [Запуск бота](#-запуск-бота)
- [Использование](#-использование)
- [Тестирование](#-тестирование)
- [Частые проблемы](#-частые-проблемы)
- [Лицензия](#-лицензия)

---

## 🚀 Возможности

- ✅ **Обработка документов** – загружайте PDF (и другие форматы через Docling), бот извлекает текст, разбивает на чанки, генерирует эмбеддинги и сохраняет в Pinecone.
- ✅ **Долговременная память** – история диалога хранится в векторной базе, бот «помнит» прошлые сообщения даже после перезапуска.
- ✅ **RAG-ответы** – на вопросы отвечает, используя контекст из загруженных документов и истории беседы.
- ✅ **Генерация резюме** – после загрузки документа бот автоматически создаёт краткое резюме (одно предложение).
- ✅ **Интерактивные инструменты**:
  - 🐱 Случайный факт о кошках (`catfact.ninja`)
  - 🐶 Случайное фото собаки с описанием породы (через OpenAI Vision)
  - 🌦️ Текущая погода в любом городе (OpenWeatherMap)
- ✅ **Команды**:
  - `/start` – приветствие и список возможностей
  - `/help` – то же, что и `/start`
  - `/clear` – очистить историю диалога

---

## 🛠 Технологии

| Компонент | Используется для |
|-----------|------------------|
| **Python 3.11+** | Язык программирования |
| **Haystack 3.0** | Фреймворк для RAG-приложений (пайплайны, компоненты) |
| **Docling** | Конвертация PDF и других документов в текст |
| **OpenAI API** | Генерация эмбеддингов (`text-embedding-3-small`) и ответов (`gpt-3.5-turbo-16k`) |
| **Pinecone** | Векторная база данных для хранения эмбеддингов |
| **Telegram Bot API** | Интерфейс для пользователей |
| **OpenWeatherMap API** | Получение погоды |
| **PyTelegramBotAPI** | Библиотека для Telegram-ботов |
| **unittest / pytest** | Тестирование |

---

## 📂 Структура проекта
hay_v2_bot/
├── bot/
│ └── telegram_bot.py # Основная логика бота (обработчики сообщений)
├── components/
│ ├── cat_fact.py # Факты о кошках
│ ├── dog_image.py # Получение фото собаки
│ ├── dog_image_analyzer.py # Анализ породы через OpenAI Vision
│ ├── weather.py # Погода
│ ├── docling_converter.py # Конвертер документов (Docling)
│ ├── embedder.py # Единый эмбеддер (OpenAI)
│ ├── message_context.py # Управление историей диалога
│ └── pinecone_helpers.py # Работа с Pinecone (upsert, query, очистка метаданных)
├── pipelines/
│ └── generation.py # Генерация ответов через OpenAI (RAG)
├── tests/
│ ├── test_generation.py
│ ├── test_message_context.py
│ ├── test_pinecone_helpers.py
│ └── test_telegram_bot.py
├── temp_files/ # Временные файлы (создаётся автоматически)
├── config.py # Загрузка переменных окружения + валидация
├── main.py # Точка входа (запуск бота)
├── run_tests.py # Скрипт запуска тестов
├── requirements.txt # Зависимости
├── .env.example # Шаблон для .env
└── README.md # Этот файл

text

---

## 📋 Требования

Перед установкой убедитесь, что у вас есть:

- **Python 3.11 или выше** (рекомендуется 3.11+)
- **Аккаунты и API-ключи**:
  - OpenAI API (или прокси-сервер, например, `proxyapi.ru`)
  - Pinecone (создайте индекс размерностью **1536**)
  - Telegram Bot (получите токен через [@BotFather](https://t.me/BotFather))
  - OpenWeatherMap (получите API-ключ)

---

## ⚙️ Установка и настройка

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo/hay_v2_bot
2. Создайте и активируйте виртуальное окружение
bash
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
.venv\Scripts\activate         # Windows
3. Установите зависимости
bash
pip install -r requirements.txt
4. Настройте переменные окружения
Скопируйте .env.example в .env и заполните своими ключами:

bash
cp .env.example .env
Пример содержимого .env:

env
# OpenAI / Proxy
OPENAI_API_KEY=sk-ваш-ключ
OPENAI_BASE_URL=https://api.proxyapi.ru/openai/v1   # или https://api.proxypi.ru/v1
OPENAI_MODEL=gpt-3.5-turbo-16k
EMBEDDING_MODEL=text-embedding-3-small

# Pinecone
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX_NAME=zerovpg07
PINECONE_HOST=https://zerovpg07-ykilia5.svc.aped-4627-b74a.pinecone.io

# Telegram
TELEGRAM_TOKEN=ваш-токен-бота

# Weather
WEATHER_API_KEY=ваш-ключ-openweather
Важно: Убедитесь, что ваш индекс Pinecone имеет размерность 1536 (для модели text-embedding-3-small).

▶️ Запуск бота
bash
python main.py
После запуска в консоли появится сообщение Бот запущен. Откройте Telegram, найдите своего бота и отправьте /start.

📖 Использование
Команды
Команда	Действие
/start или /help	Показать список возможностей
/clear	Очистить историю диалога (удаляются сообщения пользователя из Pinecone)
Примеры текстовых запросов
Запрос	Что делает бот
Расскажи факт о кошках	Возвращает случайный факт
Покажи собаку	Отправляет фото и описание породы
Какая погода в Москве?	Сообщает текущую температуру и описание
О чём этот документ?	Отвечает на основе загруженного документа
Что я говорил ранее о погоде?	Ищет в истории диалога и отвечает
Загрузка документов
Отправьте боту PDF-файл (размер до 20 МБ).

Бот начнёт обработку: конвертация → сплиттинг → эмбеддинги → сохранение в Pinecone.

По завершению вы получите краткое резюме документа.

Теперь можно задавать вопросы по содержанию документа.

🧪 Тестирование
В проекте реализованы 11 юнит-тестов для критических функций. Запустите их через скрипт:

bash
python run_tests.py
Для запуска конкретного тестового файла:

bash
python run_tests.py -t tests.test_pinecone_helpers
Для подробного вывода:

bash
python run_tests.py -v
Примечание: Тесты используют моки, поэтому не требуют реальных API-ключей.

🐛 Частые проблемы и их решение
Проблема	Решение
ModuleNotFoundError: No module named 'haystack_integrations'	Установите pip install pinecone-haystack
Permission denied при обработке файла	Временные файлы сохраняются в temp_files/ – проверьте права доступа к папке
std::bad_alloc при конвертации PDF	Слишком сложный PDF (много изображений, таблиц). Отключите OCR в docling_converter.py (уже сделано) или конвертируйте в DOCX
InvalidCxxCompiler: Compiler: cl is not found	Установите Visual Studio Build Tools
APIConnectionError при обращении к OpenAI	Проверьте интернет и OPENAI_BASE_URL в .env
Pinecone не отвечает	Проверьте PINECONE_API_KEY, PINECONE_INDEX_NAME, PINECONE_HOST
📄 Лицензия
Проект распространяется под лицензией MIT. Вы можете свободно использовать, модифицировать и распространять код.