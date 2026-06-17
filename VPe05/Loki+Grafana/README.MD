Проект: Мониторинг логов с Loki + Grafana
Данный проект демонстрирует развертывание стека Loki + Grafana с отправкой логов напрямую через HTTP API (без Promtail). Включает два примера приложений:

main.py – эмулятор криптовалютного бэкенда, генерирующий случайные логи.

app.py – простое Flask-приложение с тремя эндпоинтами, логирующее каждый запрос.

Все логи визуализируются в Grafana на дашборде с таблицей последних событий и круговой диаграммой по уровням.

📁 Структура проекта
text
.
├── docker-compose.yml                # Основной compose-файл для Loki и Grafana
├── loki-config.yml                   # Конфигурация Loki (хранилище, порты)
├── grafana/
│   └── provisioning/
│       └── datasources/
│           └── datasources.json      # Автоматическое добавление Data Source Loki
├── python_app/
│   ├── loki_logger.py                # Класс LokiLogger – отправка логов через HTTP POST
│   ├── main.py                       # Эмулятор криптовалютного бэкенда
│   └── app.py                        # Flask-приложение с логированием
└── README.md                         # Этот файл
🚀 Запуск проекта
1. Установка Docker и Docker Compose (Ubuntu)
bash
apt update && apt upgrade -y
apt install -y ca-certificates curl gnupg lsb-release
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
Проверьте установку:

bash
docker --version
docker compose version
2. Клонирование или создание файлов проекта
Создайте папку Loki+Grafana и поместите туда все файлы из структуры выше.
Убедитесь, что имена файлов совпадают:

docker-compose.yml (не docker-compose.yaml)

loki-config.yml

grafana/provisioning/datasources/datasources.json

3. Запуск Loki и Grafana
bash
cd /root/Loki+Grafana   # или путь к вашей папке
docker compose up -d
Проверьте статус контейнеров:

bash
docker compose ps
Оба контейнера (loki и grafana) должны быть в состоянии Up.

Если контейнер loki перезапускается с ошибкой permission denied, выполните:

bash
mkdir -p loki
chmod 777 loki
docker compose restart loki
4. Настройка Grafana
Откройте в браузере http://<IP-сервера>:3000
Логин: admin, пароль: admin (при первом входе можно пропустить смену пароля).

Перейдите в Configuration → Data Sources – источник Loki должен уже быть добавлен автоматически (благодаря datasources.json).
Проверьте URL: должно быть http://loki:3100.
Нажмите Save & test – должно появиться зелёное сообщение (или no labels – нормально, пока нет данных).

Если источник не появился, добавьте его вручную с теми же параметрами.

5. Установка Python-зависимостей (виртуальное окружение)
Перейдите в папку python_app и создайте виртуальное окружение:

bash
cd /root/Loki+Grafana/python_app
python3 -m venv venv
source venv/bin/activate
pip install flask requests
Теперь все скрипты будут запускаться внутри этого окружения.

6. Запуск эмулятора main.py
В первом терминале (или в фоне) запустите:

bash
cd /root/Loki+Grafana/python_app
source venv/bin/activate
python main.py
Он начнёт отправлять логи в Loki каждые 2 секунды.

7. Запуск Flask-приложения app.py
Во втором терминале (или в фоне) запустите:

bash
cd /root/Loki+Grafana/python_app
source venv/bin/activate
python app.py
Если порт 5000 занят, измените порт в файле app.py (последняя строка) на port=5001 или используйте команду:

bash
sed -i 's/port=5000/port=5001/' app.py
Затем перезапустите Flask.

📊 Создание дашборда в Grafana
1. Таблица последних логов
Перейдите в Dashboards → New → New Dashboard → Add visualization.

Выберите источник Loki.

В запросе введите (в режиме Builder или Code):

logql
{app="crypto-app"}
(или {app=~"crypto-backend|web"} для объединения с Flask).

Нажмите Run queries.

Справа выберите тип визуализации Table.

Задайте название, нажмите Apply.

2. Круговая диаграмма по уровням
На дашборде Add → Visualization.

Выберите источник Loki.

Переключитесь в режим Code и введите:

logql
sum by (level) (count_over_time({app="crypto-app"}[$__interval]))
Нажмите Run queries.

Справа выберите Pie chart.

Задайте название, нажмите Apply.

3. Настройка автообновления
В правом верхнем углу дашборда выберите временной диапазон (например, Last 5 minutes).

Нажмите на значок часов со стрелкой и выберите интервал обновления (например, 5s или 10s).

Сохраните дашборд (иконка дискеты) – дайте имя, например Crypto Monitoring.

🔍 Проверка логов из Flask
Отправьте HTTP-запросы к Flask:

bash
curl http://localhost:5001/
curl http://localhost:5001/success
curl http://localhost:5001/error
(Если порт 5001, иначе 5000).

В Grafana:

Перейдите в Explore.

Введите запрос {app="web"} (или {app="flask-app"} – смотрите метку в app.py).

Нажмите Run query – вы увидите записи от Flask.

Чтобы объединить оба источника на одном дашборде, используйте регулярное выражение в запросе:

logql
{app=~"crypto-app|web"}
🧩 Принципы SOLID в коде
Single Responsibility – LokiLogger отвечает только за отправку логов; main.py и app.py занимаются бизнес-логикой.

Dependency Inversion – приложения зависят от абстракции (LokiLogger), а не от конкретного HTTP-клиента, что позволяет легко заменить реализацию (например, на запись в файл или другой агрегатор).

⚠️ Возможные проблемы и их решение
Проблема	Решение
Loki не запускается (permission denied)	Создайте папку loki и выдайте права: chmod 777 loki
Порт 5000 занят	Используйте порт 5001: замените в app.py port=5000 на port=5001
Логи Flask не отображаются	Проверьте URL в app.py: для хоста используйте http://localhost:3100, для контейнера – http://loki:3100. Перезапустите Flask.
Grafana не видит метки (no labels)	Отправьте хотя бы один лог – после этого метки появятся.
Модуль flask не найден	Активируйте виртуальное окружение (source venv/bin/activate) и установите pip install flask
Контейнер Grafana не стартует	Проверьте, что порт 3000 не занят другим процессом
📦 Формат сдачи
Вы можете предоставить:

Ссылку на GitHub-репозиторий с полным кодом.

Архив .zip со всеми файлами (включая README).

Скриншоты:

Работающего дашборда (таблица + круговая диаграмма).
Подключенного Data Source Loki (зелёный статус).
Логов из Flask в Explore.
📚 Дополнительные материалы
Официальная документация Grafana Loki

LogQL – язык запросов

HTTP API Loki