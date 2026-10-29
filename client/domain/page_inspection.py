"""Page analysis results used by print planning."""

from dataclasses import dataclass

from domain.document_analysis import PageAnalysis


@dataclass(frozen=True)
class DocumentInspection:
    pages: tuple[PageAnalysis, ...]
