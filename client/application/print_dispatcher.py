"""Serialize print submissions and report their outcomes off the UI thread."""

from concurrent.futures import ThreadPoolExecutor

from domain.printer import PrintOptions
from domain.automated_printing import PrintMode


class PrintDispatcher:
    def __init__(self, workflow, on_result):
        self.workflow = workflow
        self.on_result = on_result
        self._submissions = ThreadPoolExecutor(max_workers=1, thread_name_prefix="print-submit")
        self._monitors = ThreadPoolExecutor(max_workers=4, thread_name_prefix="print-monitor")

    def submit(
        self,
        item,
        printer,
        page_selection=None,
        print_options: PrintOptions | None = None,
        print_mode=PrintMode.AUTOMATED,
    ):
        self._submissions.submit(self._submit_one, item, printer, page_selection, print_options, print_mode)

    def _submit_one(self, item, printer, page_selection, print_options, print_mode):
        event = {"item": item, "printer": printer, "page_selection": page_selection}
        try:
            if print_mode is PrintMode.MANUAL and not self.workflow.printer_is_ready(printer):
                event.update(status="printer_not_ready")
                self.on_result(event)
                return

            if print_mode is PrintMode.AUTOMATED:
                result = self.workflow.automated_print_file(
                    item["jalur"],
                    page_selection,
                    print_options,
                )
            else:
                result = self.workflow.print_file(item["jalur"], printer, page_selection, print_options)
            if not result or not result.get("berhasil"):
                reason = str((result or {}).get("alasan") or (result or {}).get("status") or "print gagal")
                for job in (result or {}).get("jobs", ()):
                    if job.get("job_id") is not None:
                        self._monitors.submit(
                            self._monitor_one, item, job["printer"], job["job_id"]
                        )
                self.workflow.report({
                    "status": "gagal", "file": item["nama_file"],
                    "printer": (result or {}).get("failed_printer", printer), "alasan": reason,
                })
                event.update(status="gagal", reason=reason)
                self.on_result(event)
                return

            jobs = result.get("jobs") or [{"printer": result.get("printer", printer),
                                            "job_id": result.get("job_id")}]
            job_id = result.get("job_id")
            job_printer = result.get("printer", printer)
            status = "queued" if job_id is not None else "sent"
            self.workflow.report({
                "status": status, "file": item["nama_file"],
                "printer": job_printer, "job_id": job_id,
            })
            event.update(status=status, job_id=job_id, printer=job_printer)
            self.on_result(event)
            for job in jobs:
                if job.get("job_id") is not None:
                    self._monitors.submit(self._monitor_one, item, job["printer"], job["job_id"])
        except Exception as error:
            try:
                self.workflow.report({
                    "status": "gagal", "file": item["nama_file"],
                    "printer": printer, "alasan": str(error),
                })
            except Exception:
                pass
            event.update(status="gagal", reason=str(error))
            self.on_result(event)

    def _monitor_one(self, item, printer, job_id):
        event = {"item": item, "printer": printer, "job_id": job_id}
        try:
            status = self.workflow.monitor_job(printer, job_id)
            self.workflow.report({"status": status, "file": item["nama_file"], "printer": printer})
            event.update(status=status, monitored=True)
        except Exception as error:
            try:
                self.workflow.report({
                    "status": "gagal", "file": item["nama_file"],
                    "printer": printer, "alasan": str(error),
                })
            except Exception:
                pass
            event.update(status="gagal", reason=str(error), monitored=True)
        self.on_result(event)

    def close(self):
        self._submissions.shutdown(wait=False, cancel_futures=True)
        self._monitors.shutdown(wait=False, cancel_futures=True)
