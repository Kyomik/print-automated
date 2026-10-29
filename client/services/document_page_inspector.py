"""Inspect every document page for automated print planning."""

from pathlib import Path

from domain.page_inspection import DocumentInspection
from services.document_analyzer import DocumentAnalyzer
from services.preview_renderer import PreviewRenderer


class DocumentPageInspector:
    def __init__(self, renderer_factory=PreviewRenderer, analyzer=None):
        self._renderer_factory = renderer_factory
        self._analyzer = analyzer or DocumentAnalyzer()

    def inspect(self, path):
        renderer = self._renderer_factory()
        try:
            info = renderer.open(Path(path))
            if info.page_count < 1:
                raise ValueError("Dokumen tidak memiliki halaman.")
            pages = []
            for page_index in range(info.page_count):
                frame = renderer.render(page_index)
                if frame.image is None:
                    raise ValueError(f"Halaman {page_index + 1} tidak dapat dianalisis.")
                pages.append(self._analyzer.analyze(frame.image, frame.geometry))
            return DocumentInspection(tuple(pages))
        finally:
            renderer.close()
