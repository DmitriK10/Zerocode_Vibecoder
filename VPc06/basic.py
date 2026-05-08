from pathlib import Path

env_file = Path(__file__).parent / '.env'
print("Путь к .env:", env_file.absolute())
print("Файл существует:", env_file.exists())
if env_file.exists():
    with open(env_file, 'rb') as f:
        raw = f.read()
        print("Сырое содержимое (hex первые 20 байт):", raw[:20].hex())
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
        print("Текстовое содержимое:")
        print(repr(content))

"""
basic.py – Базовый трек
Цель: подключиться к PostgreSQL, выполнить SELECT * FROM users, вывести строки.
"""

import os
import sys
import psycopg2
from psycopg2 import OperationalError, DatabaseError
from dotenv import load_dotenv


def main():
    # 1. Загружаем переменные из .env
    load_dotenv()
    print("Содержимое .env через dotenv:")
    print("DB_HOST:", os.getenv('DB_HOST'))
    print("DB_PORT:", os.getenv('DB_PORT'))
    print("DB_NAME:", os.getenv('DB_NAME'))
    print("DB_USER:", os.getenv('DB_USER'))
    print("DB_PASSWORD:", os.getenv('DB_PASSWORD'))

    # 2. Получаем параметры подключения
    conn_params = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
    }

    missing = [k for k, v in conn_params.items() if not v]
    if missing:
        print(f"Ошибка: отсутствуют переменные окружения: {', '.join(missing)}")
        print("Проверьте файл .env (скопируйте .env.example и заполните)")
        sys.exit(1)

    conn = None
    try:
        conn = psycopg2.connect(**conn_params)
        print("Соединение с PostgreSQL установлено.")

        with conn, conn.cursor() as cur:
            cur.execute("SELECT id, name, age FROM users;")
            rows = cur.fetchall()

            if not rows:
                print("Таблица 'users' пуста или не существует.")
            else:
                print("\nСписок пользователей:")
                for row in rows:
                    print(f"id={row[0]}, name='{row[1]}', age={row[2]}")

    except OperationalError as e:
        print(f"Ошибка подключения к БД: {e}")
        print("Убедитесь, что сервер PostgreSQL запущен, а параметры в .env верны.")
    except DatabaseError as e:
        print(f"Ошибка выполнения запроса: {e}")
        print("Возможно, таблица 'users' не создана в схеме public.")
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")
    finally:
        if conn is not None:
            conn.close()
            print("\nСоединение закрыто.")


if __name__ == "__main__":
    main()