"""Small lifecycle facade around format-specific preview strategies."""

from pathlib import Path

from services.preview_strategies.defaults import default_preview_strategy_factory
from services.preview_strategies.factory import PreviewStrategyFactory
from services.preview_strategies.models import PreviewFrame, PreviewInfo


class PreviewRenderer:
    def __init__(self, strategy_factory: PreviewStrategyFactory | None = None):
        self._strategy_factory = (
            strategy_factory
            if strategy_factory is not None
            else default_preview_strategy_factory()
        )
        self._session = None

    def open(self, path: Path) -> PreviewInfo:
        self.close()
        self._session = self._strategy_factory.open(Path(path))
        return self._session.info

    def render(self, page_index: int = 0) -> PreviewFrame:
        if self._session is None:
            return PreviewFrame(text="Tidak ada preview untuk file ini.")
        return self._session.render(page_index)

    def close(self) -> None:
        if self._session is not None:
            self._session.close()
            self._session = None
