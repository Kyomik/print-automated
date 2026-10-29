"""Analyze rendered page content and report its likely physical page size."""

from domain.document_analysis import (
    ColorContent,
    MeasurementUnit,
    PageAnalysis,
    PageDimensions,
    PageGeometry,
)


class DocumentAnalyzer:
    """Keep page-content classification separate from preview rendering."""

    _COLOR_CHANNEL_THRESHOLD = 18
    _MIN_COLOR_PIXEL_RATIO = 0.001
    _SAMPLE_SIZE = (96, 96)

    def analyze(self, image, geometry: PageGeometry | None) -> PageAnalysis:
        return PageAnalysis(
            color_content=self._classify_color(image),
            dimensions=self._page_dimensions(geometry),
        )

    @staticmethod
    def _page_dimensions(geometry):
        if geometry is None:
            return None
        if geometry.unit is MeasurementUnit.PDF_POINTS:
            return PageDimensions(
                geometry.width * 25.4 / 72,
                geometry.height * 25.4 / 72,
            )
        if (
            geometry.unit is MeasurementUnit.PIXELS
            and geometry.dpi_x
            and geometry.dpi_y
        ):
            return PageDimensions(
                geometry.width * 25.4 / geometry.dpi_x,
                geometry.height * 25.4 / geometry.dpi_y,
            )
        return None

    def _classify_color(self, image) -> ColorContent:
        sample = image.convert("RGB")
        sample.thumbnail(self._SAMPLE_SIZE)
        pixels = list(sample.getdata())
        if not pixels:
            return ColorContent.MONOCHROME

        colored_pixels = sum(
            1 for red, green, blue in pixels
            if max(red, green, blue) - min(red, green, blue)
            > self._COLOR_CHANNEL_THRESHOLD
        )
        if colored_pixels / len(pixels) >= self._MIN_COLOR_PIXEL_RATIO:
            return ColorContent.COLOR
        return ColorContent.MONOCHROME
