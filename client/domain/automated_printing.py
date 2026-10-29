"""Configuration and rules for page-by-page automated printer selection."""

from dataclasses import dataclass
from enum import Enum

from domain.document_analysis import ColorContent, PageAnalysis


class PrintMode(Enum):
    AUTOMATED = "Automated"
    MANUAL = "Manual"


DEFAULT_PAPER_SOURCE = "Bawaan printer"


@dataclass(frozen=True)
class PaperRule:
    paper_size: str
    printer_name: str
    paper_source: str | None


class AutomatedPrintRules:
    def __init__(self, rules):
        self._rules = rules

    @classmethod
    def from_mapping(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Konfigurasi cetak harus berupa object TOML")
        parsed = {}
        for color_key in ("hitam_putih", "warna"):
            paper_types = data.get(color_key)
            if not isinstance(paper_types, dict):
                raise ValueError(f"Bagian [{color_key}] wajib tersedia")
            parsed[color_key] = {}
            for paper, value in paper_types.items():
                if not isinstance(paper, str) or not paper.strip():
                    raise ValueError(f"Nama ukuran kertas pada [{color_key}] wajib diisi")
                if not isinstance(value, dict):
                    raise ValueError(f"Aturan {color_key}.{paper} harus berupa object")
                printer, source = value.get("nama_print"), value.get("sumber_kertas")
                if not isinstance(printer, str) or not printer.strip():
                    raise ValueError(f"{color_key}.{paper}.nama_print wajib diisi")
                if source is not None and (not isinstance(source, str) or not source.strip()):
                    raise ValueError(
                        f"{color_key}.{paper}.sumber_kertas harus berupa teks yang tidak kosong"
                    )
                if source is not None:
                    source = source.strip()
                if source is None or source.casefold() == DEFAULT_PAPER_SOURCE.casefold():
                    source = None
                canonical = paper.casefold().split()[0]
                if canonical in parsed[color_key]:
                    raise ValueError(f"Aturan ukuran kertas duplikat: [{color_key}].{paper}")
                parsed[color_key][canonical] = PaperRule(paper, printer.strip(), source)
        return cls(parsed)

    def resolve(self, analysis: PageAnalysis) -> PaperRule:
        if analysis.dimensions is None:
            raise ValueError("Ukuran kertas halaman tidak dapat diketahui")
        width, height = sorted((analysis.dimensions.width_mm, analysis.dimensions.height_mm))
        paper = next((name for name, size in (("a3", (297, 420)), ("a4", (210, 297)),
                     ("a5", (148, 210)), ("letter", (216, 279)),
                     ("folio", (216, 330)), ("legal", (216, 356)))
                     if abs(width-size[0]) <= 2 and abs(height-size[1]) <= 2), None)
        if paper is None:
            raise ValueError(f"Ukuran halaman {analysis.dimensions.description} belum ada di TOML")
        color = "warna" if analysis.color_content is ColorContent.COLOR else "hitam_putih"
        rule = self._rules[color].get(paper)
        if rule is None:
            raise ValueError(f"Aturan [{color}].{paper} belum ada di TOML")
        return rule
