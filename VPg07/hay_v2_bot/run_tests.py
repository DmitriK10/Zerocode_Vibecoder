#!/usr/bin/env python
"""
Скрипт для запуска всех тестов проекта "Персональный ассистент v2"

Запуск:
    python run_tests.py

Для запуска конкретного тестового файла:
    python -m unittest tests.test_pinecone_helpers

Для запуска с большей детализацией:
    python run_tests.py --verbose
"""

import sys
import os
import unittest
import argparse
from datetime import datetime

# Добавляем корень проекта в sys.path, чтобы импорты из tests/ работали
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Цветной вывод (опционально, для удобства)
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    # Заглушки, если colorama не установлен
    class Fore:
        RED = ''
        GREEN = ''
        YELLOW = ''
        BLUE = ''
        MAGENTA = ''
        CYAN = ''
        RESET = ''
    class Style:
        BRIGHT = ''
        DIM = ''
        NORMAL = ''


def print_header(text: str, color=Fore.CYAN if COLORS_AVAILABLE else ''):
    """Печатает заголовок с рамкой."""
    line = "=" * 60
    if COLORS_AVAILABLE:
        print(f"{color}{line}{Style.RESET_ALL}")
        print(f"{color}{text.center(60)}{Style.RESET_ALL}")
        print(f"{color}{line}{Style.RESET_ALL}")
    else:
        print(line)
        print(text.center(60))
        print(line)


def print_section(text: str, color=Fore.YELLOW if COLORS_AVAILABLE else ''):
    """Печатает подзаголовок."""
    if COLORS_AVAILABLE:
        print(f"{color}>>> {text}{Style.RESET_ALL}")
    else:
        print(f">>> {text}")


def main():
    parser = argparse.ArgumentParser(description="Запуск тестов проекта")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Показать подробный вывод (verbosity=2)"
    )
    parser.add_argument(
        "-t", "--test",
        type=str,
        help="Запустить конкретный тестовый файл (например, tests.test_pinecone_helpers)"
    )
    args = parser.parse_args()

    # Определяем уровень детализации
    verbosity = 2 if args.verbose else 2  # всегда 2 для детального вывода

    print_header("🧪 ЗАПУСК ТЕСТОВ ПРОЕКТА", Fore.MAGENTA if COLORS_AVAILABLE else '')
    print(f"📁 Директория проекта: {PROJECT_ROOT}")
    print(f"📅 Дата и время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Версия Python: {sys.version.split()[0]}")

    # Загрузка тестов
    if args.test:
        # Запуск конкретного тестового модуля
        print_section(f"Запуск конкретного теста: {args.test}", Fore.CYAN if COLORS_AVAILABLE else '')
        test_loader = unittest.TestLoader()
        try:
            suite = test_loader.loadTestsFromName(args.test)
        except (ImportError, AttributeError) as e:
            print(f"{Fore.RED if COLORS_AVAILABLE else ''}❌ Ошибка загрузки теста: {e}")
            sys.exit(1)
    else:
        # Загрузка всех тестов из папки tests/
        print_section("Обнаружение тестов в папке tests/...", Fore.CYAN if COLORS_AVAILABLE else '')
        test_loader = unittest.TestLoader()
        suite = test_loader.discover('tests', pattern='test_*.py')

    if suite.countTestCases() == 0:
        print(f"{Fore.YELLOW if COLORS_AVAILABLE else ''}⚠️ Тесты не найдены. Убедитесь, что в папке tests/ есть файлы с префиксом test_.py")
        sys.exit(0)

    print(f"🔍 Найдено тестов: {suite.countTestCases()}")

    # Запуск тестов
    print_section("Запуск тестов...", Fore.GREEN if COLORS_AVAILABLE else '')
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    # Вывод результатов
    print_header("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ", Fore.CYAN if COLORS_AVAILABLE else '')

    if result.wasSuccessful():
        status_color = Fore.GREEN if COLORS_AVAILABLE else ''
        status_text = "✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!"
    else:
        status_color = Fore.RED if COLORS_AVAILABLE else ''
        status_text = "❌ ЕСТЬ УПАВШИЕ ТЕСТЫ!"

    if COLORS_AVAILABLE:
        print(f"{status_color}{status_text}{Style.RESET_ALL}")
    else:
        print(status_text)

    print(f"📊 Выполнено тестов: {result.testsRun}")
    print(f"✅ Успешно: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Упало: {len(result.failures)}")
    print(f"⚠️ Ошибок: {len(result.errors)}")
    if result.skipped:
        print(f"⏭️ Пропущено: {len(result.skipped)}")

    # Дополнительная информация
    if result.failures or result.errors:
        print_section("📌 Детали проблем:", Fore.RED if COLORS_AVAILABLE else '')
        for i, (test, trace) in enumerate(result.failures, 1):
            print(f"{Fore.RED if COLORS_AVAILABLE else ''}{i}) Ошибка в тесте: {test}{Style.RESET_ALL}")
            print(f"{trace[:500]}...")  # ограничим вывод первых 500 символов
        for i, (test, trace) in enumerate(result.errors, 1):
            print(f"{Fore.YELLOW if COLORS_AVAILABLE else ''}{i}) Исключение в тесте: {test}{Style.RESET_ALL}")
            print(f"{trace[:500]}...")

    # Рекомендации
    print_section("💡 Полезные команды:", Fore.MAGENTA if COLORS_AVAILABLE else '')
    print("  python run_tests.py -v          # Запуск с подробным выводом")
    print("  python run_tests.py -t tests.test_pinecone_helpers  # Запуск конкретного файла")
    print("  python -m unittest discover tests  # Запуск через встроенный unittest")

    # Возвращаем код завершения
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()