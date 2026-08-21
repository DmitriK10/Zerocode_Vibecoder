"""
gui/tasks_window.py
Окно управления задачами.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import webbrowser
from gui.base_table_window import BaseTableWindow
from gui.forms import TaskForm
from gui.google_config import get_reporter
from logger import logger

API_URL = "http://localhost:8000"

class TasksWindow(BaseTableWindow):
    def __init__(self, parent):
        columns = ["id", "title", "description", "due_date", "is_done", "client_id", "deal_id"]
        column_names = ["ID", "Название", "Описание", "Срок", "Выполнена", "ID клиента", "ID сделки"]
        super().__init__(parent, "Управление задачами", "/tasks/", columns, column_names)

    def add_record(self):
        form = TaskForm(self.window)
        data = form.get_result()
        if data:
            try:
                resp = requests.post(f"{API_URL}/tasks/", json=data)
                resp.raise_for_status()
                logger.info("Задача добавлена: %s", data.get("title"))
                messagebox.showinfo("Успех", "Задача добавлена")
                self.load_data()
            except Exception as e:
                logger.error("Ошибка при добавлении задачи: %s", e)
                messagebox.showerror("Ошибка", f"Не удалось добавить задачу: {e}")

    def edit_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите запись для редактирования")
            return
        item = self.tree.item(selected[0])
        values = item['values']
        task_id = values[0]
        current_data = {
            "title": values[1],
            "description": values[2] or "",
            "due_date": values[3] or "",
            "is_done": values[4] or "",
            "client_id": values[5] or "",
            "deal_id": values[6] or "",
        }
        form = TaskForm(self.window, current_data)
        data = form.get_result()
        if data:
            data = {k: v for k, v in data.items() if v is not None and v != ""}
            try:
                resp = requests.put(f"{API_URL}/tasks/{task_id}", json=data)
                resp.raise_for_status()
                logger.info("Задача %s обновлена", task_id)
                messagebox.showinfo("Успех", "Задача обновлена")
                self.load_data()
            except Exception as e:
                logger.error("Ошибка при обновлении задачи %s: %s", task_id, e)
                messagebox.showerror("Ошибка", f"Не удалось обновить задачу: {e}")

    def delete_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите запись для удаления")
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранную задачу?"):
            return
        item = self.tree.item(selected[0])
        task_id = item['values'][0]
        try:
            resp = requests.delete(f"{API_URL}/tasks/{task_id}")
            resp.raise_for_status()
            logger.info("Задача %s удалена", task_id)
            messagebox.showinfo("Успех", "Задача удалена")
            self.load_data()
        except Exception as e:
            logger.error("Ошибка при удалении задачи %s: %s", task_id, e)
            messagebox.showerror("Ошибка", f"Не удалось удалить задачу: {e}")

    def export_report(self):
        try:
            reporter = get_reporter()
            result = reporter.export_tasks_report()
            messagebox.showinfo(
                "Успех",
                f"Отчёт по задачам создан!\nID: {result['file_id']}\nСсылка: {result['web_link']}"
            )
            webbrowser.open(result['web_link'])
            logger.info("Отчёт по задачам выгружен: %s", result['web_link'])
        except Exception as e:
            logger.error("Ошибка при выгрузке отчёта по задачам: %s", e)
            messagebox.showerror("Ошибка", f"Не удалось выгрузить отчёт: {e}")