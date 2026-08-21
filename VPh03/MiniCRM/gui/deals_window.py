"""
gui/deals_window.py
Окно управления сделками.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import webbrowser
from gui.base_table_window import BaseTableWindow
from gui.forms import DealForm
from gui.google_config import get_reporter
from logger import logger

API_URL = "http://localhost:8000"

class DealsWindow(BaseTableWindow):
    def __init__(self, parent):
        columns = ["id", "title", "amount", "status", "client_id"]
        column_names = ["ID", "Название", "Сумма", "Статус", "ID клиента"]
        super().__init__(parent, "Управление сделками", "/deals/", columns, column_names)

    def add_record(self):
        form = DealForm(self.window)
        data = form.get_result()
        if data:
            try:
                resp = requests.post(f"{API_URL}/deals/", json=data)
                resp.raise_for_status()
                logger.info("Сделка добавлена: %s", data.get("title"))
                messagebox.showinfo("Успех", "Сделка добавлена")
                self.load_data()
            except Exception as e:
                logger.error("Ошибка при добавлении сделки: %s", e)
                messagebox.showerror("Ошибка", f"Не удалось добавить сделку: {e}")

    def edit_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите запись для редактирования")
            return
        item = self.tree.item(selected[0])
        values = item['values']
        deal_id = values[0]
        current_data = {
            "title": values[1],
            "amount": values[2] or "",
            "status": values[3] or "",
            "client_id": values[4] or "",
        }
        form = DealForm(self.window, current_data)
        data = form.get_result()
        if data:
            data = {k: v for k, v in data.items() if v is not None and v != ""}
            try:
                resp = requests.put(f"{API_URL}/deals/{deal_id}", json=data)
                resp.raise_for_status()
                logger.info("Сделка %s обновлена", deal_id)
                messagebox.showinfo("Успех", "Сделка обновлена")
                self.load_data()
            except Exception as e:
                logger.error("Ошибка при обновлении сделки %s: %s", deal_id, e)
                messagebox.showerror("Ошибка", f"Не удалось обновить сделку: {e}")

    def delete_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите запись для удаления")
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранную сделку?"):
            return
        item = self.tree.item(selected[0])
        deal_id = item['values'][0]
        try:
            resp = requests.delete(f"{API_URL}/deals/{deal_id}")
            resp.raise_for_status()
            logger.info("Сделка %s удалена", deal_id)
            messagebox.showinfo("Успех", "Сделка удалена")
            self.load_data()
        except Exception as e:
            logger.error("Ошибка при удалении сделки %s: %s", deal_id, e)
            messagebox.showerror("Ошибка", f"Не удалось удалить сделку: {e}")

    def export_report(self):
        try:
            reporter = get_reporter()
            result = reporter.export_deals_report()
            messagebox.showinfo(
                "Успех",
                f"Отчёт по сделкам создан!\nID: {result['file_id']}\nСсылка: {result['web_link']}"
            )
            webbrowser.open(result['web_link'])
            logger.info("Отчёт по сделкам выгружен: %s", result['web_link'])
        except Exception as e:
            logger.error("Ошибка при выгрузке отчёта по сделкам: %s", e)
            messagebox.showerror("Ошибка", f"Не удалось выгрузить отчёт: {e}")