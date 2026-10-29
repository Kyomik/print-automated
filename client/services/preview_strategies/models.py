"""Preview data shared by format strategies and the preview renderer."""

from dataclasses import dataclass

from PIL import Image

from domain.document_analysis import PageAnalysis, PageGeometry


@dataclass(frozen=True)
class PreviewInfo:
    kind: str
    page_count: int
    description: str


@dataclass(frozen=True)
class PreviewFrame:
    image: Image.Image | None = None
    text: str | None = None
    geometry: PageGeometry | None = None
    analysis: PageAnalysis | None = None
