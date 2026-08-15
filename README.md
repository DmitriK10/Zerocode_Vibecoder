# 🐍 Zerocode Vibecoder — Портфолио учебных проектов

Привет! Я **Дмитрий** — начинающий Python-разработчик, проходящий курс **«Профессия Вайбкодер»** (Zerocoder).  
Этот репозиторий — моё портфолио, где собраны проекты по веб-разработке, автоматизации, работе с базами данных, аналитике и созданию Telegram-ботов.
---

## 📌 Оглавление

| Проект | Краткое описание |
|--------|------------------|
| [DiscountCalculator](#-vpa06-discountcalculator) | Калькулятор скидок с сохранением истории (CLI + SQLite) |
| [TodoApp](#-vpb04-todoapp) | Веб-приложение для управления задачами на Flask |
| [task_bot](#-vpb06-task_bot) | Телеграм-бот для управления задачами |
| [pdf_generator](#-vpa05-pdf_generator) | Генерация PDF-отчётов из данных |
| [water_reminder](#-vpf03-water_reminder) | Телеграм-бот-напоминалка о воде |
| [fastapi-app](#-vpe03-fastapi-app) | REST API на FastAPI с документацией Swagger |
| [Loki+Grafana](#-vpe05-lokigrafana) | Настройка мониторинга и сбора логов |
| [lead_mvp](#-vpk011-lead_mvp) | MVP-система для управления лидами |

---

## 🛠️ Используемые технологии

<p align="left">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLAlchemy-FF6C37?style=for-the-badge&logo=sqlalchemy&logoColor=white" />
  <img src="https://img.shields.io/badge/Aiogram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white" />
  <img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" />
</p>

---

## 📂 Структура репозитория
Zerocode_Vibecoder/
├── VPa04/ # Начальные задания по Python
├── VPa05/pdf_generator/ # Генерация PDF-отчётов
├── VPa06/DiscountCalculator/ # Калькулятор скидок
├── VPb04/TodoApp/ # Веб-приложение на Flask
├── VPb06/task_bot/ # Телеграм-бот для задач
├── VPc01–VPc07/ # Работа с базами данных и SQL
├── VPd01–VPd06/ # Продвинутая работа с данными
├── VPe03/fastapi-app/ # REST API на FastAPI
├── VPe05/Loki+Grafana/ # Настройка мониторинга
├── VPf03/water_reminder/ # Бот-напоминалка о воде
├── VPk01.1/lead_mvp/ # MVP для лидов
└── README.md # Этот файл

text

---

## 🚀 Ключевые проекты (с подробностями)

### 💰 VPa06 — DiscountCalculator
**Консольное приложение** для расчёта скидок с сохранением истории в SQLite.  
Позволяет вводить сумму и процент скидки, вычислять итоговую цену и хранить все расчёты в базе данных.

- **Технологии:** Python, SQLite, ООП
- [📁 Перейти к проекту](VPa06/DiscountCalculator)
- [📸 Скриншот] (добавь позже)

---

### ✅ VPb04 — TodoApp
**Веб-приложение** для управления задачами с аутентификацией.  
Пользователи могут создавать, редактировать, удалять задачи и отмечать их выполненными.

- **Технологии:** Flask, SQLAlchemy, Jinja2, Bootstrap
- [📁 Перейти к проекту](VPb04/TodoApp)

---

### 🤖 VPb06 — task_bot
**Телеграм-бот** для создания и отслеживания задач.  
Умеет добавлять задачи, показывать список, отмечать выполненные и удалять.

- **Технологии:** Aiogram, SQLite
- [📁 Перейти к проекту](VPb06/task_bot)

---

### 📄 VPa05 — pdf_generator
**Генератор PDF-отчётов** из данных (например, из CSV или базы данных).  
Создаёт красивые структурированные отчёты с таблицами и графиками.

- **Технологии:** Python, ReportLab / FPDF
- [📁 Перейти к проекту](VPa05/pdf_generator)

---

### 💧 VPf03 — water_reminder
**Телеграм-бот**, который напоминает пить воду по расписанию.  
Настраивается интервал напоминаний, есть команды для старта/остановки.

- **Технологии:** python-telegram-bot
- [📁 Перейти к проекту](VPf03/water_reminder)

---

### ⚡ VPe03 — fastapi-app
**REST API** на FastAPI с автоматической документацией Swagger.  
Реализует CRUD для управления сущностями (например, пользователями или товарами).

- **Технологии:** FastAPI, Pydantic, Uvicorn
- [📁 Перейти к проекту](VPe03/fastapi-app)

---

### 📊 VPe05 — Loki+Grafana
**Настройка мониторинга** для приложений: сбор логов через Loki и визуализация в Grafana.  
Всё упаковано в Docker.

- **Технологии:** Loki, Grafana, Docker
- [📁 Перейти к проекту](VPe05/Loki+Grafana)

---

### 📋 VPk01.1 — lead_mvp
**MVP-система** для управления лидами (клиентскими заявками).  
Позволяет добавлять лиды, назначать ответственных, менять статусы.

- **Технологии:** Python, базы данных
- [📁 Перейти к проекту](VPk01.1/lead_mvp)

---

## 🧠 Чему я научился

За время обучения я освоил:

- 🔹 **Веб-разработку** на Flask и FastAPI
- 🔹 **Работу с базами данных** (SQLite, PostgreSQL, SQLAlchemy)
- 🔹 **Создание Telegram-ботов** (Aiogram, python-telegram-bot)
- 🔹 **Генерацию отчётов** (PDF, Excel)
- 🔹 **Контейнеризацию** (Docker)
- 🔹 **Мониторинг и логирование** (Loki, Grafana)
- 🔹 **Принципы ООП, чистый код, PEP8**
- 🔹 **Работу с Git** и командную разработку

---

## ⚙️ Как запустить проекты (общая инструкция)

1. **Клонируй репозиторий**:
   ```bash
   git clone https://github.com/DmitriK10/Zerocode_Vibecoder.git
   cd Zerocode_Vibecoder
Установи виртуальное окружение (рекомендуется):

bash
python -m venv venv
source venv/bin/activate      # для Linux/Mac
# или venv\Scripts\activate   # для Windows
Установи зависимости (если в проекте есть requirements.txt):

bash
pip install -r requirements.txt
Запусти нужный проект (перейди в его папку и следуй инструкциям в локальном README).

💡 Совет: Для каждого проекта внутри папки есть свой README с детальным запуском.

🌐 Демо и ссылки
Telegram-канал -

Действующий бот – 

Сайт-портфолио – https://dmitrik10.ru)

📬 Контакты
GitHub: DmitriK10

Telegram: @DmitriK10

Email: ymd@yandex.ru

📝 Лицензия
Этот репозиторий распространяется под лицензией MIT — подробности в файле LICENSE (если он есть).

⭐️ Если тебе понравились мои проекты, поставь звёздочку! Это мотивирует меня развиваться дальше.

📸 Скриншоты (будут добавлены позже)
Здесь будут скриншоты интерфейсов ключевых проектов.