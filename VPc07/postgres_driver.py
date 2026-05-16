# postgres_driver.py
import inspect
from typing import Any, Dict, List, Optional
from datetime import datetime, date
import psycopg2
import psycopg2.extras
from database_driver import DatabaseDriver
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

class PostgresSQLDriver(DatabaseDriver):
    def __init__(self):
        self._connection = None
        self._cursor = None

    def connect(self) -> None:
        self._connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        self._connection.autocommit = True   # ← РЕШЕНИЕ ПРОБЛЕМЫ ТРАНЗАКЦИЙ
        self._cursor = self._connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def disconnect(self) -> None:
        if self._cursor:
            self._cursor.close()
        if self._connection:
            self._connection.close()

    def execute(self, query: str, params: Optional[tuple] = None) -> None:
        self._cursor.execute(query, params)
        # autocommit = True, но commit() не повредит
        self._connection.commit()

    def select(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        self._cursor.execute(query, params)
        return self._cursor.fetchall()

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"
        self._cursor.execute(query, tuple(data.values()))
        self._connection.commit()
        return self._cursor.fetchone()["id"]

    def update(self, table: str, data: Dict[str, Any], condition: str, params: tuple) -> None:
        set_clause = ", ".join([f"{col} = %s" for col in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        self._cursor.execute(query, tuple(data.values()) + params)
        self._connection.commit()

    def delete(self, table: str, condition: str, params: tuple) -> None:
        query = f"DELETE FROM {table} WHERE {condition}"
        self._cursor.execute(query, params)
        self._connection.commit()

    def create_table_from_model(self, model_class: type) -> bool:
        table_name = model_class.__name__.lower() + "s"
        if self._check_table_exists(table_name):
            return False

        columns_sql = []
        for name, py_type in model_class.__annotations__.items():
            if name == "id":
                # Исправление: автоинкремент для первичного ключа
                col_type = "SERIAL"
                constraints = " PRIMARY KEY"
            else:
                col_type = self._python_type_to_postgres(py_type)
                constraints = ""
            columns_sql.append(f"{name} {col_type}{constraints}")

        # Добавляем внешние ключи, если определены
        fk_clauses = []
        if hasattr(model_class, '__foreign_keys__'):
            for fk in model_class.__foreign_keys__:
                fk_clauses.append(
                    f"FOREIGN KEY ({fk['column']}) REFERENCES {fk['ref_table']}({fk['ref_column']})"
                )

        all_columns = ",\n    ".join(columns_sql + fk_clauses)
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n    {all_columns}\n);"
        self._cursor.execute(sql)
        self._connection.commit()
        return True

    def _check_table_exists(self, table_name: str) -> bool:
        self._cursor.execute(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = %s)",
            (table_name,)
        )
        return self._cursor.fetchone()["exists"]

    @staticmethod
    def _python_type_to_postgres(py_type) -> str:
        mapping = {
            int: "INTEGER",
            str: "VARCHAR(255)",
            float: "REAL",
            bool: "BOOLEAN",
            datetime: "TIMESTAMP",
            date: "DATE",
            type(None): "VARCHAR(255)"
        }
        origin = getattr(py_type, "__origin__", None)
        if origin is not None and hasattr(py_type, "__args__"):
            args = py_type.__args__
            if type(None) in args:
                non_none = [a for a in args if a is not type(None)]
                if non_none:
                    return mapping.get(non_none[0], "VARCHAR(255)")
        return mapping.get(py_type, "VARCHAR(255)")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()