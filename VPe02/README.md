# Flask приложение в Docker

## Эндпоинты

- `GET /` – информация о приложении
- `GET /health` – проверка здоровья
- `GET /info` – версия и принципы SOLID
- `GET /calc/<operation>/<a>/<b>` – вычисления (operation: add, subtract, multiply, divide).  
  Пример: `/calc/add/10/5` → `{"result":15.0}`

## Требования

- Установленный [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- (Опционально) Доступ к зеркалам Docker Hub и PyPI для сборки

## Сборка и запуск

1. **Откройте терминал** в папке проекта (где лежат `Dockerfile`, `app.py`, `requirements.txt` и т.д.)

2. **Соберите Docker-образ** (используя зеркало для стабильной загрузки):
   ```bash
   docker build --build-arg PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ -t solid-flask-app --add-host registry-1.docker.io:193.112.232.125 .
3. Запустите контейнер:

bash
docker run -d -p 5000:5000 --name my_solid_app solid-flask-app
4. Проверьте работу – откройте браузер и перейдите по адресу:

text
http://localhost:5000/calc/add/10/5
