import sqlite3
import os
import random

DB_PATH = os.path.join(os.path.dirname(__file__), 'movies.db')

def get_connection():
    """Возвращает соединение с БД."""
    return sqlite3.connect(DB_PATH)

def init_db():
    """Создаёт таблицу movies, индексы и заполняет тестовыми данными."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            director TEXT NOT NULL,
            genre TEXT NOT NULL,
            year INTEGER,
            rating REAL
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_director ON movies(director)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_genre ON movies(genre)')

    cursor.execute('SELECT COUNT(*) FROM movies')
    count = cursor.fetchone()[0]
    if count == 0:
        movies_data = [
            ('Побег из Шоушенка', 'Фрэнк Дарабонт', 'Драма', 1994, 9.3),
            ('Крёстный отец', 'Фрэнсис Форд Коппола', 'Криминал', 1972, 9.2),
            ('Тёмный рыцарь', 'Кристофер Нолан', 'Боевик', 2008, 9.0),
            ('Список Шиндлера', 'Стивен Спилберг', 'Драма', 1993, 8.9),
            ('Криминальное чтиво', 'Квентин Тарантино', 'Криминал', 1994, 8.9),
            ('Властелин колец: Возвращение короля', 'Питер Джексон', 'Фэнтези', 2003, 8.9),
            ('Бойцовский клуб', 'Дэвид Финчер', 'Триллер', 1999, 8.8),
            ('Начало', 'Кристофер Нолан', 'Фантастика', 2010, 8.8),
            ('Форрест Гамп', 'Роберт Земекис', 'Драма', 1994, 8.8),
            ('Зелёная миля', 'Фрэнк Дарабонт', 'Драма', 1999, 8.6),
            ('Интерстеллар', 'Кристофер Нолан', 'Фантастика', 2014, 8.6),
            ('Молчание ягнят', 'Джонатан Демме', 'Триллер', 1991, 8.6),
            ('Гладиатор', 'Ридли Скотт', 'Боевик', 2000, 8.5),
            ('Унесённые призраками', 'Хаяо Миядзаки', 'Аниме', 2001, 8.6),
            ('Пираты Карибского моря', 'Гор Вербински', 'Приключения', 2003, 8.0),
            ('Матрица', 'Лана Вачовски', 'Фантастика', 1999, 8.7),
            ('Терминатор 2', 'Джеймс Кэмерон', 'Боевик', 1991, 8.5),
            ('Пятый элемент', 'Люк Бессон', 'Фантастика', 1997, 7.7),
            ('Аватар', 'Джеймс Кэмерон', 'Фантастика', 2009, 7.8),
            ('Гарри Поттер и философский камень', 'Крис Коламбус', 'Фэнтези', 2001, 7.6),
            ('Властелин колец: Братство кольца', 'Питер Джексон', 'Фэнтези', 2001, 8.8),
            ('Властелин колец: Две крепости', 'Питер Джексон', 'Фэнтези', 2002, 8.7),
            ('Социальная сеть', 'Дэвид Финчер', 'Драма', 2010, 7.7),
            ('Игра престолов (сезон 1)', 'Тим Ван Паттен', 'Фэнтези', 2011, 9.3),
            ('Звёздные войны: Новая надежда', 'Джордж Лукас', 'Фантастика', 1977, 8.6)
        ]
        cursor.executemany('INSERT INTO movies (title, director, genre, year, rating) VALUES (?,?,?,?,?)', movies_data)
        conn.commit()
    conn.close()

# ---------- Основные функции работы с БД ----------

def list_movies():
    """Возвращает список всех фильмов, отсортированных по id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, director, genre, year, rating FROM movies ORDER BY id')
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'title': r[1], 'director': r[2], 'genre': r[3], 'year': r[4], 'rating': r[5]} for r in rows]

def find_movie_by_title(title):
    """Поиск фильмов по части названия (регистронезависимо)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, director, genre, year, rating FROM movies WHERE LOWER(title) LIKE ?', (f'%{title.lower()}%',))
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'title': r[1], 'director': r[2], 'genre': r[3], 'year': r[4], 'rating': r[5]} for r in rows]

def find_movies_by_director(director):
    """Поиск фильмов по части имени режиссёра (регистронезависимо)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, director, genre, year, rating FROM movies WHERE LOWER(director) LIKE ?', (f'%{director.lower()}%',))
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'title': r[1], 'director': r[2], 'genre': r[3], 'year': r[4], 'rating': r[5]} for r in rows]

def find_movies_by_genre(genre):
    """Поиск фильмов по жанру (точное совпадение, регистронезависимо)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, director, genre, year, rating FROM movies WHERE LOWER(genre) = ?', (genre.lower(),))
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'title': r[1], 'director': r[2], 'genre': r[3], 'year': r[4], 'rating': r[5]} for r in rows]

def add_movie(title, director, genre, year=None, rating=None):
    """Добавляет новый фильм и возвращает его ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO movies (title, director, genre, year, rating) VALUES (?,?,?,?,?)',
                   (title, director, genre, year, rating))
    conn.commit()
    movie_id = cursor.lastrowid
    conn.close()
    return {'id': movie_id, 'title': title, 'director': director, 'genre': genre, 'year': year, 'rating': rating}

def delete_movie(movie_id):
    """Удаляет фильм по ID. Возвращает True, если удаление произошло."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM movies WHERE id = ?', (movie_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

def update_movie_rating(movie_id, new_rating):
    """Обновляет рейтинг фильма. Возвращает обновлённую запись или None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE movies SET rating = ? WHERE id = ?', (new_rating, movie_id))
    conn.commit()
    updated = cursor.rowcount > 0
    if updated:
        cursor.execute('SELECT id, title, director, genre, year, rating FROM movies WHERE id = ?', (movie_id,))
        row = cursor.fetchone()
        conn.close()
        return {'id': row[0], 'title': row[1], 'director': row[2], 'genre': row[3], 'year': row[4], 'rating': row[5]}
    conn.close()
    return None

def get_top_movies(limit=5):
    """Возвращает топ-N фильмов по рейтингу (по убыванию)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, director, genre, year, rating FROM movies ORDER BY rating DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'title': r[1], 'director': r[2], 'genre': r[3], 'year': r[4], 'rating': r[5]} for r in rows]

def get_random_movie():
    """Возвращает случайный фильм."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, director, genre, year, rating FROM movies ORDER BY RANDOM() LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'title': row[1], 'director': row[2], 'genre': row[3], 'year': row[4], 'rating': row[5]}
    return None