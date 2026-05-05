-- =============================================
-- Файл: ../sql_learning/queries.sql
-- Все запросы SQLite
-- =============================================

-- 1. БАЗОВЫЕ ОПЕРАЦИИ INSERT (ручные + массовая)
-- 1.1 Ручной INSERT одного товара
INSERT INTO products (Name, Description, Category, Price, SKU)
VALUES ('Яблоки', 'Свежие красные яблоки', 'Продукты', 350.0, 'FRT001');

-- 1.2 Ручной INSERT второго товара
INSERT INTO products (Name, Description, Category, Price, SKU)
VALUES ('Батон', 'Хлеб пшеничный', 'Продукты', 45.0, 'BRD002');

-- 1.3 Ручной INSERT третьего товара
INSERT INTO products (Name, Description, Category, Price, SKU)
VALUES ('Молоко 1л', 'Пастеризованное', 'Продукты', 89.0, 'MLK003');

-- 1.4 Массовая вставка (добавим сразу 5 тестовых книг)
INSERT INTO products (Name, Description, Category, Price, SKU) VALUES
('Python для начинающих', 'Учебник', 'Книги', 1200.0, 'BOK004'),
('Искусство войны', 'Трактат', 'Книги', 550.0, 'BOK005'),
('1984', 'Роман-антиутопия', 'Книги', 420.0, 'BOK006'),
('Мастер и Маргарита', 'Роман', 'Книги', 610.0, 'BOK007'),
('Гарри Поттер', 'Фэнтези', 'Книги', 890.0, 'BOK008');

-- 2. ОСМЫСЛЕННЫЕ UPDATE (обязательно с WHERE)

-- 2.1 Скидка 15% на все товары категории "Электроника"
UPDATE products
SET Price = Price * 0.85
WHERE Category = 'Электроника';

-- 2.2 Изменить описание для товара с конкретным SKU
UPDATE products
SET Description = 'Супер-акция! Успей купить.'
WHERE SKU = 'FRT001';

-- 2.3 Категорию "Игрушки" переименовать в "Детские товары"
UPDATE products
SET Category = 'Детские товары'
WHERE Category = 'Игрушки';

-- 3. DELETE с безопасным WHERE (удалим тестовые записи, добавленные массово)
DELETE FROM products
WHERE SKU IN ('BOK004', 'BOK005', 'BOK006', 'BOK007', 'BOK008');

-- 4. ЧТЕНИЕ И АНАЛИЗ

-- 4.1 SELECT с WHERE + ORDER BY + LIMIT (топ-10 самых дорогих товаров дороже 1000)
SELECT Name, Price, SKU
FROM products
WHERE Price > 1000
ORDER BY Price DESC
LIMIT 10;

-- 4.2 Агрегация: количество товаров и средняя цена по категориям (исключая категории с ≤5 товарами)
SELECT Category,
       COUNT(*) AS ProductCount,
       AVG(Price) AS AvgPrice
FROM products
GROUP BY Category
HAVING COUNT(*) > 5;

-- 4.3 LIKE / поиск по шаблону (регистронезависимый, через UPPER)
-- Найдём товары, SKU которых начинается на 'URW' (или 'urw')
SELECT Name, SKU
FROM products
WHERE UPPER(SKU) LIKE 'URW%';

-- 4.4 JOIN: сводная выборка заказов с названием товара и суммой заказа по категориям
-- (показывает sum(quantity) по категориям)
SELECT p.Category,
       COUNT(o.ID) AS NumberOfOrders,
       SUM(o.Quantity) AS TotalItemsOrdered
FROM orders o
JOIN products p ON o.Product_ID = p.ID
GROUP BY p.Category
ORDER BY TotalItemsOrdered DESC;

-- Дополнительный JOIN для наглядного списка заказов с названием товара
SELECT o.ID AS OrderID,
       p.Name AS ProductName,
       o.Quantity,
       o.Order_Date
FROM orders o
JOIN products p ON o.Product_ID = p.ID
LIMIT 20;