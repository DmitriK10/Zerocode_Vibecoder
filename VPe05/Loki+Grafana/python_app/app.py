from flask import Flask, jsonify, render_template, request
import datetime
import platform
import os
import random
import socket
from loki_logger import LokiLogger

app = Flask(__name__)

# Логгер Loki (UI-логи будут с job="ui")
loki = LokiLogger(loki_url="http://localhost:3100", default_job="ui")

# --- UI Маршруты ---

@app.route('/')
def index():
    """Главная страница UI"""
    return render_template('index.html',
                           system_info=None,
                           main_info=None,
                           math_result=None)

@app.route('/system')
def system_info():
    """Получить информацию о системе"""
    info = {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "processor": platform.processor(),
        "architecture": platform.architecture(),
        "user": os.getenv("USER", "unknown"),
        "working_directory": os.getcwd()
    }
    loki.send("Запрошена информация о системе", level="INFO", job="ui")
    return render_template('index.html',
                           system_info=info,
                           main_info=None,
                           math_result=None)

@app.route('/main')
def main_info():
    """Получить главную информацию"""
    info = {
        "message": "Приложение успешно запущено в Docker контейнере!",
        "timestamp": datetime.datetime.now().isoformat(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "container_id": os.environ.get("HOSTNAME", "unknown"),
        "environment": dict(os.environ)
    }
    loki.send("Запрошена главная информация", level="INFO", job="ui")
    return render_template('index.html',
                           system_info=None,
                           main_info=info,
                           math_result=None)

@app.route('/math')
def math_operation():
    """Выполнить математическую операцию"""
    a = request.args.get('a', type=float)
    b = request.args.get('b', type=float)
    op = request.args.get('op', 'multiply')

    if a is None or b is None:
        result = "Ошибка: введите оба числа"
    elif op == 'multiply':
        result = f"{a} × {b} = {a * b}"
        loki.send(f"Умножение: {a} × {b} = {a * b}", level="INFO", job="ui")
    elif op == 'divide':
        if b == 0:
            result = "Ошибка: деление на ноль"
            loki.send(f"Попытка деления на ноль: {a} ÷ {b}", level="ERROR", job="ui")
        else:
            result = f"{a} ÷ {b} = {a / b}"
            loki.send(f"Деление: {a} ÷ {b} = {a / b}", level="INFO", job="ui")
    else:
        result = "Неизвестная операция"

    return render_template('index.html',
                           system_info=None,
                           main_info=None,
                           math_result=result)

# --- Старые API-эндпоинты (для обратной совместимости) ---

@app.route('/success')
def success():
    loki.send("Запрос /success выполнен успешно", level="INFO", job="web")
    return jsonify({"status": "success", "data": {"random": random.randint(1, 100)}})

@app.route('/error')
def simulate_error():
    error_msg = "Внутренняя ошибка сервера: не удалось обработать запрос"
    loki.send(error_msg, level="ERROR", job="web")
    return jsonify({"error": error_msg}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
