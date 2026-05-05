# Инструкция по оператору INSERT в SQL

**Файл:** `C:/Users/Student/sql_learning/insert_products_explained.md`

## Что такое INSERT?

`INSERT` – оператор языка SQL, предназначенный для добавления новых строк (записей) в таблицу. Без него таблица остаётся пустой, и другие операторы (`SELECT`, `UPDATE`, `DELETE`) теряют смысл.

## Базовый синтаксис

```sql
INSERT INTO table_name (column1, column2, ...)
VALUES (value1, value2, ...);