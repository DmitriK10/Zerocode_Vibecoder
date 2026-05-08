"""
postgres_driver.py – драйвер для работы с PostgreSQL.
Предоставляет удобный интерфейс для внешних проектов.
"""

import os
import psycopg2
from psycopg2 import OperationalError, DatabaseError, Error
from dotenv import load_dotenv


class PostgresDriver:
    """
    Драйвер для подключения к PostgreSQL и выполнения операций.
    Использует переменные окружения из .env.
    """

    def __init__(self, env_file='.env'):
        load_dotenv(env_file)
        self._conn_params = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'dbname': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
        }
        self._validate_params()
        self._conn = None

    def _validate_params(self):
        missing = [k for k, v in self._conn_params.items() if not v]
        if missing:
            raise ValueError(f"Отсутствуют переменные окружения: {', '.join(missing)}")

    def _get_connection(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**self._conn_params)
        return self._conn

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()
            self._conn = None

    def execute_query(self, query, params=None, fetch=False):
        conn = self._get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                if fetch:
                    return cur.fetchall()
                return None

    def create_users_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS users (
            id   SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            age  INT CHECK (age >= 0)
        );
        """
        self.execute_query(sql)

    def create_orders_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS orders (
            id         SERIAL PRIMARY KEY,
            user_id    INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            amount     NUMERIC(10,2) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
        self.execute_query(sql)

    def add_user(self, name, age):
        sql = "INSERT INTO users (name, age) VALUES (%s, %s) RETURNING id;"
        result = self.execute_query(sql, (name, age), fetch=True)
        return result[0][0] if result else None

    def add_order(self, user_id, amount):
        sql = "INSERT INTO orders (user_id, amount) VALUES (%s, %s);"
        self.execute_query(sql, (user_id, amount))

    def get_user_totals(self):
        sql = """
        SELECT u.name,
               COALESCE(SUM(o.amount), 0) AS total_amount
        FROM users u
        LEFT JOIN orders o ON o.user_id = u.id
        GROUP BY u.id, u.name
        ORDER BY total_amount DESC;
        """
        return self.execute_query(sql, fetch=True)

    def get_all_users(self):
        sql = "SELECT id, name, age FROM users;"
        return self.execute_query(sql, fetch=True)

    def drop_tables(self, cascade=False):
        cascade_sql = " CASCADE" if cascade else ""
        self.execute_query(f"DROP TABLE IF EXISTS orders{cascade_sql};")
        self.execute_query(f"DROP TABLE IF EXISTS users{cascade_sql};")


if __name__ == "__main__":
    db = PostgresDriver()
    try:
        db.create_users_table()
        db.create_orders_table()
        if not db.get_all_users():
            alice_id = db.add_user("Alice", 28)
            bob_id = db.add_user("Bob", 34)
            db.add_user("Charlie", 25)
            db.add_order(alice_id, 499.90)
            db.add_order(bob_id, 1250.00)
            db.add_order(alice_id, 300.00)
        totals = db.get_user_totals()
        print("Суммы заказов:")
        for name, total in totals:
            print(f"  {name}: {total:.2f}")
    finally:
        db.close()