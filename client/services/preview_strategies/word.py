"""Word document preview strategy using Word's PDF export."""

from pathlib import Path
import tempfile
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from services.document_conversion.word_com import WordComConverter
from services.preview_strategies.base import PreviewSession, PreviewStrategy
from services.preview_strategies.models import PreviewFrame, PreviewInfo
from services.preview_strategies.pdf import PdfPreviewSession
from services.preview_strategies.text import TextPreviewSession


class WordPreviewStrategy(PreviewStrategy):
    extensions = frozenset({".docx"})

    def __init__(self, converter=None):
        self._converter = converter or WordComConverter()

    def open(self, path: Path) -> PreviewSession:
        temporary_directory = tempfile.TemporaryDirectory(prefix="ilo-preview-")
        pdf_path = Path(temporary_directory.name) / "preview.pdf"
        try:
            self._converter.convert_to_pdf(path, pdf_path)
            import pymupdf

            document = pymupdf.open(pdf_path)
            return WordPdfPreviewSession(document, temporary_directory)
        except Exception as error:
            temporary_directory.cleanup()
            text = self._extract_text(path)
            return TextPreviewSession(
                PreviewInfo(
                    "WORD",
                    1,
                    f"Preview teks Word; konversi visual gagal: {error}",
                ),
                text,
            )

    @staticmethod
    def _extract_text(path: Path) -> str:
        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        with ZipFile(path) as package:
            document = ET.fromstring(package.read("word/document.xml"))
        paragraphs = []
        for paragraph in document.findall(".//w:p", namespace):
            text = "".join(
                node.text or "" for node in paragraph.findall(".//w:t", namespace)
            )
            if text.strip():
                paragraphs.append(text)
        return "\n\n".join(paragraphs[:70]) or (
            "Dokumen Word tidak memiliki teks yang dapat ditampilkan."
        )


class WordPdfPreviewSession(PdfPreviewSession):
    def __init__(self, document, temporary_directory):
        super().__init__(document, "WORD")
        self._temporary_directory = temporary_directory

    def close(self) -> None:
        try:
            super().close()
        finally:
            self._temporary_directory.cleanup()


