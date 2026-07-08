# Используем официальный образ Python 3.12-slim для минимального размера
FROM python:3.12-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения
COPY api.py .

# Открываем порт, на котором слушает приложение
EXPOSE 8080

# Команда запуска
CMD ["python", "api.py"]