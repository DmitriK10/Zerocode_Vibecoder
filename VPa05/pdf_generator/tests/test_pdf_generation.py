# tests/test_pdf_generation.py
import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).parent.parent))
from pdf_generator import generate_pdf

def test_generate_pdf_creates_file(tmp_path):
    html_content = "<html><body><h1>Test PDF</h1></body></html>"
    output_pdf = tmp_path / "test.pdf"
    generate_pdf(html_content, output_pdf)
    assert output_pdf.exists()
    assert output_pdf.stat().st_size > 0