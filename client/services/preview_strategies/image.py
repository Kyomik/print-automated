"""Raster image preview strategy and in-memory image session."""

from pathlib import Path

from PIL import Image, ImageOps

from domain.document_analysis import MeasurementUnit, PageGeometry
from services.preview_strategies.base import PreviewSession, PreviewStrategy
from services.preview_strategies.models import PreviewFrame, PreviewInfo


class ImagePreviewStrategy(PreviewStrategy):
    extensions = frozenset({".jpg", ".jpeg", ".png", ".webp"})

    def open(self, path: Path) -> PreviewSession:
        with Image.open(path) as source:
            orientation = source.getexif().get(274)
            image = ImageOps.exif_transpose(source)
            dpi_x, dpi_y = self._dpi_axes(source.info.get("dpi"), orientation)
            geometry = PageGeometry(
                image.width,
                image.height,
                MeasurementUnit.PIXELS,
                dpi_x,
                dpi_y,
            )
            image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
            image = image.convert("RGB")
        return ImagePreviewSession(image, geometry)

    @staticmethod
    def _dpi_axes(dpi, orientation):
        if not dpi or len(dpi) < 2:
            return None, None
        dpi_x, dpi_y = dpi[0], dpi[1]
        if orientation in {5, 6, 7, 8}:
            return dpi_y, dpi_x
        return dpi_x, dpi_y


class ImagePreviewSession(PreviewSession):
    def __init__(self, image: Image.Image, geometry: PageGeometry):
        self._image = image
        self._geometry = geometry
        self.info = PreviewInfo("IMAGE", 1, "IMAGE")

    def render(self, page_index: int = 0) -> PreviewFrame:
        if page_index != 0:
            raise IndexError("Gambar hanya memiliki satu halaman")
        return PreviewFrame(image=self._image.copy(), geometry=self._geometry)

    def close(self) -> None:
        self._image.close()
