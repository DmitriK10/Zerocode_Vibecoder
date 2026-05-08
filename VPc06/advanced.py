"""
advanced.py – Средний трек
Цель: создать таблицы, добавить данные, выполнить JOIN + SUM, вывести итоги.
"""

import os
import sys
import psycopg2
from psycopg2 import OperationalError, DatabaseError, Error
from dotenv import load_dotenv


def create_tables(cur):
    """Создаёт таблицы users и orders, если они не существуют."""
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id   SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            age  INT CHECK (age >= 0)
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id         SERIAL PRIMARY KEY,
            user_id    INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            amount     NUMERIC(10,2) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)


def insert_sample_data(cur):
    """Добавляет тестовых пользователей и заказы (если таблицы пусты)."""
    cur.execute("SELECT COUNT(*) FROM users;")
    count_users = cur.fetchone()[0]
    if count_users == 0:
        users_data = [
            ("Alice", 28),
            ("Bob", 34),
            ("Charlie", 25)
        ]
        for name, age in users_data:
            cur.execute(
                "INSERT INTO users (name, age) VALUES (%s, %s)",
                (name, age)
            )
        print("Добавлены 3 пользователя.")

    cur.execute("SELECT COUNT(*) FROM orders;")
    count_orders = cur.fetchone()[0]
    if count_orders == 0:
        cur.execute("SELECT id, name FROM users;")
        users = cur.fetchall()
        if len(users) >= 2:
            cur.execute(
                "INSERT INTO orders (user_id, amount) VALUES (%s, %s)",
                (users[0][0], 499.90)
            )
            cur.execute(
                "INSERT INTO orders (user_id, amount) VALUES (%s, %s)",
                (users[1][0], 1250.00)
            )
            cur.execute(
                "INSERT INTO orders (user_id, amount) VALUES (%s, %s)",
                (users[0][0], 300.00)
            )
            print("Добавлены тестовые заказы (2 пользователя, 3 заказа).")


def get_user_totals(cur):
    cur.execute("""
        SELECT u.name,
               COALESCE(SUM(o.amount), 0) AS total_amount
        FROM users u
        LEFT JOIN orders o ON o.user_id = u.id
        GROUP BY u.id, u.name
        ORDER BY total_amount DESC;
    """)
    return cur.fetchall()


def main():
    load_dotenv()

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
        print("Проверьте файл .env")
        sys.exit(1)

    conn = None
    try:
        conn = psycopg2.connect(**conn_params)
        print("Соединение установлено.")

        with conn:
            with conn.cursor() as cur:
                create_tables(cur)
                print("Таблицы созданы/проверены.")

                insert_sample_data(cur)
                print("Данные добавлены (если таблицы были пусты).")

                totals = get_user_totals(cur)
                print("\n--- Сумма заказов по каждому пользователю (сортировка по убыванию) ---")
                for name, total in totals:
                    print(f"{name}: {total:.2f}")

        print("\nТранзакция успешно завершена (commit).")

    except OperationalError as e:
        print(f"Ошибка подключения: {e}")
    except DatabaseError as e:
        print(f"Ошибка базы данных: {e}")
        if conn:
            conn.rollback()
            print("Выполнен откат транзакции.")
    except Error as e:
        print(f"Общая ошибка psycopg2: {e}")
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")
    finally:
        if conn:
            conn.close()
            print("Соединение закрыто.")


if __name__ == "__main__":
    main()