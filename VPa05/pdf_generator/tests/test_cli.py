# tests/test_cli.py
import subprocess
import sys
from pathlib import Path
import pytest

@pytest.mark.integration
def test_cli_generate_invoice(tmp_path, monkeypatch):
    # Подготавливаем тестовое окружение
    project_dir = Path(__file__).parent.parent
    data_dir = tmp_path / "data"
    templates_dir = tmp_path / "templates"
    output_dir = tmp_path / "output"
    data_dir.mkdir()
    templates_dir.mkdir()
    output_dir.mkdir()

    # Копируем реальные файлы или создаём тестовые
    import shutil
    shutil.copy(project_dir / "data" / "invoices.csv", data_dir / "invoices.csv")
    shutil.copy(project_dir / "templates" / "invoice_simple.html", templates_dir / "invoice_simple.html")

    # Подменяем пути в скрипте через monkeypatch или переменные окружения
    # (для упрощения можно написать отдельный тестовый скрипт)
    # Здесь мы просто проверим, что скрипт не падает с ошибкой при корректных данных
    # Для полного теста CLI используем subprocess с передачей stdin

    # Это пример, для реального использования лучше создать тестовый скрипт,
    # который принимает аргументы командной строки, а не input()