"""PDF preview strategy and resource-owning PDF session."""

from pathlib import Path

from PIL import Image
import pymupdf

from domain.document_analysis import MeasurementUnit, PageGeometry
from services.preview_strategies.base import PreviewSession, PreviewStrategy
from services.preview_strategies.models import PreviewFrame, PreviewInfo


class PdfPreviewStrategy(PreviewStrategy):
    extensions = frozenset({".pdf"})

    def open(self, path: Path) -> PreviewSession:
        return PdfPreviewSession(pymupdf.open(path), "PDF")


class PdfPreviewSession(PreviewSession):
    def __init__(self, document, kind: str):
        self._document = document
        self.info = PreviewInfo(kind, len(document), kind)

    def render(self, page_index: int = 0) -> PreviewFrame:
        page = self._document.load_page(page_index)
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(1.15, 1.15), alpha=False)
        image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
        geometry = PageGeometry(
            page.rect.width,
            page.rect.height,
            MeasurementUnit.PDF_POINTS,
        )
        return PreviewFrame(image=image, geometry=geometry)

    def close(self) -> None:
        self._document.close()
