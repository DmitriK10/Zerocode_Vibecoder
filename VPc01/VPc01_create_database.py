"""
Модуль для создания базы данных SQLite и таблицы students.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any
from abc import ABC, abstractmethod


# ----------------------------------------------------------------------
# Абстрактный интерфейс для работы с БД (Dependency Inversion)
class DatabaseConnection(ABC):
    """Абстракция соединения с БД"""
    @abstractmethod
    def connect(self) -> sqlite3.Connection:
        pass

    @abstractmethod
    def close(self) -> None:
        pass


# ----------------------------------------------------------------------
# Конкретная реализация для SQLite (Single Responsibility)
class SQLiteConnection(DatabaseConnection):
    """Управляет подключением к SQLite"""
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._connection: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row  # удобный доступ по именам колонок
        return self._connection

    def close(self) -> None:
        if self._connection:
            self._connection.close()
            self._connection = None


# ----------------------------------------------------------------------
# Класс для выполнения SQL-операций (Single Responsibility)
class QueryExecutor:
    """Выполняет SQL-запросы, используя переданное соединение"""
    def __init__(self, connection: DatabaseConnection):
        self._conn_wrapper = connection

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        conn = self._conn_wrapper.connect()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor

    def fetch_all(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        cursor = self.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# ----------------------------------------------------------------------
# Класс для создания таблиц (Open/Closed – можно расширить методами alter)
class TableCreator:
    """Отвечает за создание таблиц в БД"""
    def __init__(self, executor: QueryExecutor):
        self.executor = executor

    def create_students_table(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS students (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT    NOT NULL,
            last_name  TEXT    NOT NULL,
            age        REAL    NOT NULL,
            is_active  INTEGER NOT NULL   -- SQLite нет BOOLEAN, используем 0/1
        );
        """
        self.executor.execute(sql)
        print("Таблица 'students' создана (или уже существует).")


# ----------------------------------------------------------------------
# Класс для вставки данных (Single Responsibility)
class DataInserter:
    def __init__(self, executor: QueryExecutor):
        self.executor = executor

    def insert_student(self, first_name: str, last_name: str, age: float, is_active: bool) -> int:
        sql = """
        INSERT INTO students (first_name, last_name, age, is_active)
        VALUES (?, ?, ?, ?);
        """
        cursor = self.executor.execute(sql, (first_name, last_name, age, int(is_active)))
        return cursor.lastrowid


# ----------------------------------------------------------------------
# Класс для выборки данных (Single Responsibility)
class DataSelector:
    def __init__(self, executor: QueryExecutor):
        self.executor = executor

    def get_all_students(self) -> List[Dict[str, Any]]:
        sql = "SELECT id, first_name, last_name, age, is_active FROM students;"
        return self.executor.fetch_all(sql)


# ----------------------------------------------------------------------
# Главная функция – оркестрация (не нарушает SOLID, т.к. это точка входа)
def main():
    # Абсолютный путь к базе данных (укажите свой реальный путь!)
    DB_PATH = Path("C:/Users/ADATA/Documents/Zerocode_Vibecoder/VPc01/homework.db")  # <<< ЗАМЕНИТЕ НА ВАШ ПУТЬ
    # Либо используйте путь относительно скрипта:
    # DB_PATH = Path(__file__).parent / "homework.db"

    # Убедимся, что директория существует
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Создаём компоненты (Dependency Injection)
    sqlite_conn = SQLiteConnection(DB_PATH)
    executor = QueryExecutor(sqlite_conn)
    table_creator = TableCreator(executor)
    inserter = DataInserter(executor)
    selector = DataSelector(executor)

    # 1. Создаём таблицу
    table_creator.create_students_table()

    # 2. Вставляем минимум 3 студентов
    students_data = [
        ("Иван", "Петров", 19.5, True),
        ("Мария", "Иванова", 20.0, True),
        ("Алексей", "Сидоров", 18.0, False),
        ("Елена", "Козлова", 22.3, True),   # четвёртый для примера
    ]

    print("\nДобавление студентов:")
    for first, last, age, active in students_data:
        new_id = inserter.insert_student(first, last, age, active)
        print(f"  Добавлен студент: {first} {last}, id={new_id}")

    # 3. Выводим всех студентов для проверки
    print("\nСписок всех студентов из базы данных:")
    students = selector.get_all_students()
    for s in students:
        active_str = "активен" if s["is_active"] else "не активен"
        print(f"  id={s['id']}: {s['first_name']} {s['last_name']}, "
              f"возраст={s['age']}, {active_str}")

    # Закрываем соединение
    sqlite_conn.close()
    print(f"\nБаза данных сохранена по пути: {DB_PATH.absolute()}")


if __name__ == "__main__":
    main()