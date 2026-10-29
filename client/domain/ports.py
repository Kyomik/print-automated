"""Application-facing ports implemented by client infrastructure adapters."""

from pathlib import Path
from typing import Any, Protocol

from domain.printer import PrinterCapabilities, PrintOptions
from domain.page_inspection import DocumentInspection


class AttachmentStore(Protocol):
    def simpan_file(self, incoming: dict[str, Any]) -> dict[str, Any]: ...


class PrinterGateway(Protocol):
    def ambil_semua_printer(self) -> list[str]: ...
    def ambil_kemampuan_printer(self, nama_printer: str) -> PrinterCapabilities: ...
    def cek_printer_ready(self, nama_printer: str) -> bool: ...
    def cetak_file(
        self,
        jalur_lengkap: str | Path,
        target_printer: str,
        page_selection: str | None = None,
        print_options: PrintOptions | None = None,
    ) -> dict[str, Any]: ...


class PrinterCapabilitiesProvider(Protocol):
    def get_capabilities(self, printer_name: str) -> PrinterCapabilities: ...
    def monitor_job(self, nama_printer: str, job_id: int, timeout: int = 300) -> str: ...


class DocumentPageInspector(Protocol):
    def inspect(self, path: str | Path) -> DocumentInspection: ...


class AutomatedPrintRuleProvider(Protocol):
    def load(self) -> Any: ...


class EventReporter(Protocol):
    def report_print_result(self, result: dict[str, Any]) -> None: ...
    def close(self) -> None: ...


class LogSink(Protocol):
    """Storage adapter for application log records."""

    def write(self, level: str, message: str) -> None: ...
