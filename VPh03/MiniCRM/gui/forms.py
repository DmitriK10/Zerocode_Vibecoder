"""
gui/forms.py
Диалоговые окна для добавления/редактирования клиентов, сделок, задач.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class BaseForm(tk.Toplevel):
    """Базовый класс для формы с полями и кнопками."""
    def __init__(self, parent, title, fields, data=None):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.fields = fields
        self.data = data or {}
        self.result = None
        self.entries = {}

        self.geometry("400x300")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        self.fill_data()

    def create_widgets(self):
        frame = ttk.Frame(self, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        row = 0
        for label, key in self.fields:
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=5)
            entry = ttk.Entry(frame, width=30)
            entry.grid(row=row, column=1, sticky=tk.W, pady=5)
            self.entries[key] = entry
            row += 1

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Сохранить", command=self.on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def fill_data(self):
        for key, value in self.data.items():
            if key in self.entries:
                self.entries[key].insert(0, str(value) if value is not None else "")

    def on_save(self):
        self.result = {}
        for key, entry in self.entries.items():
            val = entry.get().strip()
            self.result[key] = val if val else None
        # Преобразование типов для числовых полей
        if "amount" in self.result and self.result["amount"]:
            try:
                self.result["amount"] = float(self.result["amount"])
            except ValueError:
                messagebox.showerror("Ошибка", "Сумма должна быть числом")
                return
        if "client_id" in self.result and self.result["client_id"]:
            try:
                self.result["client_id"] = int(self.result["client_id"])
            except ValueError:
                messagebox.showerror("Ошибка", "ID клиента должен быть числом")
                return
        if "deal_id" in self.result and self.result["deal_id"]:
            try:
                self.result["deal_id"] = int(self.result["deal_id"])
            except ValueError:
                messagebox.showerror("Ошибка", "ID сделки должен быть числом")
                return
        if "is_done" in self.result and self.result["is_done"]:
            try:
                self.result["is_done"] = int(self.result["is_done"])
            except ValueError:
                messagebox.showerror("Ошибка", "Значение выполнена должно быть 0 или 1")
                return
        self.destroy()

    def get_result(self):
        self.wait_window()
        return self.result


class ClientForm(BaseForm):
    def __init__(self, parent, data=None):
        fields = [
            ("Имя", "name"),
            ("Компания", "company"),
            ("Email", "email"),
            ("Телефон", "phone"),
            ("Статус", "status"),
        ]
        super().__init__(parent, "Клиент", fields, data)


class DealForm(BaseForm):
    def __init__(self, parent, data=None):
        fields = [
            ("Название", "title"),
            ("Сумма", "amount"),
            ("Статус", "status"),
            ("ID клиента", "client_id"),
        ]
        super().__init__(parent, "Сделка", fields, data)


class TaskForm(BaseForm):
    def __init__(self, parent, data=None):
        fields = [
            ("Название", "title"),
            ("Описание", "description"),
            ("Срок (ГГГГ-ММ-ДД ЧЧ:ММ:СС)", "due_date"),
            ("Выполнена (0/1)", "is_done"),
            ("ID клиента", "client_id"),
            ("ID сделки", "deal_id"),
        ]
        super().__init__(parent, "Задача", fields, data)