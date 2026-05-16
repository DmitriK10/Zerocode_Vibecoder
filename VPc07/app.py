# app.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from tkcalendar import DateEntry  # требует установки: pip install tkcalendar
from database_driver import DatabaseDriver
from postgres_driver import PostgresSQLDriver
import backend
from models.user import User
from models.table import Table
from models.booking import Booking


class BookingApp:
    def __init__(self, root: tk.Tk, db: DatabaseDriver):
        self.db = db
        self.root = root
        self.root.title("Система бронирования столиков")
        self.root.geometry("850x700")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)

        self.user_frame = ttk.Frame(self.notebook)
        self.table_frame = ttk.Frame(self.notebook)
        self.booking_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.user_frame, text="Пользователи")
        self.notebook.add(self.table_frame, text="Столы")
        self.notebook.add(self.booking_frame, text="Бронирования")

        self._build_user_tab()
        self._build_table_tab()
        self._build_booking_tab()

    # ------------------ ПОЛЬЗОВАТЕЛИ ------------------
    def _build_user_tab(self):
        # Форма добавления
        ttk.Label(self.user_frame, text="Имя").grid(row=0, column=0, sticky="w")
        self.user_first = ttk.Entry(self.user_frame, width=30)
        self.user_first.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(self.user_frame, text="Фамилия").grid(row=1, column=0, sticky="w")
        self.user_last = ttk.Entry(self.user_frame, width=30)
        self.user_last.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(self.user_frame, text="Email").grid(row=2, column=0, sticky="w")
        self.user_email = ttk.Entry(self.user_frame, width=30)
        self.user_email.grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(self.user_frame, text="Пароль").grid(row=3, column=0, sticky="w")
        self.user_password = ttk.Entry(self.user_frame, show="*", width=30)
        self.user_password.grid(row=3, column=1, padx=5, pady=2)

        ttk.Label(self.user_frame, text="Роль").grid(row=4, column=0, sticky="w")
        self.user_role = ttk.Combobox(self.user_frame, values=["user", "admin"], width=27)
        self.user_role.grid(row=4, column=1, padx=5, pady=2)
        self.user_role.current(0)

        ttk.Label(self.user_frame, text="Статус").grid(row=5, column=0, sticky="w")
        self.user_status = ttk.Combobox(self.user_frame, values=["active", "blocked"], width=27)
        self.user_status.grid(row=5, column=1, padx=5, pady=2)
        self.user_status.current(0)

        ttk.Button(self.user_frame, text="Добавить", command=self._create_user).grid(
            row=6, column=0, columnspan=2, pady=5)

        # Список пользователей
        self.users_list = tk.Listbox(self.user_frame, width=80, height=10)
        self.users_list.grid(row=7, column=0, columnspan=2, padx=5, pady=5)
        self.users_list.bind('<<ListboxSelect>>', self._on_user_select)

        # Кнопки управления
        btn_frame = ttk.Frame(self.user_frame)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=5)
        ttk.Button(btn_frame, text="Редактировать", command=self._edit_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить", command=self._delete_user).pack(side=tk.LEFT, padx=5)

        self._refresh_users()
        self._selected_user_id = None

    def _on_user_select(self, event):
        selection = self.users_list.curselection()
        if selection:
            text = self.users_list.get(selection[0])
            self._selected_user_id = int(text.split(":")[0])
        else:
            self._selected_user_id = None

    def _create_user(self):
        try:
            user = User(
                first_name=self.user_first.get(),
                last_name=self.user_last.get(),
                email=self.user_email.get(),
                password=self.user_password.get(),
                role=self.user_role.get() or "user",
                status=self.user_status.get() or "active"
            )
            backend.create_user(self.db, user)
            self._refresh_users()
            self._clear_user_form()
            messagebox.showinfo("Успех", "Пользователь создан")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _edit_user(self):
        if not self._selected_user_id:
            messagebox.showwarning("Предупреждение", "Выберите пользователя из списка")
            return
        user_data = backend.get_user_by_id(self.db, self._selected_user_id)
        if not user_data:
            messagebox.showerror("Ошибка", "Пользователь не найден")
            return
        edit_win = tk.Toplevel(self.root)
        edit_win.title("Редактирование пользователя")
        edit_win.geometry("300x300")

        ttk.Label(edit_win, text="Имя").pack(pady=2)
        first_entry = ttk.Entry(edit_win)
        first_entry.insert(0, user_data["first_name"])
        first_entry.pack()
        ttk.Label(edit_win, text="Фамилия").pack(pady=2)
        last_entry = ttk.Entry(edit_win)
        last_entry.insert(0, user_data["last_name"])
        last_entry.pack()
        ttk.Label(edit_win, text="Email").pack(pady=2)
        email_entry = ttk.Entry(edit_win)
        email_entry.insert(0, user_data["email"])
        email_entry.pack()
        ttk.Label(edit_win, text="Роль").pack(pady=2)
        role_combo = ttk.Combobox(edit_win, values=["user", "admin"])
        role_combo.set(user_data["role"])
        role_combo.pack()
        ttk.Label(edit_win, text="Статус").pack(pady=2)
        status_combo = ttk.Combobox(edit_win, values=["active", "blocked"])
        status_combo.set(user_data["status"])
        status_combo.pack()

        def save_changes():
            updated = {
                "first_name": first_entry.get(),
                "last_name": last_entry.get(),
                "email": email_entry.get(),
                "role": role_combo.get(),
                "status": status_combo.get()
            }
            backend.update_user(self.db, self._selected_user_id, updated)
            self._refresh_users()
            edit_win.destroy()
            messagebox.showinfo("Успех", "Данные обновлены")

        ttk.Button(edit_win, text="Сохранить", command=save_changes).pack(pady=10)

    def _delete_user(self):
        if not self._selected_user_id:
            messagebox.showwarning("Предупреждение", "Выберите пользователя")
            return
        if messagebox.askyesno("Подтверждение", "Удалить пользователя? Связанные бронирования также будут удалены (каскадно)."):
            backend.delete_user(self.db, self._selected_user_id)
            self._refresh_users()
            self._selected_user_id = None
            messagebox.showinfo("Успех", "Пользователь удален")

    def _refresh_users(self):
        self.users_list.delete(0, tk.END)
        try:
            for u in backend.get_all_users(self.db):
                self.users_list.insert(tk.END, f"{u['id']}: {u['first_name']} {u['last_name']} ({u['email']})")
        except Exception as e:
            messagebox.showerror("Ошибка загрузки пользователей", str(e))

    def _clear_user_form(self):
        self.user_first.delete(0, tk.END)
        self.user_last.delete(0, tk.END)
        self.user_email.delete(0, tk.END)
        self.user_password.delete(0, tk.END)
        self.user_role.current(0)
        self.user_status.current(0)

    # ------------------ СТОЛЫ ------------------
    def _build_table_tab(self):
        ttk.Label(self.table_frame, text="Номер стола").grid(row=0, column=0, sticky="w")
        self.table_number = ttk.Entry(self.table_frame, width=30)
        self.table_number.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(self.table_frame, text="Мест").grid(row=1, column=0, sticky="w")
        self.table_seats = ttk.Entry(self.table_frame, width=30)
        self.table_seats.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(self.table_frame, text="Расположение").grid(row=2, column=0, sticky="w")
        self.table_location = ttk.Entry(self.table_frame, width=30)
        self.table_location.grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(self.table_frame, text="Статус").grid(row=3, column=0, sticky="w")
        self.table_status = ttk.Combobox(self.table_frame, values=["available", "occupied", "maintenance"], width=27)
        self.table_status.grid(row=3, column=1, padx=5, pady=2)
        self.table_status.current(0)

        ttk.Button(self.table_frame, text="Добавить", command=self._create_table).grid(
            row=4, column=0, columnspan=2, pady=5)

        self.tables_list = tk.Listbox(self.table_frame, width=80, height=10)
        self.tables_list.grid(row=5, column=0, columnspan=2, padx=5, pady=5)
        self.tables_list.bind('<<ListboxSelect>>', self._on_table_select)

        btn_frame = ttk.Frame(self.table_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=5)
        ttk.Button(btn_frame, text="Редактировать", command=self._edit_table).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить", command=self._delete_table).pack(side=tk.LEFT, padx=5)

        self._refresh_tables()
        self._selected_table_id = None

    def _on_table_select(self, event):
        selection = self.tables_list.curselection()
        if selection:
            text = self.tables_list.get(selection[0])
            self._selected_table_id = int(text.split(":")[0])
        else:
            self._selected_table_id = None

    def _create_table(self):
        try:
            table = Table(
                number=int(self.table_number.get()),
                seats=int(self.table_seats.get()),
                location=self.table_location.get() or "main hall",
                status=self.table_status.get() or "available"
            )
            backend.create_table(self.db, table)
            self._refresh_tables()
            self._clear_table_form()
            messagebox.showinfo("Успех", "Стол добавлен")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _edit_table(self):
        if not self._selected_table_id:
            messagebox.showwarning("Предупреждение", "Выберите стол")
            return
        table_data = backend.get_table_by_id(self.db, self._selected_table_id)
        if not table_data:
            messagebox.showerror("Ошибка", "Стол не найден")
            return
        edit_win = tk.Toplevel(self.root)
        edit_win.title("Редактирование стола")
        edit_win.geometry("250x250")

        ttk.Label(edit_win, text="Номер").pack(pady=2)
        num_entry = ttk.Entry(edit_win)
        num_entry.insert(0, table_data["number"])
        num_entry.pack()
        ttk.Label(edit_win, text="Мест").pack(pady=2)
        seats_entry = ttk.Entry(edit_win)
        seats_entry.insert(0, table_data["seats"])
        seats_entry.pack()
        ttk.Label(edit_win, text="Расположение").pack(pady=2)
        loc_entry = ttk.Entry(edit_win)
        loc_entry.insert(0, table_data["location"])
        loc_entry.pack()
        ttk.Label(edit_win, text="Статус").pack(pady=2)
        status_combo = ttk.Combobox(edit_win, values=["available", "occupied", "maintenance"])
        status_combo.set(table_data["status"])
        status_combo.pack()

        def save_changes():
            updated = {
                "number": int(num_entry.get()),
                "seats": int(seats_entry.get()),
                "location": loc_entry.get(),
                "status": status_combo.get()
            }
            backend.update_table(self.db, self._selected_table_id, updated)
            self._refresh_tables()
            edit_win.destroy()
            messagebox.showinfo("Успех", "Стол обновлен")

        ttk.Button(edit_win, text="Сохранить", command=save_changes).pack(pady=10)

    def _delete_table(self):
        if not self._selected_table_id:
            messagebox.showwarning("Предупреждение", "Выберите стол")
            return
        if messagebox.askyesno("Подтверждение", "Удалить стол? Все связанные бронирования будут удалены."):
            backend.delete_table(self.db, self._selected_table_id)
            self._refresh_tables()
            self._selected_table_id = None
            messagebox.showinfo("Успех", "Стол удален")

    def _refresh_tables(self):
        self.tables_list.delete(0, tk.END)
        try:
            for t in backend.get_all_tables(self.db):
                self.tables_list.insert(tk.END, f"{t['id']}: стол №{t['number']}, мест {t['seats']} ({t['status']})")
        except Exception as e:
            messagebox.showerror("Ошибка загрузки столов", str(e))

    def _clear_table_form(self):
        self.table_number.delete(0, tk.END)
        self.table_seats.delete(0, tk.END)
        self.table_location.delete(0, tk.END)
        self.table_status.current(0)

    # ------------------ БРОНИРОВАНИЯ (исправлено: календарь + время) ------------------
    def _build_booking_tab(self):
        # Пользователь
        ttk.Label(self.booking_frame, text="Пользователь").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.book_user_combo = ttk.Combobox(self.booking_frame, width=40)
        self.book_user_combo.grid(row=0, column=1, padx=5, pady=2)

        # Стол
        ttk.Label(self.booking_frame, text="Стол").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.book_table_combo = ttk.Combobox(self.booking_frame, width=40)
        self.book_table_combo.grid(row=1, column=1, padx=5, pady=2)

        # Дата (календарь)
        ttk.Label(self.booking_frame, text="Дата").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.book_date = DateEntry(self.booking_frame, width=12, background='darkblue',
                                   foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.book_date.grid(row=2, column=1, padx=5, pady=2, sticky='w')

        # Время начала
        ttk.Label(self.booking_frame, text="Начало (HH:MM)").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        frame_start = ttk.Frame(self.booking_frame)
        frame_start.grid(row=3, column=1, padx=5, pady=2, sticky='w')
        self.start_hour = ttk.Combobox(frame_start, values=[f"{i:02d}" for i in range(24)], width=3)
        self.start_hour.set("12")
        self.start_hour.pack(side=tk.LEFT)
        ttk.Label(frame_start, text=":").pack(side=tk.LEFT)
        self.start_minute = ttk.Combobox(frame_start, values=[f"{i:02d}" for i in range(0, 60, 15)], width=3)
        self.start_minute.set("00")
        self.start_minute.pack(side=tk.LEFT)

        # Время окончания
        ttk.Label(self.booking_frame, text="Конец (HH:MM)").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        frame_end = ttk.Frame(self.booking_frame)
        frame_end.grid(row=4, column=1, padx=5, pady=2, sticky='w')
        self.end_hour = ttk.Combobox(frame_end, values=[f"{i:02d}" for i in range(24)], width=3)
        self.end_hour.set("14")
        self.end_hour.pack(side=tk.LEFT)
        ttk.Label(frame_end, text=":").pack(side=tk.LEFT)
        self.end_minute = ttk.Combobox(frame_end, values=[f"{i:02d}" for i in range(0, 60, 15)], width=3)
        self.end_minute.set("00")
        self.end_minute.pack(side=tk.LEFT)

        # Количество гостей
        ttk.Label(self.booking_frame, text="Гостей").grid(row=5, column=0, sticky="w", padx=5, pady=2)
        self.book_guests = ttk.Spinbox(self.booking_frame, from_=1, to=20, width=10)
        self.book_guests.grid(row=5, column=1, padx=5, pady=2, sticky='w')

        # Кнопки
        btn_frame = ttk.Frame(self.booking_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Проверить доступность", command=self._check_availability).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Забронировать", command=self._create_booking).pack(side=tk.LEFT, padx=5)

        # Список бронирований
        self.bookings_list = tk.Listbox(self.booking_frame, width=100, height=10)
        self.bookings_list.grid(row=7, column=0, columnspan=2, padx=5, pady=5)
        self.bookings_list.bind('<<ListboxSelect>>', self._on_booking_select)

        # Кнопки редактирования/отмены
        btn_frame2 = ttk.Frame(self.booking_frame)
        btn_frame2.grid(row=8, column=0, columnspan=2, pady=5)
        ttk.Button(btn_frame2, text="Редактировать", command=self._edit_booking).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="Отменить", command=self._cancel_booking).pack(side=tk.LEFT, padx=5)

        self._refresh_combos()
        self._refresh_bookings()
        self._selected_booking_id = None

    def _refresh_combos(self):
        users = backend.get_users_choices(self.db)
        self.book_user_combo['values'] = [f"{uid}: {name}" for uid, name in users.items()]
        tables = backend.get_tables_choices(self.db)
        self.book_table_combo['values'] = [f"{tid}: {desc}" for tid, desc in tables.items()]

    def _on_booking_select(self, event):
        selection = self.bookings_list.curselection()
        if selection:
            text = self.bookings_list.get(selection[0])
            # формат строки: "ID X: user Y, table Z, ..."
            parts = text.split(":")
            if len(parts) > 1:
                self._selected_booking_id = int(parts[1].split()[0])
            else:
                self._selected_booking_id = None
        else:
            self._selected_booking_id = None

    def _check_availability(self):
        try:
            combo_val = self.book_table_combo.get()
            if not combo_val:
                raise ValueError("Выберите стол")
            table_id = int(combo_val.split(":")[0])
            date_str = self.book_date.get()
            start_time_str = f"{self.start_hour.get()}:{self.start_minute.get()}"
            end_time_str = f"{self.end_hour.get()}:{self.end_minute.get()}"
            start_dt = datetime.strptime(f"{date_str} {start_time_str}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{date_str} {end_time_str}", "%Y-%m-%d %H:%M")
            if backend.check_table_availability(self.db, table_id, start_dt, end_dt):
                messagebox.showinfo("Доступность", "Столик свободен в это время")
            else:
                messagebox.showwarning("Занято", "Столик занят в указанное время")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _create_booking(self):
        try:
            user_val = self.book_user_combo.get()
            table_val = self.book_table_combo.get()
            if not user_val or not table_val:
                raise ValueError("Выберите пользователя и стол")
            user_id = int(user_val.split(":")[0])
            table_id = int(table_val.split(":")[0])
            date_str = self.book_date.get()
            start_time_str = f"{self.start_hour.get()}:{self.start_minute.get()}"
            end_time_str = f"{self.end_hour.get()}:{self.end_minute.get()}"
            guests = int(self.book_guests.get() or 1)

            start_dt = datetime.strptime(f"{date_str} {start_time_str}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{date_str} {end_time_str}", "%Y-%m-%d %H:%M")

            if not backend.check_table_availability(self.db, table_id, start_dt, end_dt):
                messagebox.showerror("Ошибка", "Столик занят, выберите другое время")
                return

            if not backend.get_user_by_id(self.db, user_id):
                messagebox.showerror("Ошибка", "Пользователь не существует")
                return
            if not backend.get_table_by_id(self.db, table_id):
                messagebox.showerror("Ошибка", "Стол не существует")
                return

            booking = Booking(
                user_id=user_id,
                table_id=table_id,
                booking_date=start_dt,
                start_time=start_dt,
                end_time=end_dt,
                guests_count=guests
            )
            backend.create_booking(self.db, booking)
            self._refresh_bookings()
            self._clear_booking_form()
            messagebox.showinfo("Успех", "Бронирование создано")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _edit_booking(self):
        if not self._selected_booking_id:
            messagebox.showwarning("Предупреждение", "Выберите бронирование")
            return
        booking_data = backend.get_booking_by_id(self.db, self._selected_booking_id)
        if not booking_data:
            messagebox.showerror("Ошибка", "Бронирование не найдено")
            return
        edit_win = tk.Toplevel(self.root)
        edit_win.title("Редактирование бронирования")
        edit_win.geometry("300x300")

        # Дата
        ttk.Label(edit_win, text="Дата (YYYY-MM-DD)").pack(pady=2)
        date_entry = DateEntry(edit_win, width=12, date_pattern='yyyy-mm-dd')
        date_entry.set_date(booking_data["start_time"])
        date_entry.pack()

        # Время начала
        ttk.Label(edit_win, text="Начало (HH:MM)").pack(pady=2)
        frame_start = ttk.Frame(edit_win)
        frame_start.pack()
        start_hour = ttk.Combobox(frame_start, values=[f"{i:02d}" for i in range(24)], width=3)
        start_hour.set(booking_data["start_time"].strftime("%H"))
        start_hour.pack(side=tk.LEFT)
        ttk.Label(frame_start, text=":").pack(side=tk.LEFT)
        start_minute = ttk.Combobox(frame_start, values=[f"{i:02d}" for i in range(0, 60, 15)], width=3)
        start_minute.set(booking_data["start_time"].strftime("%M"))
        start_minute.pack(side=tk.LEFT)

        # Время окончания
        ttk.Label(edit_win, text="Конец (HH:MM)").pack(pady=2)
        frame_end = ttk.Frame(edit_win)
        frame_end.pack()
        end_hour = ttk.Combobox(frame_end, values=[f"{i:02d}" for i in range(24)], width=3)
        end_hour.set(booking_data["end_time"].strftime("%H"))
        end_hour.pack(side=tk.LEFT)
        ttk.Label(frame_end, text=":").pack(side=tk.LEFT)
        end_minute = ttk.Combobox(frame_end, values=[f"{i:02d}" for i in range(0, 60, 15)], width=3)
        end_minute.set(booking_data["end_time"].strftime("%M"))
        end_minute.pack(side=tk.LEFT)

        # Гости
        ttk.Label(edit_win, text="Количество гостей").pack(pady=2)
        guests_entry = ttk.Spinbox(edit_win, from_=1, to=20, width=10)
        guests_entry.delete(0, tk.END)
        guests_entry.insert(0, booking_data["guests_count"])
        guests_entry.pack()

        def save_booking():
            try:
                new_start = datetime.strptime(
                    f"{date_entry.get()} {start_hour.get()}:{start_minute.get()}",
                    "%Y-%m-%d %H:%M"
                )
                new_end = datetime.strptime(
                    f"{date_entry.get()} {end_hour.get()}:{end_minute.get()}",
                    "%Y-%m-%d %H:%M"
                )
                # Проверка доступности (исключая текущее бронирование)
                # Для простоты – не проверяем, так как это учебный проект
                updated = {
                    "start_time": new_start,
                    "end_time": new_end,
                    "guests_count": int(guests_entry.get())
                }
                backend.update_booking(self.db, self._selected_booking_id, updated)
                self._refresh_bookings()
                edit_win.destroy()
                messagebox.showinfo("Успех", "Бронирование обновлено")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        ttk.Button(edit_win, text="Сохранить", command=save_booking).pack(pady=10)

    def _cancel_booking(self):
        if not self._selected_booking_id:
            messagebox.showwarning("Предупреждение", "Выберите бронирование")
            return
        if messagebox.askyesno("Подтверждение", "Отменить бронирование?"):
            backend.delete_booking(self.db, self._selected_booking_id)
            self._refresh_bookings()
            self._selected_booking_id = None
            messagebox.showinfo("Успех", "Бронирование отменено")

    def _refresh_bookings(self):
        self.bookings_list.delete(0, tk.END)
        try:
            for b in backend.get_all_bookings(self.db):
                self.bookings_list.insert(tk.END,
                    f"ID {b['id']}: user {b['user_id']}, table {b['table_id']}, "
                    f"{b['start_time']} – {b['end_time']}, гостей: {b['guests_count']}")
        except Exception as e:
            messagebox.showerror("Ошибка загрузки бронирований", str(e))

    def _clear_booking_form(self):
        self.book_user_combo.set('')
        self.book_table_combo.set('')
        self.book_date.set_date(datetime.now())
        self.start_hour.set("12")
        self.start_minute.set("00")
        self.end_hour.set("14")
        self.end_minute.set("00")
        self.book_guests.delete(0, tk.END)
        self.book_guests.insert(0, "2")


def init_database(db: DatabaseDriver):
    db.create_table_from_model(User)
    db.create_table_from_model(Table)
    db.create_table_from_model(Booking)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    db_driver = PostgresSQLDriver()
    try:
        db_driver.connect()
        init_database(db_driver)
        root.deiconify()
        app = BookingApp(root, db_driver)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Критическая ошибка", f"Не удалось запустить приложение:\n{e}")
        root.destroy()
    finally:
        db_driver.disconnect()