"""Format-specific raster strategies for images and PDF documents."""

from pathlib import Path
from domain.printer import PrintOptions

from PIL import Image, ImageOps
import pymupdf

from .base import PrinterStrategy
from domain.page_selection import selected_page_indices
from .windows_gdi import WindowsGdiPrinter


class ImagePrinterStrategy(PrinterStrategy):
    extensions = frozenset({".jpg", ".jpeg", ".png", ".webp"})

    def __init__(self, backend: WindowsGdiPrinter):
        self.backend = backend

    def print_file(self, path: Path, printer_name: str, page_selection: str | None = None, print_options: PrintOptions | None = None) -> dict:
        selected_page_indices(page_selection, 1)
        with Image.open(path) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
        job_id = self.backend.print_pages([image], printer_name, path.name, print_options)
        return {"berhasil": True, "job_id": job_id, "status": "queued"}


class PdfPrinterStrategy(PrinterStrategy):
    extensions = frozenset({".pdf"})

    def __init__(self, backend: WindowsGdiPrinter, dpi: int = 300):
        self.backend = backend
        self.dpi = dpi

    def print_file(self, path: Path, printer_name: str, page_selection: str | None = None, print_options: PrintOptions | None = None) -> dict:
        def render_pages():
            document = pymupdf.open(path)
            try:
                scale = self.dpi / 72
                for page_index in selected_page_indices(page_selection, len(document)):
                    pdf_page = document.load_page(page_index)
                    pixmap = pdf_page.get_pixmap(
                        matrix=pymupdf.Matrix(scale, scale), alpha=False
                    )
                    yield Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            finally:
                document.close()

        job_id = self.backend.print_pages(render_pages(), printer_name, path.name, print_options)
        return {"berhasil": True, "job_id": job_id, "status": "queued"}
