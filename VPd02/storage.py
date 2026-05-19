"""
Модуль для файлового кэширования данных курсов валют.
Обеспечивает сохранение, чтение и проверку возраста кэша.
"""

import json
import time
from pathlib import Path
from typing import Dict, Optional

# Определяем абсолютный путь к файлу кэша (лежит рядом со скриптом)
CACHE_DIR = Path(__file__).resolve().parent
CACHE_FILE_PATH = CACHE_DIR / "currency_rate.json"


def save_to_file(data: Dict, path: Path = CACHE_FILE_PATH) -> None:
    """
    Сохраняет словарь в JSON-файл с форматированием.

    Args:
        data (Dict): Данные для сохранения.
        path (Path): Полный путь к файлу (по умолчанию currency_rate.json).
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"[Кэш] Данные сохранены в {path}")


def read_from_file(path: Path = CACHE_FILE_PATH) -> Optional[Dict]:
    """
    Читает данные из JSON-файла.

    Args:
        path (Path): Полный путь к файлу.

    Returns:
        Optional[Dict]: Словарь с данными или None, если файл не существует
                        или повреждён.
    """
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"[Ошибка] Не удалось прочитать {path}: {e}")
        return None


def is_cache_fresh(path: Path = CACHE_FILE_PATH, max_age_hours: int = 24) -> bool:
    """
    Проверяет, не устарел ли кэш (по времени модификации файла).

    Args:
        path (Path): Полный путь к файлу кэша.
        max_age_hours (int): Максимальный допустимый возраст в часах.

    Returns:
        bool: True, если файл существует и его возраст меньше max_age_hours.
    """
    if not path.exists():
        return False
    # Получаем время последней модификации файла в секундах с эпохи
    mtime = path.stat().st_mtime
    age_seconds = time.time() - mtime
    return age_seconds < max_age_hours * 3600