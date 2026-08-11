#!/usr/bin/env python
"""
Общий скрипт для запуска всех тестов проекта.
Использует pytest для выполнения тестов из папки tests/.
"""
import sys
import pytest

if __name__ == "__main__":
    # Аргументы можно расширить: -v для подробного вывода, -s для вывода print и т.д.
    args = ["-v", "tests/"]
    # Если передан флаг --cov, можно добавить coverage, но пока просто базовый запуск.
    sys.exit(pytest.main(args))