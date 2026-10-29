"""Contract for format-specific document printing strategies."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from domain.printer import PrintOptions


class PrinterStrategy(ABC):
    extensions: frozenset[str] = frozenset()

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.extensions

    @abstractmethod
    def print_file(
        self,
        path: Path,
        printer_name: str,
        page_selection: str | None = None,
        print_options: PrintOptions | None = None,
    ) -> dict[str, Any]:
        """Render and submit one file to the chosen printer."""
