"""
gui/main_window.py
Главное окно приложения с кнопками перехода.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from gui.clients_window import ClientsWindow
from gui.deals_window import DealsWindow
from gui.tasks_window import TasksWindow
from gui.settings_window import GoogleSettingsWindow
import requests
import threading

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Мини-CRM")
        self.root.geometry("400x300")

        # Проверка доступности бэкенда
        self.check_backend()

        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Мини-CRM", font=("Arial", 16)).pack(pady=10)

        ttk.Button(main_frame, text="Управление клиентами", command=self.open_clients).pack(pady=5, fill=tk.X)
        ttk.Button(main_frame, text="Управление сделками", command=self.open_deals).pack(pady=5, fill=tk.X)
        ttk.Button(main_frame, text="Управление задачами", command=self.open_tasks).pack(pady=5, fill=tk.X)
        ttk.Button(main_frame, text="Настройки Google", command=self.open_settings).pack(pady=5, fill=tk.X)
        ttk.Button(main_frame, text="Выход", command=root.quit).pack(pady=20, fill=tk.X)

    def check_backend(self):
        try:
            resp = requests.get("http://localhost:8000/clients/?limit=1")
            resp.raise_for_status()
        except:
            messagebox.showwarning("Предупреждение",
                                   "Бэкенд не отвечает. Убедитесь, что сервер запущен.")

    def open_clients(self):
        ClientsWindow(self.root)

    def open_deals(self):
        DealsWindow(self.root)

    def open_tasks(self):
        TasksWindow(self.root)

    def open_settings(self):
        GoogleSettingsWindow(self.root)