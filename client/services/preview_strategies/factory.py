"""Select the preview strategy registered for an incoming file format."""

from pathlib import Path

from services.preview_strategies.base import PreviewSession, PreviewStrategy
from services.preview_strategies.text import UnsupportedPreviewSession


class PreviewStrategyFactory:
    def __init__(self, strategies: tuple[PreviewStrategy, ...]):
        self._strategies = tuple(strategies)

    def open(self, path: Path) -> PreviewSession:
        strategy = next(
            (candidate for candidate in self._strategies if candidate.supports(path)),
            None,
        )
        if strategy is not None:
            return strategy.open(path)
        return UnsupportedPreviewSession()
