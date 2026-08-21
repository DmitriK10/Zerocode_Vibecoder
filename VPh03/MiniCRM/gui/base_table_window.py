"""
gui/base_table_window.py
Базовый класс для окон со списком записей.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading

API_URL = "http://localhost:8000"

class BaseTableWindow:
    def __init__(self, parent, title, api_endpoint, columns, column_names):
        self.parent = parent
        self.title = title
        self.api_endpoint = api_endpoint
        self.columns = columns
        self.column_names = column_names

        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("900x500")

        self.tree = ttk.Treeview(self.window, columns=columns, show="headings")
        for col, name in zip(columns, column_names):
            self.tree.heading(col, text=name)
            self.tree.column(col, width=100)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Добавить", command=self.add_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Редактировать", command=self.edit_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Обновить", command=self.load_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Выгрузить отчёт", command=self.export_report).pack(side=tk.LEFT, padx=5)

        self.load_data()

    def load_data(self):
        """Загружает данные из API и заполняет таблицу."""
        try:
            resp = requests.get(f"{API_URL}{self.api_endpoint}")
            resp.raise_for_status()
            data = resp.json()
            self._populate_tree(data)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")

    def _populate_tree(self, data):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for item in data:
            values = [item.get(col, "") for col in self.columns]
            self.tree.insert("", tk.END, values=values)

    def add_record(self):
        """Метод для добавления записи. Переопределяется в наследниках."""
        messagebox.showinfo("Инфо", "Функция добавления не реализована")

    def edit_record(self):
        """Метод для редактирования. Переопределяется."""
        messagebox.showinfo("Инфо", "Функция редактирования не реализована")

    def delete_record(self):
        """Метод для удаления. Переопределяется."""
        messagebox.showinfo("Инфо", "Функция удаления не реализована")

    def export_report(self):
        """Выгружает отчёт в Google Sheets."""
        # Сбор данных из API
        try:
            resp = requests.get(f"{API_URL}{self.api_endpoint}")
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить данные для отчёта: {e}")
            return

        if not data:
            messagebox.showinfo("Инфо", "Нет данных для выгрузки")
            return

        # Здесь будет логика формирования отчёта с использованием google_drive и google_sheets
        # Вызываем функцию из интеграции (реализуем отдельно)
        # Пока заглушка
        messagebox.showinfo("Инфо", "Функция выгрузки отчёта в разработке")