"""Use cases for receiving attachments and submitting print jobs."""

from domain.ports import AttachmentStore, EventReporter, PrinterGateway
from domain.printer import PrinterCapabilities, PrintOptions


class PrintWorkflow:
    def __init__(
        self,
        file_service: AttachmentStore,
        printer_service: PrinterGateway,
        socket_service: EventReporter,
        automated_print_use_case=None,
    ):
        self.file_service = file_service
        self.printer_service = printer_service
        self.socket_service = socket_service
        self.automated_print_use_case = automated_print_use_case

    def receive_attachment(self, payload):
        if not isinstance(payload, dict) or not payload.get("file"):
            message = payload.get("message", {}) if isinstance(payload, dict) else {}
            reason = message.get("attachmentError") or "Lampiran gagal diunduh atau ditolak server."
            self.report(status="gagal", file=message.get("id"), alasan=reason)
            raise ValueError(reason)
        return self.file_service.simpan_file(payload)

    def available_printers(self):
        return self.printer_service.ambil_semua_printer()

    def printer_capabilities(self, printer_name) -> PrinterCapabilities:
        return self.printer_service.ambil_kemampuan_printer(printer_name)

    def printer_is_ready(self, printer_name):
        return self.printer_service.cek_printer_ready(printer_name)

    def print_file(
        self,
        file_path,
        printer_name,
        page_selection=None,
        print_options: PrintOptions | None = None,
    ):
        return self.printer_service.cetak_file(file_path, printer_name, page_selection, print_options)

    def automated_print_file(self, file_path, page_selection=None, print_options=None):
        if self.automated_print_use_case is None:
            raise RuntimeError("Use case cetak otomatis belum dikonfigurasi")
        return self.automated_print_use_case.execute(file_path, page_selection, print_options)

    def monitor_job(self, printer_name, job_id):
        return self.printer_service.monitor_job(printer_name, job_id)

    def report(self, result=None, **fields):
        self.socket_service.report_print_result({**(result or {}), **fields})

    def close(self):
        self.socket_service.close()
