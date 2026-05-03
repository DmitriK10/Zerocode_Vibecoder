"""
Скрипт автоматической сборки БД спортивного клуба.
Соблюдает принципы SOLID: каждый класс отвечает за одну задачу.
"""
import sqlite3
import os
from pathlib import Path

# Абстрактный базовый класс для выполнения SQL (OCP)
class SqlExecutor:
    def execute_script(self, connection: sqlite3.Connection, script: str):
        connection.executescript(script)

# Конкретные исполнители (SRP)
class SchemaCreator(SqlExecutor):
    def __init__(self, schema_path: str):
        self.schema_path = schema_path

    def run(self, connection: sqlite3.Connection):
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            script = f.read()
        self.execute_script(connection, script)
        print(f"Схема из {self.schema_path} применена.")

class DataSeeder(SqlExecutor):
    def __init__(self, seed_path: str):
        self.seed_path = seed_path

    def run(self, connection: sqlite3.Connection):
        with open(self.seed_path, 'r', encoding='utf-8') as f:
            script = f.read()
        self.execute_script(connection, script)
        print(f"Данные из {self.seed_path} загружены.")

class CheckQueries(SqlExecutor):
    def __init__(self, checks_path: str):
        self.checks_path = checks_path

    def run(self, connection: sqlite3.Connection):
        with open(self.checks_path, 'r', encoding='utf-8') as f:
            queries = f.read().split(';')
        cursor = connection.cursor()
        for i, query in enumerate(queries, 1):
            query = query.strip()
            if not query:
                continue
            print(f"\nЗапрос {i}:")
            try:
                cursor.execute(query)
                rows = cursor.fetchall()
                for row in rows:
                    print(row)
            except Exception as e:
                print(f"Ошибка: {e}")
        connection.commit()

# Класс для генерации ER-диаграммы (опционально)
class ErdGenerator:
    def generate(self, schema_path: str, output_png: str):
        try:
            import graphviz
            # Парсим CREATE TABLE из schema.sql
            dot = graphviz.Digraph('ERD', format='png')
            dot.attr(rankdir='LR')
            with open(schema_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Простой парсер (для демонстрации) – можно доработать
            for line in content.split(';'):
                if line.strip().upper().startswith('CREATE TABLE'):
                    table_name = line.split('(')[0].split()[-1].strip()
                    dot.node(table_name, shape='box')
                if 'REFERENCES' in line:
                    parts = line.split('REFERENCES')
                    col = parts[0].strip().split()[-1]
                    ref = parts[1].strip().split('(')[0]
                    dot.edge(col, ref[0] if ref else 'unknown')  # упрощённо
            dot.render(output_png.replace('.png', ''), view=False)
            print(f"ER-диаграмма сохранена в {output_png}")
        except ImportError:
            print("graphviz не установлен. Пропуск генерации ER-диаграммы.")

# Фасад для всего процесса
class DatabaseBuilder:
    def __init__(self, db_path: str, schema: str, seed: str, checks: str):
        self.db_path = db_path
        self.schema_creator = SchemaCreator(schema)
        self.data_seeder = DataSeeder(seed)
        self.check_runner = CheckQueries(checks)

    def build(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        self.schema_creator.run(conn)
        self.data_seeder.run(conn)
        self.check_runner.run(conn)
        conn.close()
        print(f"База данных {self.db_path} готова.")

if __name__ == "__main__":
    # Устанавливаем абсолютные пути (замените на свои, если нужно)
    base_dir = Path(__file__).parent.resolve()
    db_path = str(base_dir / "sports.db")
    schema_path = str(base_dir / "schema.sql")
    seed_path = str(base_dir / "seed.sql")
    checks_path = str(base_dir / "checks.sql")

    builder = DatabaseBuilder(db_path, schema_path, seed_path, checks_path)
    builder.build()

    # Генерация ER-диаграммы
    erd = ErdGenerator()
    erd.generate(schema_path, str(base_dir / "erd.png"))