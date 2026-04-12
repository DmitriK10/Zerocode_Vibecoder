#!/usr/bin/env python3
"""
CLI-менеджер паролей с шифрованием (рабочая версия).
Использует только разрешённые библиотеки.
"""

import os
import sys
import hashlib
import sqlite3
import random
import string
from pathlib import Path
from getpass import getpass
from cryptography.fernet import Fernet

# ---------------------- КОНСТАНТЫ ----------------------
DB_PATH = Path("passwords.db")
KEY_PATH = Path("secret.key")
MASTER_TABLE = "master_password"
PASSWORDS_TABLE = "passwords"


# ---------------------- РАБОТА С БАЗОЙ ДАННЫХ (ОДНО ПОДКЛЮЧЕНИЕ) ----------------------
class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._init_tables()

    def _connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def _init_tables(self):
        cur = self.conn.cursor()
        cur.execute(f'''
            CREATE TABLE IF NOT EXISTS {MASTER_TABLE} (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                password_hash TEXT NOT NULL
            )
        ''')
        cur.execute(f'''
            CREATE TABLE IF NOT EXISTS {PASSWORDS_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                login TEXT NOT NULL,
                encrypted_password TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def set_master_password(self, password_hash):
        cur = self.conn.cursor()
        cur.execute(f"DELETE FROM {MASTER_TABLE}")
        cur.execute(f"INSERT INTO {MASTER_TABLE} (password_hash) VALUES (?)", (password_hash,))
        self.conn.commit()

    def get_master_password_hash(self):
        cur = self.conn.cursor()
        cur.execute(f"SELECT password_hash FROM {MASTER_TABLE} LIMIT 1")
        row = cur.fetchone()
        return row["password_hash"] if row else None

    def add_password(self, name, login, encrypted_password):
        try:
            cur = self.conn.cursor()
            cur.execute(
                f"INSERT INTO {PASSWORDS_TABLE} (name, login, encrypted_password) VALUES (?, ?, ?)",
                (name, login, encrypted_password)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_password(self, name):
        cur = self.conn.cursor()
        cur.execute(f"SELECT login, encrypted_password FROM {PASSWORDS_TABLE} WHERE name = ?", (name,))
        row = cur.fetchone()
        return (row["login"], row["encrypted_password"]) if row else None

    def list_passwords(self):
        cur = self.conn.cursor()
        cur.execute(f"SELECT name, login FROM {PASSWORDS_TABLE} ORDER BY name")
        return [(row["name"], row["login"]) for row in cur.fetchall()]

    def delete_password(self, name):
        cur = self.conn.cursor()
        cur.execute(f"DELETE FROM {PASSWORDS_TABLE} WHERE name = ?", (name,))
        self.conn.commit()
        return cur.rowcount > 0

    def close(self):
        if self.conn:
            self.conn.close()


# ---------------------- ШИФРОВАНИЕ (FERNET) ----------------------
class EncryptionManager:
    def __init__(self, key_path=KEY_PATH):
        self.key_path = key_path
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)

    def _load_or_generate_key(self):
        if self.key_path.exists():
            with open(self.key_path, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_path, "wb") as f:
                f.write(key)
            return key

    def encrypt(self, plain_text):
        return self.cipher.encrypt(plain_text.encode()).decode()

    def decrypt(self, encrypted_text):
        return self.cipher.decrypt(encrypted_text.encode()).decode()


# ---------------------- ГЕНЕРАТОР ПАРОЛЕЙ (ОПТИМИЗИРОВАННЫЙ) ----------------------
class PasswordGenerator:
    @staticmethod
    def generate(length=16, use_upper=True, use_lower=True, use_digits=True, use_special=True):
        pool = ""
        if use_upper:
            pool += string.ascii_uppercase
        if use_lower:
            pool += string.ascii_lowercase
        if use_digits:
            pool += string.digits
        if use_special:
            pool += "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"
        if not pool:
            raise ValueError("Хотя бы один набор символов должен быть включён.")
        return ''.join(random.choices(pool, k=length))

    @staticmethod
    def interactive():
        print("\n--- Генерация пароля ---")
        while True:
            try:
                length = int(input("Длина пароля (8-64, по умолч. 16): ").strip() or "16")
                if 8 <= length <= 64:
                    break
                print("Длина должна быть от 8 до 64.")
            except ValueError:
                print("Введите целое число.")
        use_upper = input("Заглавные буквы? (y/n, по умолч. y): ").strip().lower() != 'n'
        use_lower = input("Строчные буквы? (y/n, по умолч. y): ").strip().lower() != 'n'
        use_digits = input("Цифры? (y/n, по умолч. y): ").strip().lower() != 'n'
        use_special = input("Спецсимволы? (y/n, по умолч. y): ").strip().lower() != 'n'
        password = PasswordGenerator.generate(length, use_upper, use_lower, use_digits, use_special)
        print(f"\nСгенерированный пароль: {password}")
        print("(Скопируйте пароль вручную)")
        return password


# ---------------------- ОСНОВНОЙ CLI КЛАСС ----------------------
class PasswordCLI:
    def __init__(self):
        self.db = DatabaseManager()
        self.crypto = EncryptionManager()

    def _read_secret(self, prompt):
        return getpass(prompt)

    def setup_master_password(self):
        print("Добро пожаловать! Это первый запуск.")
        print("Создайте мастер-пароль (ввод не отображается).")
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            p1 = self._read_secret("Введите мастер-пароль: ")
            if not p1:
                print("Пароль не может быть пустым.")
                continue
            p2 = self._read_secret("Повторите мастер-пароль: ")
            if p1 == p2:
                password_hash = hashlib.sha256(p1.encode()).hexdigest()
                self.db.set_master_password(password_hash)
                print("Мастер-пароль сохранён.\n")
                return
            print("Пароли не совпадают.")
            left = max_attempts - attempt
            if left:
                print(f"Осталось попыток: {left}")
        raise RuntimeError("Не удалось установить мастер-пароль.")

    def authenticate(self, max_attempts=3):
        saved_hash = self.db.get_master_password_hash()
        if not saved_hash:
            print("Мастер-пароль не найден. Запустите настройку заново.")
            return False
        for attempt in range(1, max_attempts + 1):
            entered = self._read_secret("Введите мастер-пароль: ")
            if not entered:
                print("Пароль не может быть пустым.")
                continue
            entered_hash = hashlib.sha256(entered.encode()).hexdigest()
            if entered_hash == saved_hash:
                print("\nАутентификация успешна!\n")
                return True
            left = max_attempts - attempt
            if left:
                print(f"Неверный пароль. Осталось попыток: {left}")
        print("Превышено число попыток. Выход.")
        return False

    def add_password(self):
        print("\n--- Добавление записи ---")
        name = input("Название (например, Google): ").strip()
        if not name:
            print("Название не может быть пустым.")
            return
        login = input("Логин: ").strip()
        if not login:
            print("Логин не может быть пустым.")
            return
        gen = input("Сгенерировать пароль автоматически? (y/n): ").strip().lower()
        if gen == 'y':
            password = PasswordGenerator.interactive()
        else:
            password = input("Введите пароль вручную: ").strip()
            if not password:
                print("Пароль не может быть пустым.")
                return
        encrypted = self.crypto.encrypt(password)
        if self.db.add_password(name, login, encrypted):
            print(f"Запись '{name}' успешно добавлена.")
        else:
            print(f"Ошибка: запись с именем '{name}' уже существует.")

    def get_password(self):
        print("\n--- Получение пароля ---")
        name = input("Введите название: ").strip()
        if not name:
            print("Название не указано.")
            return
        result = self.db.get_password(name)
        if result:
            login, encrypted = result
            try:
                password = self.crypto.decrypt(encrypted)
                print(f"\nНазвание: {name}")
                print(f"Логин: {login}")
                print(f"Пароль: {password}")
                print("(Скопируйте пароль вручную)")
            except Exception as e:
                print(f"Ошибка расшифровки: {e}")
        else:
            print(f"Запись '{name}' не найдена.")

    def list_passwords(self):
        print("\n--- Список записей ---")
        records = self.db.list_passwords()
        if not records:
            print("Нет сохранённых паролей.")
        else:
            for name, login in records:
                print(f"- {name} (логин: {login})")

    def delete_password(self):
        print("\n--- Удаление записи ---")
        name = input("Введите название для удаления: ").strip()
        if not name:
            print("Название не указано.")
            return
        confirm = input(f"Удалить запись '{name}'? (y/n): ").strip().lower()
        if confirm == 'y':
            if self.db.delete_password(name):
                print(f"Запись '{name}' удалена.")
            else:
                print(f"Запись '{name}' не найдена.")
        else:
            print("Удаление отменено.")

    def new_password(self):
        PasswordGenerator.interactive()

    def show_menu(self):
        print("\n" + "=" * 40)
        print("МЕНЕДЖЕР ПАРОЛЕЙ")
        print("1. Добавить запись")
        print("2. Получить пароль")
        print("3. Список всех записей")
        print("4. Удалить запись")
        print("5. Сгенерировать пароль")
        print("6. Выход")
        print("=" * 40)

    def run(self):
        if self.db.get_master_password_hash() is None:
            try:
                self.setup_master_password()
            except RuntimeError as e:
                print(e)
                input("Нажмите Enter для выхода...")
                self.db.close()
                return
        if not self.authenticate():
            input("Нажмите Enter для выхода...")
            self.db.close()
            return
        while True:
            self.show_menu()
            choice = input("Выберите действие (1-6): ").strip()
            if choice == "1":
                self.add_password()
            elif choice == "2":
                self.get_password()
            elif choice == "3":
                self.list_passwords()
            elif choice == "4":
                self.delete_password()
            elif choice == "5":
                self.new_password()
            elif choice == "6":
                print("До свидания!")
                break
            else:
                print("Неверный выбор. Попробуйте снова.")
            input("\nНажмите Enter для продолжения...")
        self.db.close()


if __name__ == "__main__":
    app = PasswordCLI()
    app.run()