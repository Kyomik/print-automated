"""Convert DOCX to PDF with hidden Microsoft Word, then print through GDI."""

from pathlib import Path
import tempfile

from domain.printer import PrintOptions
from .base import PrinterStrategy
from services.document_conversion.word_com import WordComConverter


class WordDocxPrinterStrategy(PrinterStrategy):
    extensions = frozenset({".docx"})

    def __init__(self, pdf_strategy: PrinterStrategy, converter=None):
        self.pdf_strategy = pdf_strategy
        self.converter = converter or WordComConverter()

    def print_file(self, path: Path, printer_name: str, page_selection: str | None = None, print_options: PrintOptions | None = None) -> dict:
        with tempfile.TemporaryDirectory(prefix="ilo-print-") as temp_dir:
            pdf_path = Path(temp_dir) / f"{path.stem}.pdf"
            self.converter.convert_to_pdf(path, pdf_path)
            return self.pdf_strategy.print_file(pdf_path, printer_name, page_selection, print_options)
