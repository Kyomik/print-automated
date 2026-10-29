"""Typed results produced while inspecting rendered document pages."""

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar


class ColorContent(Enum):
    COLOR = "Berwarna"
    MONOCHROME = "Hitam putih"


class MeasurementUnit(Enum):
    PIXELS = "px"
    PDF_POINTS = "pt"


@dataclass(frozen=True)
class PageGeometry:
    """Raw page measurements supplied by a document renderer."""

    width: float
    height: float
    unit: MeasurementUnit
    dpi_x: float | None = None
    dpi_y: float | None = None


@dataclass(frozen=True)
class PageDimensions:
    width_mm: float
    height_mm: float

    _KNOWN_SIZES: ClassVar[dict[str, tuple[int, int]]] = {
        "A3": (297, 420),
        "A4": (210, 297),
        "A5": (148, 210),
        "Letter": (216, 279),
        "Folio": (216, 330),
        "Legal": (216, 356),
    }

    @property
    def description(self) -> str:
        width, height = sorted((self.width_mm, self.height_mm))
        for name, (known_width, known_height) in self._KNOWN_SIZES.items():
            if abs(width - known_width) <= 2 and abs(height - known_height) <= 2:
                return f"{name} ({self.width_mm:.0f} × {self.height_mm:.0f} mm)"
        return f"{self.width_mm:.0f} × {self.height_mm:.0f} mm"


@dataclass(frozen=True)
class PageAnalysis:
    color_content: ColorContent
    dimensions: PageDimensions | None
