"""
api.py
Исправленное Flask-приложение с безопасной работой с SQLite,
потокобезопасным доступом к общим данным и корректной обработкой ошибок.
"""
import sqlite3
import threading
import time
from contextlib import contextmanager

from flask import Flask, request, jsonify, g

app = Flask(__name__)
DATABASE = 'test.db'

# Потокобезопасное хранилище активных пользователей
_active_users = []
_active_lock = threading.Lock()


# ---------- Слой работы с базой данных ----------
def get_db():
    """Возвращает соединение с БД для текущего контекста запроса."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    """Закрывает соединение с БД после завершения запроса."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    """Создаёт таблицу users, если она не существует."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS users ('
            'id INTEGER PRIMARY KEY AUTOINCREMENT, '
            'name TEXT NOT NULL)'
        )
        db.commit()


# @app.before_first_request устарел, используем with app.app_context() при инициализации
# Выполним инициализацию при старте через обработчик
with app.app_context():
    init_db()


# ---------- Эндпоинты ----------
@app.route('/adduser', methods=['POST'])
def add_user():
    """
    Добавляет нового пользователя.
    Ожидает JSON: {"name": "..."}
    Возвращает 201 с данными созданного пользователя.
    """
    data = request.get_json()
    if not data or 'name' not in data or not isinstance(data['name'], str) or not data['name'].strip():
        return jsonify({'error': 'Invalid name'}), 400

    name = data['name'].strip()
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO users (name) VALUES (?)', (name,))
    db.commit()
    user_id = cursor.lastrowid
    return jsonify({'status': 'ok', 'id': user_id, 'name': name}), 201


@app.route('/user/<int:uid>', methods=['GET'])
def get_user(uid):
    """
    Возвращает данные пользователя по его id.
    При успехе – 200, при отсутствии – 404.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, name FROM users WHERE id = ?', (uid,))
    row = cursor.fetchone()
    if row is None:
        return jsonify({'error': 'not_found'}), 404
    return jsonify({'id': row[0], 'name': row[1]}), 200


@app.route('/activate/<int:uid>', methods=['GET', 'POST'])
def activate_user(uid):
    """
    Добавляет пользователя в список активных (потокобезопасно).
    Возвращает текущий список активных.
    """
    with _active_lock:
        if uid not in _active_users:
            _active_users.append(uid)
        # Имитация небольшой задержки (не блокирует)
        time.sleep(0.05)
        return jsonify({'status': 'ok', 'active': list(_active_users)}), 200


def _slow_task():
    """Тяжёлая задача, выполняется в отдельном потоке."""
    time.sleep(10)
    print("Slow task completed")


@app.route('/slow', methods=['GET'])
def slow_endpoint():
    """
    Запускает тяжёлую задачу в фоновом потоке и немедленно возвращает 202.
    """
    thread = threading.Thread(target=_slow_task)
    thread.start()
    return jsonify({'status': 'scheduled'}), 202


@app.route('/wrong', methods=['GET'])
def wrong_example():
    """
    Демонстрирует корректную обработку исключения деления на ноль.
    """
    try:
        x = 1 / 0  # noqa: F841
    except ZeroDivisionError as e:
        return jsonify({'msg': 'error', 'detail': str(e)}), 500
    return jsonify({'msg': 'ok'}), 200


# ---------- Запуск ----------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)