import csv
import os
from typing import List, Tuple
from config import CSV_EXPORT_DIR

def generate_tasks_csv(tasks: List[Tuple[int, str, int, str, str, str]]) -> str:
    """
    Создаёт CSV-файл со списком задач, включая статус и категорию.
    Возвращает полный путь к созданному файлу.
    """
    csv_path = os.path.join(CSV_EXPORT_DIR, "tasks_export.csv")
    
    # utf-8-sig для корректного отображения кириллицы в Excel
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["ID", "Текст задачи", "ID пользователя", "Дата создания", "Статус", "Категория"])
        for row in tasks:
            # row: (id, text, user_id, created_at, status, category)
            writer.writerow(row)
    
    return csv_path