"""Точка входа – создание и запуск Flask-приложения."""

from flask import Flask
from services import SimpleCalculator
from routes import register_routes


def create_app():
    """Фабрика приложения (принцип инверсии зависимостей)."""
    app = Flask(__name__)

    # Создаём зависимости
    calculator = SimpleCalculator()

    # Регистрируем маршруты, передавая зависимости
    register_routes(app, calculator)

    return app


# Создаём экземпляр приложения для Gunicorn
app = create_app()

if __name__ == '__main__':
    # Запуск встроенного сервера (только для отладки)
    app.run(host='0.0.0.0', port=5000)