#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDF Generator – CLI инструмент для создания PDF из HTML-шаблонов и данных (CSV/JSON).
Использует WeasyPrint.
"""

import os
import sys
import json
import csv
import subprocess
from datetime import datetime
from pathlib import Path

# Попытка импорта pandas, если не установлен – используем встроенный csv
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from weasyprint import HTML, CSS

# ------------------------------------------------------------
# Константы и пути
# ------------------------------------------------------------
BASE_DIR = Path(__file__).parent.absolute()
DATA_DIR = BASE_DIR / 'data'
TEMPLATES_DIR = BASE_DIR / 'templates'
OUTPUT_DIR = BASE_DIR / 'output'

# Базовый CSS для поддержки кириллицы и стилизации таблиц
BASE_CSS = CSS(string='''
    @page { size: A4; margin: 2cm; }
    body {
        font-family: 'DejaVu Sans', 'Roboto', 'Liberation Sans', sans-serif;
        font-size: 12pt;
        color: #333;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        word-wrap: break-word;
    }
    th, td {
        border: 1px solid #7f8c8d;
        padding: 8px 10px;
        text-align: left;
    }
    th {
        background-color: #ecf0f1;
    }
    .total {
        font-weight: bold;
        text-align: right;
        margin-top: 20px;
    }
    .footer {
        margin-top: 40px;
        font-size: 10pt;
        color: #95a5a6;
        text-align: center;
    }
''')

# ------------------------------------------------------------
# Вспомогательные функции
# ------------------------------------------------------------
def ensure_directories():
    """Создаёт необходимые папки, если их нет."""
    DATA_DIR.mkdir(exist_ok=True)
    TEMPLATES_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

def get_data_files():
    """Возвращает список путей ко всем CSV и JSON файлам в папке data."""
    files = []
    if DATA_DIR.exists():
        for ext in ('*.csv', '*.json'):
            files.extend(DATA_DIR.glob(ext))
    return sorted(files)

def get_template_files():
    """Возвращает список путей ко всем HTML файлам в папке templates."""
    if TEMPLATES_DIR.exists():
        return sorted(TEMPLATES_DIR.glob('*.html'))
    return []

def load_data(file_path):
    """Загружает данные из CSV или JSON файла. Возвращает список словарей."""
    ext = file_path.suffix.lower()
    if ext == '.csv':
        if PANDAS_AVAILABLE:
            df = pd.read_csv(file_path, encoding='utf-8')
            # Преобразуем DataFrame в список словарей
            return df.to_dict(orient='records')
        else:
            # Используем стандартный модуль csv
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
    elif ext == '.json':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Если данные – одиночный объект, оборачиваем в список
            if isinstance(data, dict):
                return [data]
            return data
    else:
        raise ValueError(f"Неподдерживаемый формат файла: {ext}")

def find_id_field(record):
    """
    Пытается найти поле, которое может служить идентификатором записи.
    Возвращает (field_name, value).
    """
    # Приоритетные имена полей
    candidates = ['invoice_id', 'order_id', 'product_id', 'id', 'sale_id', 'emp_id', 'expense_id', 'project_code']
    for cand in candidates:
        if cand in record:
            return cand, record[cand]
    # Если ничего не найдено – берём первый ключ
    first_key = next(iter(record))
    return first_key, record[first_key]

def render_html(template_path, record):
    """
    Заменяет плейсхолдеры {{ field }} в шаблоне значениями из record.
    Обрабатывает простые поля и (опционально) список items.
    Возвращает строку с готовым HTML.
    """
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # Простая подстановка {{ field }}
    for key, value in record.items():
        # Если значение – список (например, items в заказе), формируем таблицу
        if isinstance(value, list):
            # Создаём строку с таблицей позиций
            items_html = ''
            for item in value:
                if isinstance(item, dict):
                    # Предполагаем поля: name, qty, price
                    name = item.get('name', item.get('product', ''))
                    qty = item.get('qty', item.get('quantity', 1))
                    price = item.get('price', 0)
                    total = qty * price
                    items_html += f'<tr><td>{name}</td><td>{qty}</td><td>{price:.2f}</td><td>{total:.2f}</td></tr>'
            template = template.replace('{{ items }}', items_html)
            # Удалим блоки jinja для простоты (можно не удалять, если не используются)
            template = template.replace('{% for item in items %}', '').replace('{% endfor %}', '')
        else:
            # Для обычных полей
            template = template.replace(f'{{{{ {key} }}}}', str(value))
    return template

def generate_pdf(html_content, output_path):
    """Генерирует PDF из HTML-контента с использованием WeasyPrint."""
    # Создаём HTML-объект
    html = HTML(string=html_content, base_url=str(BASE_DIR))
    # Рендерим документ с нашими стилями
    document = html.render(stylesheets=[BASE_CSS])
    # Сохраняем PDF
    document.write_pdf(output_path)

def open_pdf(pdf_path):
    """Открывает PDF-файл в системной программе просмотра."""
    if sys.platform == 'win32':
        os.startfile(pdf_path)
    elif sys.platform == 'darwin':  # macOS
        subprocess.run(['open', pdf_path])
    else:  # Linux и др.
        subprocess.run(['xdg-open', pdf_path])

def print_menu(title, items):
    """Выводит пронумерованное меню."""
    print(f"\n{title}")
    for idx, item in enumerate(items, start=1):
        print(f"  {idx}. {item.name}")
    print("  0. Выход")

def choose_option(items, prompt):
    """Запрашивает у пользователя выбор номера из списка."""
    while True:
        try:
            choice = input(prompt).strip()
            if choice == '0':
                sys.exit(0)
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                return items[idx]
            else:
                print("Неверный номер. Попробуйте снова.")
        except ValueError:
            print("Введите число.")

# ------------------------------------------------------------
# Основная функция
# ------------------------------------------------------------
def main():
    ensure_directories()

    # Получаем списки файлов
    data_files = get_data_files()
    template_files = get_template_files()

    if not data_files:
        print("В папке data/ нет CSV или JSON файлов. Добавьте файлы и повторите запуск.")
        sys.exit(1)
    if not template_files:
        print("В папке templates/ нет HTML шаблонов.")
        sys.exit(1)

    # Выбор файла данных
    print_menu("Доступные файлы с данными:", data_files)
    selected_data_file = choose_option(data_files, "Выберите номер файла данных: ")

    # Выбор шаблона
    print_menu("Доступные HTML шаблоны:", template_files)
    selected_template = choose_option(template_files, "Выберите номер шаблона: ")

    # Загрузка данных
    try:
        records = load_data(selected_data_file)
        if not records:
            print("Файл данных пуст.")
            sys.exit(1)
    except Exception as e:
        print(f"Ошибка загрузки данных: {e}")
        sys.exit(1)

    # Определяем поле-идентификатор и выводим список записей
    print("\nДоступные записи:")
    ids = []
    for idx, rec in enumerate(records, start=1):
        id_field, id_value = find_id_field(rec)
        ids.append((id_field, id_value, rec))
        print(f"  {idx}. {id_value}")
    print("  0. Выход")

    # Выбор конкретной записи по номеру
    while True:
        try:
            choice = input("\nВыберите номер записи (или 0 для выхода): ").strip()
            if choice == '0':
                sys.exit(0)
            idx = int(choice) - 1
            if 0 <= idx < len(ids):
                selected_record = ids[idx][2]
                chosen_id = ids[idx][1]   # сохраняем идентификатор для имени файла
                break
            else:
                print("Неверный номер. Попробуйте снова.")
        except ValueError:
            print("Введите число.")

    # Генерация HTML
    try:
        html_content = render_html(selected_template, selected_record)
    except Exception as e:
        print(f"Ошибка при рендеринге шаблона: {e}")
        sys.exit(1)

    # Формирование имени выходного PDF
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_id = str(chosen_id).replace('/', '_').replace('\\', '_')
    output_pdf = OUTPUT_DIR / f"{selected_template.stem}_{safe_id}_{timestamp}.pdf"

    # Генерация PDF
    try:
        generate_pdf(html_content, output_pdf)
        print(f"\nPDF успешно создан: {output_pdf}")
    except Exception as e:
        print(f"Ошибка при создании PDF: {e}")
        sys.exit(1)

    # Открытие PDF
    try:
        open_pdf(output_pdf)
        print("PDF открыт в программе просмотра.")
    except Exception as e:
        print(f"Не удалось автоматически открыть PDF: {e}")

if __name__ == '__main__':
    main()