### 5. Демонстрация безопасности (SQL-инъекции и параметризация)

Небольшой Python-скрипт, показывающий опасную конкатенацию и правильный параметризованный метод.

**Файл:** `../sql_learning/sql_injection_demo.py`

```python
import sqlite3

DB_PATH = "../sql_learning/learning.db"

def dangerous_login(conn: sqlite3.Connection, username: str, password: str):
    """
    НЕБЕЗОПАСНЫЙ метод – прямая подстановка строк.
    Риск: SQL-инъекция.
    """
    cursor = conn.cursor()
    # Опасно! Вместо параметров используется форматирование / конкатенация.
    query = f"SELECT * FROM products WHERE Name = '{username}' AND SKU = '{password}'"
    print("Выполняется опасный запрос:", query)
    cursor.execute(query)
    return cursor.fetchall()

def safe_login(conn: sqlite3.Connection, username: str, password: str):
    """
    БЕЗОПАСНЫЙ метод – параметризованный запрос (placeholders ?).
    SQLite экранирует входные данные.
    """
    cursor = conn.cursor()
    query = "SELECT * FROM products WHERE Name = ? AND SKU = ?"
    print("Безопасный запрос с плейсхолдерами")
    cursor.execute(query, (username, password))
    return cursor.fetchall()

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    # Данные атакующего
    malicious_name = "' OR '1'='1'; DROP TABLE products; --"
    malicious_sku = "any"

    print("=== ДЕМОНСТРАЦИЯ SQL-ИНЪЕКЦИИ ===")
    try:
        # Попытка опасного вызова
        result = dangerous_login(conn, malicious_name, malicious_sku)
        print("Опасно: запрос выполнился, возможно, удалил таблицу!")
    except Exception as e:
        print("Опасный метод вызвал ошибку:", e)
        # В реальном приложении злоумышленник мог бы удалить таблицу.
        # Для демонстрации восстановим таблицу (на всякий случай перезапустим seed.py)
        print("Таблица products могла быть удалена. Восстановите её через seed.py")

    print("\n=== БЕЗОПАСНЫЙ ПАРАМЕТРИЗОВАННЫЙ ЗАПРОС ===")
    try:
        result = safe_login(conn, malicious_name, malicious_sku)
        print("Результат безопасного запроса:", result)
        print("Инъекция не сработала, таблица цела.")
    except Exception as e:
        print("Ошибка:", e)

    conn.close()