import os
import logging
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_pdf(data: dict, template_name: str, output_dir: str = "reports") -> str:
    """
    Генерирует PDF из HTML-шаблона с данными.
    template_name: имя файла шаблона (например, 'client_report.html' или 'multiple_product_cards.html')
    data: словарь с данными для подстановки (может содержать список продуктов)
    output_dir: папка для сохранения PDF
    Возвращает путь к сгенерированному PDF.
    """
    template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_name)

    html_content = template.render(data)

    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_filename = f"products_{timestamp}.pdf" if "multiple" in template_name else f"report_{timestamp}.pdf"
    output_path = os.path.join(output_dir, output_filename)

    HTML(string=html_content).write_pdf(output_path)

    logger.info(f"PDF сохранён: {output_path}")
    return output_path