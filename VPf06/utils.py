import logging
from pathlib import Path
from typing import List

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    import docx
except ImportError:
    docx = None

logger = logging.getLogger(__name__)

def load_document(file_path: str) -> str:
    """
    Извлекает полный текст из файла (PDF, TXT, DOCX).
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    text = ""

    if suffix == ".txt":
        text = path.read_text(encoding="utf-8", errors="ignore")
    elif suffix == ".pdf":
        if PdfReader is None:
            raise RuntimeError("Для PDF требуется пакет pypdf. Установите: pip install pypdf")
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                pages.append("")
        text = "\n".join(pages)
    elif suffix in (".docx", ".doc"):
        if docx is None:
            raise RuntimeError("Для DOCX требуется пакет python-docx. Установите: pip install python-docx")
        document = docx.Document(str(path))
        text = "\n".join(p.text for p in document.paragraphs)
    else:
        raise RuntimeError("Поддерживаются только PDF, TXT, DOCX")

    return text