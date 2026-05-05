# ../sql_learning/seed.py
import sqlite3
import random
import string
from pathlib import Path

# Абсолютный путь к БД
DB_PATH = Path("../sql_learning/learning.db")

# Константы для генерации
CATEGORIES = ["Электроника", "Книги", "Одежда", "Дом", "Игрушки", "Спорт"]
NAMES = {
    "Электроника": ["Смартфон", "Ноутбук", "Планшет", "Наушники", "Зарядка"],
    "Книги": ["Роман", "Детектив", "Фантастика", "Учебник", "Словарь"],
    "Одежда": ["Футболка", "Джинсы", "Куртка", "Шапка", "Кроссовки"],
    "Дом": ["Стул", "Стол", "Лампа", "Кастрюля", "Полка"],
    "Игрушки": ["Кукла", "Машинка", "Конструктор", "Мяч", "Пазл"],
    "Спорт": ["Мяч", "Гантели", "Коврик", "Скакалка", "Велосипед"]
}

def get_connection() -> sqlite3.Connection:
    """Создаёт подключение к БД (Single Responsibility)."""
    return sqlite3.connect(DB_PATH)

def create_tables(conn: sqlite3.Connection) -> None:
    """Создаёт таблицы products и orders."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Description TEXT,
            Category TEXT,
            Price REAL,
            SKU TEXT UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Product_ID INTEGER,
            Quantity INTEGER,
            Order_Date DATE,
            FOREIGN KEY (Product_ID) REFERENCES products(ID)
        )
    """)
    conn.commit()

def random_sku() -> str:
    """Генерирует уникальный SKU (буквы+цифры)."""
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    digits = ''.join(random.choices(string.digits, k=4))
    return f"{letters}{digits}"

def generate_products(n: int = 150) -> list:
    """Генерирует список товаров (кортежей) для вставки."""
    products = []
    for _ in range(n):
        category = random.choice(CATEGORIES)
        name = random.choice(NAMES[category]) + " " + str(random.randint(1, 100))
        price = round(random.uniform(100, 50000), 2)
        sku = random_sku()
        desc = f"Описание для {name}"
        products.append((name, desc, category, price, sku))
    return products

def insert_products(conn: sqlite3.Connection, products: list) -> None:
    """Массовая вставка товаров (параметризованный запрос)."""
    cursor = conn.cursor()
    cursor.executemany("""
        INSERT INTO products (Name, Description, Category, Price, SKU)
        VALUES (?, ?, ?, ?, ?)
    """, products)
    conn.commit()

def generate_orders(conn: sqlite3.Connection, num_orders: int = 50) -> None:
    """Создаёт случайные заказы на существующие товары."""
    cursor = conn.cursor()
    # Получаем все ID товаров
    cursor.execute("SELECT ID FROM products")
    product_ids = [row[0] for row in cursor.fetchall()]
    if not product_ids:
        return
    orders = []
    for _ in range(num_orders):
        product_id = random.choice(product_ids)
        quantity = random.randint(1, 10)
        # Случайная дата за последние 30 дней
        order_date = f"2025-03-{random.randint(1, 28):02d}"
        orders.append((product_id, quantity, order_date))
    cursor.executemany("""
        INSERT INTO orders (Product_ID, Quantity, Order_Date)
        VALUES (?, ?, ?)
    """, orders)
    conn.commit()

def main():
    """Главная функция – точка входа."""
    conn = get_connection()
    try:
        create_tables(conn)
        print("Таблицы созданы.")
        products = generate_products(150)  # ≥100 товаров
        insert_products(conn, products)
        print(f"Добавлено {len(products)} товаров.")
        generate_orders(conn, 50)
        print("Добавлено 50 заказов.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()