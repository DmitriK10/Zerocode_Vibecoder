#!/usr/bin/env python
import unittest
import sys
import os

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    # Загружаем все тесты из папки tests/
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Возвращаем код выхода (0 если успешно, иначе 1)
    sys.exit(0 if result.wasSuccessful() else 1)