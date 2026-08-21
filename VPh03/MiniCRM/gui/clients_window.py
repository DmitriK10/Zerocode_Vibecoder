"""
gui/clients_window.py
Окно управления клиентами.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import webbrowser
from gui.base_table_window import BaseTableWindow
from gui.forms import ClientForm
from gui.google_config import get_reporter
from logger import logger

API_URL = "http://localhost:8000"

class ClientsWindow(BaseTableWindow):
    def __init__(self, parent):
        columns = ["id", "name", "company", "email", "phone", "status"]
        column_names = ["ID", "Имя", "Компания", "Email", "Телефон", "Статус"]
        super().__init__(parent, "Управление клиентами", "/clients/", columns, column_names)

    def add_record(self):
        form = ClientForm(self.window)
        data = form.get_result()
        if data:
            try:
                resp = requests.post(f"{API_URL}/clients/", json=data)
                resp.raise_for_status()
                logger.info("Клиент добавлен: %s", data.get("name"))
                messagebox.showinfo("Успех", "Клиент добавлен")
                self.load_data()
            except Exception as e:
                logger.error("Ошибка при добавлении клиента: %s", e)
                messagebox.showerror("Ошибка", f"Не удалось добавить клиента: {e}")

    def edit_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите запись для редактирования")
            return
        item = self.tree.item(selected[0])
        values = item['values']
        client_id = values[0]
        current_data = {
            "name": values[1],
            "company": values[2] or "",
            "email": values[3] or "",
            "phone": values[4] or "",
            "status": values[5] or "",
        }
        form = ClientForm(self.window, current_data)
        data = form.get_result()
        if data:
            # Убираем пустые значения
            data = {k: v for k, v in data.items() if v is not None and v != ""}
            try:
                resp = requests.put(f"{API_URL}/clients/{client_id}", json=data)
                resp.raise_for_status()
                logger.info("Клиент %s обновлён", client_id)
                messagebox.showinfo("Успех", "Клиент обновлён")
                self.load_data()
            except Exception as e:
                logger.error("Ошибка при обновлении клиента %s: %s", client_id, e)
                messagebox.showerror("Ошибка", f"Не удалось обновить клиента: {e}")

    def delete_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите запись для удаления")
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранного клиента?"):
            return
        item = self.tree.item(selected[0])
        client_id = item['values'][0]
        try:
            resp = requests.delete(f"{API_URL}/clients/{client_id}")
            resp.raise_for_status()
            logger.info("Клиент %s удалён", client_id)
            messagebox.showinfo("Успех", "Клиент удалён")
            self.load_data()
        except Exception as e:
            logger.error("Ошибка при удалении клиента %s: %s", client_id, e)
            messagebox.showerror("Ошибка", f"Не удалось удалить клиента: {e}")

    def export_report(self):
        try:
            reporter = get_reporter()
            result = reporter.export_clients_report()
            messagebox.showinfo(
                "Успех",
                f"Отчёт по клиентам создан!\nID: {result['file_id']}\nСсылка: {result['web_link']}"
            )
            webbrowser.open(result['web_link'])
            logger.info("Отчёт по клиентам выгружен: %s", result['web_link'])
        except Exception as e:
            logger.error("Ошибка при выгрузке отчёта по клиентам: %s", e)
            messagebox.showerror("Ошибка", f"Не удалось выгрузить отчёт: {e}")