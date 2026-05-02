import sqlite3
import os
from typing import List, Tuple, Any

# ----------------------------------------------------------------------
# 1. Класс для управления подключением к БД (Single Responsibility)
# ----------------------------------------------------------------------
class DatabaseConnection:
    """Отвечает за подключение и закрытие соединения с SQLite."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
    
    def connect(self) -> sqlite3.Connection:
        """Устанавливает соединение и включает поддержку внешних ключей."""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.execute("PRAGMA foreign_keys = ON;")
        print(f"Подключение к базе данных установлено: {self.db_path}")
        return self.connection
    
    def close(self):
        """Закрывает соединение, если оно открыто."""
        if self.connection:
            self.connection.close()
            print("Соединение закрыто.")

# ----------------------------------------------------------------------
# 2. Класс для создания таблиц (Single Responsibility)
# ----------------------------------------------------------------------
class TableCreator:
    """Создаёт таблицы в базе данных."""
    
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
    
    def create_tables(self):
        """Выполняет SQL-скрипты для создания трёх таблиц."""
        cursor = self.connection.cursor()
        
        # Таблица продуктов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')
        
        # Таблица рецептов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE,
                description TEXT,
                instructions TEXT
            )
        ''')
        
        # Связующая таблица (many-to-many) с дополнительным полем quantity
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipe_products (
                recipe_id INTEGER,
                product_id INTEGER,
                quantity TEXT,  -- количество (например, '2 шт.', '500 мл')
                PRIMARY KEY (recipe_id, product_id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        ''')
        
        self.connection.commit()
        print("Таблицы 'products', 'recipes', 'recipe_products' успешно созданы.")

# ----------------------------------------------------------------------
# 3. Класс для вставки начальных данных (Single Responsibility)
# ----------------------------------------------------------------------
class DataInserter:
    """Заполняет таблицы тестовыми данными."""
    
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
    
    def insert_products(self, products: List[str]):
        """Вставляет список продуктов."""
        cursor = self.connection.cursor()
        for name in products:
            cursor.execute("INSERT OR IGNORE INTO products (name) VALUES (?)", (name,))
        self.connection.commit()
        print(f"Добавлены продукты: {', '.join(products)}")
    
    def insert_recipes(self, recipes: List[Tuple[str, str, str]]):
        """
        Вставляет рецепты.
        Каждый элемент: (title, description, instructions)
        """
        cursor = self.connection.cursor()
        for title, desc, instr in recipes:
            cursor.execute('''
                INSERT OR IGNORE INTO recipes (title, description, instructions)
                VALUES (?, ?, ?)
            ''', (title, desc, instr))
        self.connection.commit()
        print(f"Добавлены рецепты: {', '.join(r[0] for r in recipes)}")
    
    def link_product_to_recipe(self, recipe_title: str, product_name: str, quantity: str):
        """
        Связывает продукт с рецептом, указывая количество.
        Использует названия для поиска ID.
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM recipes WHERE title = ?", (recipe_title,))
        recipe_row = cursor.fetchone()
        cursor.execute("SELECT id FROM products WHERE name = ?", (product_name,))
        product_row = cursor.fetchone()
        
        if not recipe_row or not product_row:
            print(f"Ошибка: не найден рецепт '{recipe_title}' или продукт '{product_name}'")
            return
        
        recipe_id, product_id = recipe_row[0], product_row[0]
        cursor.execute('''
            INSERT OR IGNORE INTO recipe_products (recipe_id, product_id, quantity)
            VALUES (?, ?, ?)
        ''', (recipe_id, product_id, quantity))
        self.connection.commit()
        print(f"Связь: {product_name} ({quantity}) -> {recipe_title}")

# ----------------------------------------------------------------------
# 4. Основная функция (High-level orchestration)
# ----------------------------------------------------------------------
def main():
    # Полный путь к файлу базы данных
    db_filename = "recipe_database.db"
    db_full_path = os.path.join(os.getcwd(), db_filename)
    print(f"Файл базы данных будет создан по пути: {db_full_path}")
    
    # Удаляем старый файл, если он существует (для чистоты эксперимента)
    if os.path.exists(db_full_path):
        os.remove(db_full_path)
        print(f"Старый файл {db_full_path} удалён.")
    
    # Инициализация компонентов с соблюдением Dependency Inversion
    db_conn = DatabaseConnection(db_full_path)
    connection = db_conn.connect()
    
    try:
        # Создание таблиц
        table_creator = TableCreator(connection)
        table_creator.create_tables()
        
        # Вставка продуктов
        inserter = DataInserter(connection)
        products = ["Мука", "Яйца", "Молоко", "Сахар", "Соль", "Масло сливочное"]
        inserter.insert_products(products)
        
        # Вставка рецептов
        recipes = [
            ("Блины", "Классические тонкие блины", "Смешать муку, яйца, молоко, сахар, соль. Жарить на сковороде."),
            ("Омлет", "Пышный омлет на завтрак", "Взбить яйца с молоком и солью. Обжарить на масле."),
            ("Пирог", "Песочный пирог с начинкой", "Замесить тесто из муки, масла, сахара и яиц. Выпекать 30 мин.")
        ]
        inserter.insert_recipes(recipes)
        
        # Связи many-to-many (продукты -> рецепты)
        links = [
            ("Блины", "Мука", "2 стакана"),
            ("Блины", "Яйца", "2 шт."),
            ("Блины", "Молоко", "500 мл"),
            ("Блины", "Сахар", "1 ст.л."),
            ("Блины", "Соль", "щепотка"),
            ("Омлет", "Яйца", "3 шт."),
            ("Омлет", "Молоко", "100 мл"),
            ("Омлет", "Соль", "по вкусу"),
            ("Омлет", "Масло сливочное", "20 г"),
            ("Пирог", "Мука", "300 г"),
            ("Пирог", "Яйца", "3 шт."),
            ("Пирог", "Сахар", "150 г"),
            ("Пирог", "Масло сливочное", "100 г")
        ]
        for recipe, product, qty in links:
            inserter.link_product_to_recipe(recipe, product, qty)
        
        # Демонстрация работы: выборка всех продуктов для рецепта "Блины"
        print("\n--- Проверка связей (рецепт 'Блины') ---")
        cursor = connection.cursor()
        cursor.execute('''
            SELECT p.name, rp.quantity
            FROM recipe_products rp
            JOIN products p ON rp.product_id = p.id
            JOIN recipes r ON rp.recipe_id = r.id
            WHERE r.title = 'Блины'
        ''')
        for product_name, quantity in cursor.fetchall():
            print(f"  {product_name}: {quantity}")
        
        print("\n--- Рецепты, в которых используется продукт 'Яйца' ---")
        cursor.execute('''
            SELECT r.title, rp.quantity
            FROM recipe_products rp
            JOIN recipes r ON rp.recipe_id = r.id
            JOIN products p ON rp.product_id = p.id
            WHERE p.name = 'Яйца'
        ''')
        for recipe_title, quantity in cursor.fetchall():
            print(f"  {recipe_title}: {quantity}")
        
        print(f"\n✅ База данных успешно создана: {db_full_path}")
    
    except sqlite3.Error as e:
        print(f"Ошибка SQLite: {e}")
    finally:
        db_conn.close()

if __name__ == "__main__":
    main()