# tests/test_rendering.py
import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).parent.parent))
from pdf_generator import render_html, find_id_field

def test_find_id_field():
    record1 = {"invoice_id": "INV001", "customer": "Test"}
    field, value = find_id_field(record1)
    assert field == "invoice_id"
    assert value == "INV001"

    record2 = {"order_id": "ORD-001", "total": 100}
    field, value = find_id_field(record2)
    assert field == "order_id"

    record3 = {"unknown_field": "123", "data": "abc"}
    field, value = find_id_field(record3)
    assert field == "unknown_field"  # первый ключ

def test_render_html_simple(tmp_path):
    # Создаём временный HTML-шаблон
    template_content = """
    <html><body>
    <h1>{{ title }}</h1>
    <p>{{ description }}</p>
    </body></html>
    """
    template_path = tmp_path / "template.html"
    template_path.write_text(template_content, encoding='utf-8')

    record = {"title": "Привет", "description": "Мир"}
    result = render_html(template_path, record)
    assert "<h1>Привет</h1>" in result
    assert "<p>Мир</p>" in result
    assert "{{" not in result

def test_render_html_with_items_list(tmp_path):
    template_content = """
    <table>
        <tbody>
            {{ items }}
        </tbody>
    </table>
    """
    template_path = tmp_path / "template.html"
    template_path.write_text(template_content, encoding='utf-8')

    record = {
        "items": [
            {"name": "Товар1", "qty": 2, "price": 100.0},
            {"name": "Товар2", "qty": 1, "price": 50.0}
        ]
    }
    result = render_html(template_path, record)
    assert "<tr><td>Товар1</td><td>2</td><td>100.00</td><td>200.00</td></tr>" in result
    assert "<tr><td>Товар2</td><td>1</td><td>50.00</td><td>50.00</td></tr>" in result