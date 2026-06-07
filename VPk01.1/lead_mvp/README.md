# Lead Intake MVP

Сервис для автоматического приёма заявок (лидов) через веб-перехватчик (webhook).  
Заявка → валидация → сохранение в SQLite → уведомление в лог-файл.

**Вариант уведомления:** Вариант A запись в `events.log` (простой и надёжный).

---

## 🚀 Быстрый старт за 5 минут

### Требования
- Python 3.10 или выше
- Установленный `pip`
- (Опционально) `sqlite3` для просмотра БД из командной строки

### Установка и запуск

1. **Склонируйте репозиторий** (или создайте файлы вручную по структуре ниже):
   ```bash
   git clone <url> lead_mvp
   cd lead_mvp
Создайте виртуальное окружение (рекомендуется):

bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
Установите зависимости:

bash
pip install -r requirements.txt
При ошибках SSL (корпоративный антивирус) используйте:
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

Запустите сервер:

bash
uvicorn app.main:app --reload
Вы увидите:

text
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
📨 Пример запроса
PowerShell (Windows):

powershell
$body = @{
    name    = "Ирина"
    contact = "+79990000000"
    source  = "landing"
    comment = "Хочу консультацию"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://127.0.0.1:8000/lead" `
                  -Method POST `
                  -Body $body `
                  -ContentType "application/json"
Linux/macOS / curl.exe (Windows):

bash
curl -X POST "http://127.0.0.1:8000/lead" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ирина",
    "contact": "+79990000000",
    "source": "landing",
    "comment": "Хочу консультацию по тарифам"
  }'
Успешный ответ (201 Created):

json
{
  "id": 1,
  "message": "Lead saved successfully"
}
🗄️ Где смотреть результаты?
1. База данных SQLite
Файл leads.db создаётся автоматически в корне проекта.
Просмотр через командную строку:

bash
sqlite3 leads.db "SELECT * FROM leads;"
Если sqlite3 не установлен, используйте Python:

bash
python -c "import sqlite3; conn = sqlite3.connect('leads.db'); cur = conn.cursor(); cur.execute('SELECT * FROM leads'); print(cur.fetchall())"
Пример вывода:

text
[(1, '2026-06-05T21:33:26.215903', 'Ирина', '+79990000000', 'landing', 'Хочу консультацию')]
2. Лог-уведомления
Файл events.log в корне проекта.
Просмотр:

bash
cat events.log          # Linux/macOS
Get-Content events.log  # PowerShell
Пример строки:

text
[2026-06-05T21:33:26.227896] New lead saved: id=1, contact=+79990000000
❗ Обработка ошибок
Ситуация	HTTP статус	Пример ответа
Отсутствует обязательное поле contact	400	{"detail":"Невалидный запрос. Проверьте поля name, contact (обязательно), source, comment."}
Невалидный JSON	400	(аналогичное сообщение)
База данных недоступна (ошибка записи)	500	{"detail":"Не удалось сохранить заявку в БД: ..."}
Ошибка записи в лог-файл	500	{"detail":"Не удалось записать уведомление: ..."}
📂 Структура проекта (SOLID)
text
lead_mvp/
├── app/
│   ├── __init__.py          # признак пакета
│   ├── main.py              # FastAPI приложение, endpoint /lead
│   ├── config.py            # пути к БД и логу
│   ├── models.py            # Pydantic-схемы валидации
│   ├── database.py          # репозиторий SQLite
│   ├── notifier.py          # уведомление через лог-файл
│   ├── service.py           # бизнес-логика
│   └── exceptions.py        # кастомные исключения
├── leads.db                 # создаётся автоматически
├── events.log               # создаётся при первом уведомлении
├── requirements.txt
├── test_payloads.json       # 10 тестовых кейсов
├── examples.md              # документация тестов
└── README.md
🛠 Возможные проблемы и решения
Ошибка SSL при установке пакетов – используйте --trusted-host (см. выше).

Порт 8000 уже занят – запустите на другом порту: uvicorn app.main:app --reload --port 8001.

Модули не найдены – убедитесь, что вы активировали виртуальное окружение и установили зависимости.

Нет прав на запись в файл leads.db или events.log – проверьте, что папка проекта доступна для записи.

📈 Планы на v2 (улучшения)
Дедупликация заявок (по contact + временное окно)

Отправка уведомлений на email / Telegram

Асинхронная работа с БД (aiosqlite)

Веб-интерфейс для просмотра заявок

Деплой на VPS в Docker-контейнере

📄 Лицензия
MIT (свободное использование).