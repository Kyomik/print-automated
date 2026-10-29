"""Application use case for analyzing and submitting automated print jobs."""

from dataclasses import replace

from domain.page_selection import selected_page_indices
from domain.ports import AutomatedPrintRuleProvider, DocumentPageInspector, PrinterGateway
from application.automated_print_planner import AutomatedPrintPlanner


class AutomatedPrintUseCase:
    def __init__(
        self,
        printer_gateway: PrinterGateway,
        rule_repository: AutomatedPrintRuleProvider,
        page_inspector: DocumentPageInspector,
        planner: AutomatedPrintPlanner | None = None,
    ):
        self._printers = printer_gateway
        self._rules = rule_repository
        self._inspector = page_inspector
        self._planner = planner or AutomatedPrintPlanner(printer_gateway)

    def execute(self, file_path, page_selection=None, print_options=None):
        inspection = self._inspector.inspect(file_path)
        indices = selected_page_indices(page_selection, len(inspection.pages))
        rules = self._rules.load()
        batches = self._planner.plan(inspection.pages, indices, rules)

        jobs = []
        for batch in batches:
            result = self._printers.cetak_file(
                file_path, batch.printer_name, batch.page_selection,
                _with_copies(batch.options, print_options),
            )
            if not result or not result.get("berhasil"):
                reason = (result or {}).get("alasan") or "Gagal mengirim pekerjaan cetak otomatis."
                return {
                    "berhasil": False,
                    "alasan": reason,
                    "failed_printer": batch.printer_name,
                    "jobs": jobs,
                }
            jobs.append({"printer": batch.printer_name, "job_id": result.get("job_id")})

        return {
            "berhasil": True,
            "jobs": jobs,
            "job_id": jobs[-1]["job_id"] if jobs else None,
            "printer": jobs[-1]["printer"] if jobs else None,
        }


def _with_copies(batch_options, request_options):
    """Preserve rule-selected paper settings while applying the requested copies."""
    if request_options is None:
        return batch_options
    return replace(batch_options, copies=request_options.copies)
