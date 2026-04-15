# tests/test_loaders.py
import json
import csv
import pytest
from pathlib import Path
import sys

# Добавляем путь к корневой папке проекта, чтобы импортировать модули
sys.path.append(str(Path(__file__).parent.parent))
from pdf_generator import load_data, PANDAS_AVAILABLE

# Фикстура для создания временных файлов
@pytest.fixture
def temp_csv_file(tmp_path):
    data = """invoice_id,customer_name,date,item,quantity,price,total
INV001,ООО "Ромашка",2025-04-01,Товар А,2,1500.00,3000.00
INV002,ИП Иванов,2025-04-02,Товар Б,1,2500.50,2500.50
"""
    file_path = tmp_path / "test.csv"
    file_path.write_text(data, encoding='utf-8')
    return file_path

@pytest.fixture
def temp_json_file(tmp_path):
    data = [
        {"id": 1, "name": "Test", "phone": "123"},
        {"id": 2, "name": "Test2", "phone": "456"}
    ]
    file_path = tmp_path / "test.json"
    file_path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    return file_path

def test_load_csv_pandas(temp_csv_file, monkeypatch):
    monkeypatch.setattr("pdf_generator.PANDAS_AVAILABLE", True)
    records = load_data(temp_csv_file)
    assert len(records) == 2
    assert records[0]["invoice_id"] == "INV001"
    assert records[1]["customer_name"] == "ИП Иванов"

def test_load_csv_standard(temp_csv_file, monkeypatch):
    monkeypatch.setattr("pdf_generator.PANDAS_AVAILABLE", False)
    records = load_data(temp_csv_file)
    assert len(records) == 2
    assert records[0]["total"] == "3000.00"
    assert records[1]["item"] == "Товар Б"

def test_load_json(temp_json_file):
    records = load_data(temp_json_file)
    assert isinstance(records, list)
    assert records[0]["name"] == "Test"
    assert records[1]["id"] == 2