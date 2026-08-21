#!/usr/bin/env python3
"""
run_all_tests.py
Запускает все тесты проекта с помощью pytest.
"""
import subprocess
import sys

def main():
    print("Запуск всех тестов...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v"],
        capture_output=False,
        text=True
    )
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()