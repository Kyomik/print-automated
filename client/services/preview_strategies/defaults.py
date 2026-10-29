"""Built-in format strategies used by the preview strategy factory."""

from services.preview_strategies.factory import PreviewStrategyFactory
from services.preview_strategies.image import ImagePreviewStrategy
from services.preview_strategies.pdf import PdfPreviewStrategy
from services.preview_strategies.word import WordPreviewStrategy


def default_preview_strategy_factory():
    return PreviewStrategyFactory((
        PdfPreviewStrategy(),
        ImagePreviewStrategy(),
        WordPreviewStrategy(),
    ))
