import threading
import time
import tkinter as tk
from typing import Optional

try:
    from win10toast import ToastNotifier
except Exception:  # pragma: no cover - зависимость опциональна
    ToastNotifier = None


class NotificationManager:
    def __init__(self, db, root: tk.Tk):
        self.db = db
        self.root = root
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.toaster = ToastNotifier() if ToastNotifier else None
        self.toast_available = self.toaster is not None

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._check_loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.5)

    def _check_loop(self) -> None:
        while self.running:
            self.db.mark_overdue()
            self._check_and_notify()
            time.sleep(1)

    def _check_and_notify(self) -> None:
        due_reminders = self.db.get_due_reminders()
        for reminder in due_reminders:
            self._show_notification(reminder["title"], reminder["description"] or "Напоминание")
            self.db.update_status(reminder["id"], "Готово")

    def _show_notification(self, title: str, message: str) -> None:
        used_toast = False
        if self.toast_available and self.toaster:
            try:
                self.toaster.show_toast(title, message, duration=8, threaded=True)
                used_toast = True
            except Exception:
                self.toast_available = False
        if not used_toast:
            self.root.after(0, lambda: self._show_popup(title, message))

    def _show_popup(self, title: str, message: str) -> None:
        popup = tk.Toplevel(self.root)
        popup.title("Напоминание")
        popup.attributes("-topmost", True)
        popup.geometry("420x180")
        popup.resizable(False, False)

        # Поднимаем поверх остальных и пытаемся дать фокус.
        popup.lift()
        popup.focus_force()
        popup.grab_set()

        frame = tk.Frame(popup, padx=16, pady=14)
        frame.pack(fill="both", expand=True)
        tk.Label(frame, text=title, font=("Segoe UI", 11, "bold"), wraplength=380, anchor="w", justify="left").pack(fill="x")
        tk.Label(frame, text=message, font=("Segoe UI", 10), wraplength=380, anchor="w", justify="left").pack(fill="x", pady=(8, 14))
        tk.Button(frame, text="OK", width=10, command=popup.destroy).pack(anchor="e")

        popup.after(30000, lambda: popup.winfo_exists() and popup.destroy())

    def show_manual_notification(self, title: str = "Тест уведомления", message: str = "Проверка уведомлений.") -> None:
        self._show_notification(title, message)

    def test_notification(self) -> None:
        self.show_manual_notification("Тест уведомления", "Если вы видите это сообщение, уведомления работают.")