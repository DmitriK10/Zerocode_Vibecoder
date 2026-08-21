"""
gui/settings_window.py
Окно настроек Google интеграции.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pathlib import Path

SETTINGS_FILE = Path.home() / ".crm_google_settings.txt"

class GoogleSettingsWindow:
    def __init__(self, parent, on_save_callback=None):
        self.parent = parent
        self.on_save = on_save_callback
        self.window = tk.Toplevel(parent)
        self.window.title("Настройки Google")
        self.window.geometry("600x250")
        self.window.transient(parent)
        self.window.grab_set()

        self.client_secret_path = tk.StringVar()
        self.credentials_path = tk.StringVar()
        self.folder_id = tk.StringVar()

        self.load_settings()

        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self.window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Client secret
        ttk.Label(frame, text="Путь к client_secret.json:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.client_secret_path, width=50).grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Button(frame, text="Обзор", command=self.browse_client_secret).grid(row=0, column=2, padx=5)

        # Credentials (сервисный аккаунт)
        ttk.Label(frame, text="Путь к credentials.json (сервисный):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.credentials_path, width=50).grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Button(frame, text="Обзор", command=self.browse_credentials).grid(row=1, column=2, padx=5)

        # Folder ID
        ttk.Label(frame, text="ID папки для отчётов:").grid(row=2, column=0, sticky=tk.W, pady=5)
        entry_folder = ttk.Entry(frame, textvariable=self.folder_id, width=50)
        entry_folder.grid(row=2, column=1, sticky=tk.W, pady=5)
        ttk.Button(frame, text="Вставить", command=self.paste_folder_id).grid(row=2, column=2, padx=5)

        # Кнопки
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=20)
        ttk.Button(btn_frame, text="Сохранить", command=self.save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.window.destroy).pack(side=tk.LEFT, padx=5)

    def browse_client_secret(self):
        path = filedialog.askopenfilename(
            title="Выберите client_secret.json",
            filetypes=[("JSON files", "*.json")]
        )
        if path:
            self.client_secret_path.set(path)

    def browse_credentials(self):
        path = filedialog.askopenfilename(
            title="Выберите credentials.json (сервисный аккаунт)",
            filetypes=[("JSON files", "*.json")]
        )
        if path:
            self.credentials_path.set(path)

    def paste_folder_id(self):
        try:
            text = self.window.clipboard_get()
            self.folder_id.set(text)
        except:
            messagebox.showerror("Ошибка", "Не удалось вставить из буфера обмена")

    def load_settings(self):
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                lines = f.read().strip().splitlines()
            for line in lines:
                if "=" in line:
                    key, val = line.split("=", 1)
                    if key == "client_secret":
                        self.client_secret_path.set(val)
                    elif key == "credentials":
                        self.credentials_path.set(val)
                    elif key == "folder_id":
                        self.folder_id.set(val)

    def save_settings(self):
        # Проверка заполненности
        if not self.client_secret_path.get().strip():
            messagebox.showerror("Ошибка", "Укажите путь к client_secret.json")
            return
        if not self.credentials_path.get().strip():
            messagebox.showerror("Ошибка", "Укажите путь к credentials.json (сервисный аккаунт)")
            return
        if not self.folder_id.get().strip():
            messagebox.showerror("Ошибка", "Укажите ID папки")
            return

        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            f.write(f"client_secret={self.client_secret_path.get()}\n")
            f.write(f"credentials={self.credentials_path.get()}\n")
            f.write(f"folder_id={self.folder_id.get()}\n")
        messagebox.showinfo("Успех", "Настройки сохранены")
        if self.on_save:
            self.on_save()
        self.window.destroy()