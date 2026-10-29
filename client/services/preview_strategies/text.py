"""Text-only preview session shared by fallback and document strategies."""

from services.preview_strategies.base import PreviewSession
from services.preview_strategies.models import PreviewFrame, PreviewInfo


class TextPreviewSession(PreviewSession):
    def __init__(self, info: PreviewInfo, text: str):
        self.info = info
        self._text = text

    def render(self, page_index: int = 0) -> PreviewFrame:
        if page_index != 0:
            raise IndexError("Preview teks hanya memiliki satu halaman")
        return PreviewFrame(text=self._text)

    def close(self) -> None:
        pass


class UnsupportedPreviewSession(TextPreviewSession):
    def __init__(self):
        super().__init__(
            PreviewInfo("FILE", 1, "Preview tidak didukung untuk format ini"),
            "Tidak ada preview untuk file ini.",
        )
