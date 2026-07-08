# AI Client Report Generator

Telegram‑бот для автоматической генерации PDF‑отчётов по диалогам с клиентами с использованием LLM (через ProxyAPI), Jinja2 и WeasyPrint (или pdfkit на Windows).

## Переменные окружения (.env)

| Переменная | Описание | Пример |
|------------|----------|--------|
| `BOT_TOKEN` | Токен Telegram-бота | `123456:ABC...` |
| `TELEGRAM_API_BASE_URL` | Прокси для Telegram API (опционально) | `https://tg-proxy...` |
| `OPENAI_API_KEY` | Ключ API для OpenAI (ProxyAPI) | `sk-...` |
| `OPENAI_BASE_URL` | Базовый URL для OpenAI-совместимого API | `https://openai.api.proxyapi.ru/v1` |
| `OPENAI_MODEL` | Модель для генерации | `gpt-4o-mini` |
| `OPENAI_TEMPERATURE` | Температура (0.0–1.0). Влияет на креативность. Для точных данных – низкая (0.2–0.3), для творческих задач – выше (0.7–0.9). | `0.3` |

## Возможности

- **Три типа отчётов**:
  - Клиентский отчёт (основные данные, бюджет, сроки)
  - Отчёт по дизайну сайта (требования + пример изображения)
  - Карточка товара для маркетплейса (название, цена, описание, изображение)
- **Генерация изображений** через бесплатный сервис pollinations.ai (вставка в PDF)
- **Постоянная память** не требуется – работа идёт по запросу.
- **Удобный Telegram‑интерфейс** с машиной состояний (FSM).

## Установка и запуск

1. Клонируйте репозиторий.
2. Создайте виртуальное окружение и активируйте его.
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
4. Создайте файл .env с вашими токенами (см. .env.example).

5. Для Linux/macOS убедитесь, что установлены системные зависимости для WeasyPrint:

bash
sudo apt install libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
6. Для Windows рекомендуется использовать pdfkit вместо WeasyPrint (чтобы избежать сложной установки GTK+):

Установите pdfkit:

bash
pip install pdfkit
Скачайте и установите wkhtmltopdf с официального сайта (выберите стабильную версию для Windows).

В файле utils/pdf_generator.py замените импорт и вызов weasyprint на pdfkit (пример ниже).

Альтернативный код для pdf_generator.py (Windows):

python
import pdfkit
# вместо HTML(string=html_content).write_pdf(output_path)
options = {
    'enable-local-file-access': None,
    'margin-top': '10mm',
    'margin-bottom': '10mm',
    'margin-left': '10mm',
    'margin-right': '10mm',
}
pdfkit.from_string(html_content, output_path, options=options)
Не забудьте удалить weasyprint из requirements.txt и добавить pdfkit.

7. Запустите бота:

bash
python bot.py
8. Команды бота
/start – начать диалог, выбрать тип отчёта

/help – справка

/cancel – отменить текущее действие

9. Пример использования
/start → выбор типа отчёта.

Для клиентского/дизайн‑отчёта: отправьте текст диалога или файл .txt.

Для карточки товара: введите название и цену через запятую (можно несколько строк, до 10 товаров).

Бот сгенерирует PDF и отправит его вам.

Используемые технологии
Python 3.10+

aiogram – Telegram Bot API

OpenAI (ProxyAPI) – LLM

Jinja2 – HTML‑шаблоны

WeasyPrint / pdfkit – конвертация HTML → PDF

aiohttp – асинхронные запросы к pollinations.ai

python-dotenv – управление переменными окружения

### Дополнительные замечания

- **ProxyAPI** используется для доступа к OpenAI‑совместимому API (указан `OPENAI_BASE_URL`).
- **Telegram‑прокси** задан через `TELEGRAM_API_BASE_URL` – все запросы к Telegram API идут через него.
- Генерация изображений выполняется через `pollinations.ai`, что не требует API‑ключа и работает бесплатно.
- Все PDF сохраняются в папку `reports/` с временной меткой в имени.