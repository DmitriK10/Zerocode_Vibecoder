"""
report_generator.py
Приложение на tkinter для генерации структурированных отчётов
с метриками и детализацией по дням в Google Таблицу.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import random
from datetime import datetime, timedelta
import os

from dotenv import load_dotenv
from google_sheets import CredentialsProvider, SheetsClient

load_dotenv()

CREDENTIALS_PATH = os.getenv('PATH_CREDENTIALS', 'credentials.json')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', '')

if not SPREADSHEET_ID:
    raise ValueError("Не задан SPREADSHEET_ID в .env файле")


class ReportGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор отчётов")
        self.root.geometry("700x550")

        try:
            provider = CredentialsProvider(CREDENTIALS_PATH)
            self.sheets = SheetsClient(provider, SPREADSHEET_ID)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось инициализировать Google Sheets: {e}")
            self.root.destroy()
            return

        self.date_start_var = tk.StringVar(value=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        self.date_end_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.report_types = ['Ежемесячный', 'Квартальный', 'Годовой', 'Произвольный']
        self.report_type_var = tk.StringVar(value=self.report_types[0])
        self.departments = ['Продажи', 'Маркетинг', 'Разработка', 'Администрация', 'Финансы']
        self.department_var = tk.StringVar(value=self.departments[0])
        self.responsible_var = tk.StringVar(value="Иванов И.И.")
        self.comment_var = tk.StringVar(value="")

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        row = 0
        ttk.Label(main_frame, text="Дата начала (YYYY-MM-DD):").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.date_start_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1

        ttk.Label(main_frame, text="Дата окончания (YYYY-MM-DD):").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.date_end_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1

        ttk.Label(main_frame, text="Тип отчёта:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Combobox(main_frame, textvariable=self.report_type_var, values=self.report_types,
                     state="readonly", width=18).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1

        ttk.Label(main_frame, text="Отдел:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Combobox(main_frame, textvariable=self.department_var, values=self.departments,
                     state="readonly", width=18).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1

        ttk.Label(main_frame, text="Ответственное лицо:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.responsible_var, width=30).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1

        ttk.Label(main_frame, text="Комментарий:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.comment_var, width=40).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1

        ttk.Button(main_frame, text="Сгенерировать отчёт", command=self.generate_report).grid(
            row=row, column=0, columnspan=2, pady=20
        )

        self.status_var = tk.StringVar(value="Готов к генерации отчёта")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)

    def generate_report(self):
        date_start = self.date_start_var.get().strip()
        date_end = self.date_end_var.get().strip()
        report_type = self.report_type_var.get()
        department = self.department_var.get()
        responsible = self.responsible_var.get().strip()
        comment = self.comment_var.get().strip()

        try:
            start_dt = datetime.strptime(date_start, "%Y-%m-%d")
            end_dt = datetime.strptime(date_end, "%Y-%m-%d")
            if start_dt > end_dt:
                messagebox.showerror("Ошибка", "Дата начала не может быть позже даты окончания")
                return
        except ValueError:
            messagebox.showerror("Ошибка", "Даты должны быть в формате YYYY-MM-DD")
            return

        sheet_name = f"Отчёт {report_type} {date_start} – {date_end}"
        if len(sheet_name) > 100:
            sheet_name = sheet_name[:100]

        self.status_var.set("Генерация данных...")
        self.root.update()

        # ------------------ Генерация данных ------------------
        total_revenue = round(random.uniform(500000, 2000000), 2)
        num_clients = random.randint(50, 200)
        conversion_rate = round(random.uniform(5.0, 25.0), 1)
        avg_check = round(total_revenue / num_clients, 2) if num_clients > 0 else 0
        num_deals = random.randint(30, 150)
        returns = round(random.uniform(0.5, 5.0), 1)
        new_clients = random.randint(10, 40)
        repeat_purchases = random.randint(20, 80)

        days_diff = (end_dt - start_dt).days + 1
        daily_data = []
        daily_revenue_sum = 0
        for i in range(days_diff):
            current_date = start_dt + timedelta(days=i)
            if i == days_diff - 1:
                day_revenue = round(total_revenue - daily_revenue_sum, 2)
            else:
                day_revenue = round(random.uniform(1000, max(total_revenue * 0.15, 1000)), 2)
                daily_revenue_sum += day_revenue
            if i == days_diff - 1:
                day_revenue = round(total_revenue - daily_revenue_sum + day_revenue, 2)
            day_clients = random.randint(1, max(3, int(num_clients / days_diff * 2)))
            day_deals = random.randint(1, max(2, int(num_deals / days_diff * 2)))
            daily_data.append({
                'date': current_date.strftime("%Y-%m-%d"),
                'revenue': day_revenue,
                'clients': day_clients,
                'deals': day_deals
            })
        total_daily_revenue = sum(d['revenue'] for d in daily_data)
        if abs(total_daily_revenue - total_revenue) > 0.01:
            last_day = daily_data[-1]
            last_day['revenue'] += round(total_revenue - total_daily_revenue, 2)
            daily_data[-1] = last_day

        # ------------------ Формирование строк отчёта ------------------
        rows = []
        rows.append(["ОТЧЁТ ПО ПРОДАЖАМ", "", "", "", ""])

        # Метаданные – комментарий добавляем всегда
        rows.append([f"Период: {date_start} – {date_end}", "", "", "", ""])
        rows.append([f"Отдел: {department}", "", "", "", ""])
        rows.append([f"Ответственное лицо: {responsible}", "", "", "", ""])
        if comment:
            rows.append([f"Комментарий: {comment}", "", "", "", ""])
        else:
            rows.append([f"Комментарий:                ", "", "", "", ""])
        rows.append([f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}", "", "", "", ""])

        rows.append([])  # пустая строка-разделитель

        rows.append(["ОСНОВНЫЕ МЕТРИКИ", "", "", "", ""])
        rows.append(["Показатель", "Значение", "Изменение, %", "", ""])
        metrics = [
            ("Выручка", f"{total_revenue:,.2f} руб.", f"{random.uniform(-5, 15):.1f}%"),
            ("Количество клиентов", num_clients, f"{random.uniform(-3, 10):.1f}%"),
            ("Конверсия", f"{conversion_rate}%", f"{random.uniform(-2, 5):.1f}%"),
            ("Средний чек", f"{avg_check:,.2f} руб.", f"{random.uniform(-4, 8):.1f}%"),
            ("Количество сделок", num_deals, f"{random.uniform(-2, 12):.1f}%"),
            ("Возвраты", f"{returns}%", f"{random.uniform(-1, 3):.1f}%"),
            ("Новые клиенты", new_clients, f"{random.uniform(0, 15):.1f}%"),
            ("Повторные покупки", repeat_purchases, f"{random.uniform(0, 20):.1f}%")
        ]
        for metric in metrics:
            rows.append(list(metric) + ["", ""])
        rows.append([])

        rows.append(["ДЕТАЛИЗАЦИЯ ПО ДНЯМ", "", "", "", ""])
        rows.append(["Дата", "Выручка, руб", "Клиенты", "Сделки", ""])
        for day in daily_data:
            rows.append([day['date'], f"{day['revenue']:,.2f}", day['clients'], day['deals'], ""])
        total_clients = sum(d['clients'] for d in daily_data)
        total_deals = sum(d['deals'] for d in daily_data)
        rows.append(["ИТОГО:", f"{total_revenue:,.2f}", total_clients, total_deals, ""])

        # Индексы для форматирования (строки 1-based)
        meta_end = 6
        metrics_title_row = 8
        metrics_header_row = 9
        metrics_data_end = metrics_header_row + len(metrics)
        empty_after_metrics = metrics_data_end + 1
        daily_title_row = empty_after_metrics + 1
        daily_header_row = daily_title_row + 1
        daily_data_start = daily_header_row + 1
        daily_data_end = daily_data_start + len(daily_data) - 1
        daily_total_row = daily_data_end + 1

        try:
            self.sheets.add_sheet(sheet_name)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать лист: {e}")
            self.status_var.set("Ошибка")
            return

        try:
            self.sheets.write_range(f"'{sheet_name}'!A1", rows, value_input_option='USER_ENTERED')
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось записать данные: {e}")
            self.status_var.set("Ошибка")
            return

        try:
            self.format_report(
                sheet_name,
                header_row=1,
                meta_end=meta_end,
                metrics_title_row=metrics_title_row,
                metrics_header_row=metrics_header_row,
                metrics_data_end=metrics_data_end,
                daily_title_row=daily_title_row,
                daily_header_row=daily_header_row,
                daily_data_start=daily_data_start,
                daily_data_end=daily_data_end,
                daily_total_row=daily_total_row
            )
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось применить форматирование: {e}")
            self.status_var.set("Ошибка")
            return

        self.status_var.set(f"Отчёт '{sheet_name}' успешно создан!")
        messagebox.showinfo("Успех", f"Отчёт '{sheet_name}' записан в таблицу.")

    def format_report(self, sheet_name, header_row, meta_end, metrics_title_row, metrics_header_row,
                      metrics_data_end, daily_title_row, daily_header_row, daily_data_start,
                      daily_data_end, daily_total_row):
        # Заголовок
        self.sheets.merge_cells(sheet_name, start_row=header_row, end_row=header_row, start_col=1, end_col=5)
        self.sheets.set_cell_format(
            sheet_name,
            start_row=header_row, end_row=header_row,
            start_col=1, end_col=5,
            format_dict={
                'textFormat': {'bold': True, 'fontSize': 14},
                'horizontalAlignment': 'CENTER',
                'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.6}
            }
        )

        # Метаданные
        if meta_end >= 2:
            self.sheets.set_cell_format(
                sheet_name,
                start_row=2, end_row=meta_end,
                start_col=1, end_col=5,
                format_dict={
                    'textFormat': {'bold': True},
                    'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
                }
            )

        # Заголовок "Основные метрики"
        self.sheets.merge_cells(sheet_name, start_row=metrics_title_row, end_row=metrics_title_row, start_col=1, end_col=5)
        self.sheets.set_cell_format(
            sheet_name,
            start_row=metrics_title_row, end_row=metrics_title_row,
            start_col=1, end_col=5,
            format_dict={
                'textFormat': {'bold': True, 'fontSize': 12},
                'horizontalAlignment': 'CENTER',
                'backgroundColor': {'red': 0.7, 'green': 0.8, 'blue': 0.9}
            }
        )

        # Заголовки метрик
        self.sheets.set_cell_format(
            sheet_name,
            start_row=metrics_header_row, end_row=metrics_header_row,
            start_col=1, end_col=3,
            format_dict={
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}
            }
        )

        # Данные метрик
        self.sheets.set_cell_format(
            sheet_name,
            start_row=metrics_header_row + 1, end_row=metrics_data_end,
            start_col=1, end_col=3,
            format_dict={
                'backgroundColor': {'red': 0.98, 'green': 0.98, 'blue': 0.98}
            }
        )

        # Заголовок "Детализация по дням"
        self.sheets.merge_cells(sheet_name, start_row=daily_title_row, end_row=daily_title_row, start_col=1, end_col=4)
        self.sheets.set_cell_format(
            sheet_name,
            start_row=daily_title_row, end_row=daily_title_row,
            start_col=1, end_col=4,
            format_dict={
                'textFormat': {'bold': True, 'fontSize': 12},
                'horizontalAlignment': 'CENTER',
                'backgroundColor': {'red': 0.7, 'green': 0.8, 'blue': 0.9}
            }
        )

        # Заголовки детализации
        self.sheets.set_cell_format(
            sheet_name,
            start_row=daily_header_row, end_row=daily_header_row,
            start_col=1, end_col=4,
            format_dict={
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}
            }
        )

        # Данные детализации
        self.sheets.set_cell_format(
            sheet_name,
            start_row=daily_header_row + 1, end_row=daily_data_end,
            start_col=1, end_col=4,
            format_dict={
                'backgroundColor': {'red': 0.98, 'green': 0.98, 'blue': 0.98}
            }
        )

        # Итоговая строка
        self.sheets.set_cell_format(
            sheet_name,
            start_row=daily_total_row, end_row=daily_total_row,
            start_col=1, end_col=4,
            format_dict={
                'textFormat': {'bold': True, 'fontSize': 11},
                'backgroundColor': {'red': 0.8, 'green': 0.9, 'blue': 0.8}
            }
        )

        # Ширина столбцов
        self.sheets.set_column_width(sheet_name, 1, 180)
        self.sheets.set_column_width(sheet_name, 2, 150)
        self.sheets.set_column_width(sheet_name, 3, 120)
        self.sheets.set_column_width(sheet_name, 4, 120)


if __name__ == "__main__":
    root = tk.Tk()
    app = ReportGeneratorApp(root)
    root.mainloop()