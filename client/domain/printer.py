"""Typed printer capabilities and per-job paper settings."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PrinterChoice:
    """A driver-provided choice identified by the value accepted by Windows."""

    id: int
    name: str


@dataclass(frozen=True)
class PrinterCapabilities:
    """Paper options exposed by one installed printer driver."""

    sources: tuple[PrinterChoice, ...] = ()
    paper_sizes: tuple[PrinterChoice, ...] = ()


@dataclass(frozen=True)
class PrintOptions:
    """Per-job print settings; unset paper fields use the driver's defaults."""

    source_id: int | None = None
    paper_id: int | None = None
    copies: int = 1

    def __post_init__(self):
        if (isinstance(self.copies, bool) or not isinstance(self.copies, int)
                or not 1 <= self.copies <= 999):
            raise ValueError("Jumlah rangkap harus bilangan bulat antara 1 dan 999")

    @property
    def has_overrides(self) -> bool:
        return self.source_id is not None or self.paper_id is not None
