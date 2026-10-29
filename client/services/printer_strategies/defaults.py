"""Composition of the built-in document printing strategies."""

from .media import ImagePrinterStrategy, PdfPrinterStrategy
from .windows_gdi import WindowsGdiPrinter
from .word_docx import WordDocxPrinterStrategy


def default_print_strategies():
    gdi_printer = WindowsGdiPrinter()
    pdf_strategy = PdfPrinterStrategy(gdi_printer)
    return (
        ImagePrinterStrategy(gdi_printer),
        pdf_strategy,
        WordDocxPrinterStrategy(pdf_strategy),
    )
