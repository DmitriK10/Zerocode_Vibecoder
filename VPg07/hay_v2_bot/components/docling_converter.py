import os
import logging
from haystack import component, Document
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat

# Отключаем torch inductor (избегаем ошибки с компилятором cl.exe)
os.environ["TORCHDYNAMO_DISABLE"] = "1"

logger = logging.getLogger(__name__)

@component
class DoclingConverterComponent:
    @component.output_types(documents=list[Document])
    def run(self, file_path: str) -> dict:
        """
        Конвертирует файл в список документов Haystack.
        Для PDF отключаем OCR (ускорение) и используем лёгкий pipeline.
        """
        logger.info(f"Начинаю конвертацию файла: {file_path}")

        # Настраиваем конвертер с отключённым OCR для PDF
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(use_ocr=False)
            }
        )

        try:
            result = converter.convert(file_path)
            docling_doc = result.document
            content = docling_doc.export_to_markdown()
            doc = Document(
                content=content,
                meta={"file_name": os.path.basename(file_path)}
            )
            logger.info(f"Конвертация завершена, длина текста: {len(content)} символов")
            return {"documents": [doc]}
        except Exception as e:
            logger.error(f"Ошибка конвертации: {e}")
            # Пробрасываем исключение, чтобы обработать выше
            raise