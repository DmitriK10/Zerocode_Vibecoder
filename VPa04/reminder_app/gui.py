import datetime
import tkinter as tk
from tkinter import messagebox, ttk

from database import ReminderDatabase
from notifications import NotificationManager


class ReminderApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.db = ReminderDatabase("reminders.db")
        self.notification_manager = NotificationManager(self.db, self.root)

        self.title_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Все")
        self.datetime_var = tk.StringVar()

        self.tree = None
        self.status_label = None

    def setup_ui(self) -> None:
        self.root.title("Напоминалка Windows 11")
        self.root.geometry("1020x700")
        self.root.minsize(980, 660)

        title_label = tk.Label(self.root, text="Напоминалка", font=("Segoe UI", 24, "bold"))
        title_label.pack(pady=(20, 10))

        add_frame = tk.LabelFrame(self.root, text="Добавить новое напоминание", padx=12, pady=10)
        add_frame.pack(fill="x", padx=12, pady=(0, 10))

        tk.Label(add_frame, text="Заголовок:", font=("Segoe UI", 12)).grid(row=0, column=0, sticky="w", pady=6)
        tk.Entry(add_frame, textvariable=self.title_var, font=("Segoe UI", 12)).grid(
            row=0, column=1, columnspan=5, sticky="ew", pady=6
        )

        tk.Label(add_frame, text="Описание:", font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", pady=6)
        self.description_text = tk.Text(add_frame, height=2, font=("Segoe UI", 12))
        self.description_text.grid(row=1, column=1, columnspan=5, sticky="ew", pady=6)

        tk.Label(add_frame, text="Дата и время:", font=("Segoe UI", 12)).grid(row=2, column=0, sticky="w", pady=6)
        tk.Button(add_frame, text="Через 1 мин", command=lambda: self.set_quick_time(1)).grid(row=2, column=1, sticky="w")
        tk.Button(add_frame, text="Через 5 мин", command=lambda: self.set_quick_time(5)).grid(row=2, column=2, sticky="w")
        tk.Button(add_frame, text="Через 15 мин", command=lambda: self.set_quick_time(15)).grid(row=2, column=3, sticky="w")
        tk.Button(add_frame, text="Через 1 час", command=lambda: self.set_quick_time(60)).grid(row=2, column=4, sticky="w")

        self.datetime_entry = tk.Entry(add_frame, textvariable=self.datetime_var, font=("Segoe UI", 12))
        self.datetime_entry.grid(row=3, column=1, columnspan=5, sticky="ew", pady=(6, 2))
        self.datetime_var.set((datetime.datetime.now() + datetime.timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M"))

        tk.Button(add_frame, text="Добавить напоминание", command=self.add_reminder, font=("Segoe UI", 12, "bold")).grid(
            row=4, column=2, pady=14, sticky="e"
        )
        tk.Button(add_frame, text="Тест уведомления", command=self.test_notification, font=("Segoe UI", 12, "bold")).grid(
            row=4, column=3, pady=14, padx=(8, 0), sticky="w"
        )

        add_frame.grid_columnconfigure(1, weight=1)
        add_frame.grid_columnconfigure(2, weight=1)
        add_frame.grid_columnconfigure(3, weight=1)
        add_frame.grid_columnconfigure(4, weight=1)
        add_frame.grid_columnconfigure(5, weight=2)

        top_bar = tk.Frame(self.root)
        top_bar.pack(fill="x", padx=12, pady=(6, 8))
        tk.Label(top_bar, text="Фильтр по статусу:", font=("Segoe UI", 12)).pack(side="left")
        status_combo = ttk.Combobox(
            top_bar,
            textvariable=self.status_var,
            values=["Все", "Ожидает", "Готово", "Просрочено", "Отменено"],
            width=12,
            state="readonly",
            font=("Segoe UI", 11),
        )
        status_combo.pack(side="left", padx=(8, 8))
        status_combo.bind("<<ComboboxSelected>>", lambda _: self.refresh_reminders())

        tk.Button(top_bar, text="Обновить", command=self.refresh_reminders, font=("Segoe UI", 11, "bold")).pack(side="left")

        self.status_label = tk.Label(top_bar, text="", font=("Segoe UI", 12))
        self.status_label.pack(side="right")

        list_frame = tk.Frame(self.root)
        list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        tk.Label(list_frame, text="Список напоминаний", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 6))

        columns = ("id", "title", "description", "due_time", "status", "created_at")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Заголовок")
        self.tree.heading("description", text="Описание")
        self.tree.heading("due_time", text="Дата/Время")
        self.tree.heading("status", text="Статус")
        self.tree.heading("created_at", text="Создано")
        self.tree.column("id", width=60, anchor="center")
        self.tree.column("title", width=170)
        self.tree.column("description", width=260)
        self.tree.column("due_time", width=150, anchor="center")
        self.tree.column("status", width=120, anchor="center")
        self.tree.column("created_at", width=150, anchor="center")

        self.tree.tag_configure("Готово", background="#b8eec0")
        self.tree.tag_configure("Просрочено", background="#f8cccc")
        self.tree.tag_configure("Ожидает", background="#fdfdfd")
        self.tree.tag_configure("Отменено", background="#ececec")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self.on_double_click)

        actions = tk.Frame(self.root)
        actions.pack(fill="x", padx=12, pady=(0, 12))
        tk.Button(actions, text="Отметить как Готово", command=self.mark_as_done).pack(side="left")
        tk.Button(actions, text="Отменить", command=self.mark_as_cancelled).pack(side="left", padx=(8, 0))
        tk.Button(actions, text="Удалить", command=self.delete_reminder).pack(side="left", padx=(8, 0))

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_status_bar(self) -> None:
        counts = self.db.get_reminders_count()
        self.status_label.config(
            text=f"Всего: {counts['Всего']} | Ожидает: {counts['Ожидает']} | Готово: {counts['Готово']} | Просрочено: {counts['Просрочено']}"
        )

    def test_notification(self) -> None:
        self.notification_manager.test_notification()

    def set_quick_time(self, minutes: int) -> None:
        target = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        self.datetime_var.set(target.strftime("%Y-%m-%d %H:%M"))

    def _parse_datetime(self) -> datetime.datetime:
        try:
            return datetime.datetime.strptime(self.datetime_var.get().strip(), "%Y-%m-%d %H:%M")
        except ValueError as exc:
            raise ValueError("Используйте формат даты: ГГГГ-ММ-ДД ЧЧ:ММ") from exc

    def add_reminder(self) -> None:
        title = self.title_var.get().strip()
        description = self.description_text.get("1.0", "end").strip()
        if not title:
            messagebox.showwarning("Ошибка", "Введите заголовок напоминания.")
            return
        try:
            due_dt = self._parse_datetime()
            self.db.add_reminder(title, description, due_dt)
        except ValueError as err:
            messagebox.showerror("Ошибка", str(err))
            return

        self.title_var.set("")
        self.description_text.delete("1.0", "end")
        self.set_quick_time(1)
        self.refresh_reminders()

    def refresh_reminders(self) -> None:
        self.db.mark_overdue()
        rows = self.db.get_all_reminders(self.status_var.get())

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row["id"],
                    row["title"],
                    row["description"],
                    row["due_time"][:16].replace("-", "."),
                    row["status"],
                    row["created_at"][:16].replace("-", "."),
                ),
                tags=(row["status"],),
            )
        self.update_status_bar()

    def _get_selected_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите напоминание в списке.")
            return None
        values = self.tree.item(selected[0], "values")
        return int(values[0])

    def mark_as_done(self) -> None:
        reminder_id = self._get_selected_id()
        if reminder_id is None:
            return
        self.db.update_status(reminder_id, "Готово")
        self.refresh_reminders()

    def mark_as_cancelled(self) -> None:
        reminder_id = self._get_selected_id()
        if reminder_id is None:
            return
        self.db.update_status(reminder_id, "Отменено")
        self.refresh_reminders()

    def delete_reminder(self) -> None:
        reminder_id = self._get_selected_id()
        if reminder_id is None:
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранное напоминание?"):
            return
        self.db.delete_reminder(reminder_id)
        self.refresh_reminders()

    def on_double_click(self, _event) -> None:
        reminder_id = self._get_selected_id()
        if reminder_id is None:
            return
        reminder = self.db.get_reminder_by_id(reminder_id)
        if not reminder:
            return
        details = (
            f"ID: {reminder['id']}\n"
            f"Заголовок: {reminder['title']}\n"
            f"Описание: {reminder['description'] or '-'}\n"
            f"Дата/время: {reminder['due_time']}\n"
            f"Статус: {reminder['status']}\n"
            f"Создано: {reminder['created_at']}"
        )
        messagebox.showinfo("Детали напоминания", details)

    def on_closing(self) -> None:
        if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
            self.notification_manager.stop()
            self.root.destroy()

    def run(self) -> None:
        self.setup_ui()
        self.refresh_reminders()
        self.notification_manager.start()
        self.root.mainloop()
