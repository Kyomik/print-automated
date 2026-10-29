"""Contracts for document-format-specific preview strategies and sessions."""

from abc import ABC, abstractmethod
from pathlib import Path

from services.preview_strategies.models import PreviewInfo, PreviewFrame


class PreviewSession(ABC):
    info: PreviewInfo

    @abstractmethod
    def render(self, page_index: int = 0) -> PreviewFrame:
        """Render one page and return its raw geometry with the preview."""

    @abstractmethod
    def close(self) -> None:
        """Release files and resources held by the session."""


class PreviewStrategy(ABC):
    extensions: frozenset[str] = frozenset()

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.extensions

    @abstractmethod
    def open(self, path: Path) -> PreviewSession:
        """Open a source file and create its preview session."""
