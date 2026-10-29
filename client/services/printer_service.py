import time
from pathlib import Path
from threading import Lock
import win32print

from domain.printer import PrinterCapabilities, PrintOptions
from domain.ports import PrinterCapabilitiesProvider
from services.printer_strategies.defaults import default_print_strategies
from utils.logger import cetak_log


class PrinterService:
    def __init__(
        self,
        print_strategies=None,
        capabilities_provider: PrinterCapabilitiesProvider | None = None,
    ):
        self._print_strategies = tuple(print_strategies or default_print_strategies())
        self._capabilities_provider = capabilities_provider
        self._capabilities_cache = {}
        self._capabilities_locks = {}
        self._capabilities_lock_guard = Lock()

    def ambil_semua_printer(self):
        printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
        return [p[2] for p in printers]

    def ambil_kemampuan_printer(self, nama_printer) -> PrinterCapabilities:
        if self._capabilities_provider is None:
            raise RuntimeError("Printer capabilities provider belum dikonfigurasi")
        key = nama_printer.casefold()
        with self._capabilities_lock_guard:
            printer_lock = self._capabilities_locks.setdefault(key, Lock())
        with printer_lock:
            if key not in self._capabilities_cache:
                self._capabilities_cache[key] = self._capabilities_provider.get_capabilities(nama_printer)
            return self._capabilities_cache[key]

    def cek_printer_ready(self, nama_printer):
        try:
            handle = win32print.OpenPrinter(nama_printer)
            try:
                info = win32print.GetPrinter(handle, 2)
                status = info["Status"]

                if status == 0:
                    return True

                cetak_log("warning", f"[Service] Printer {nama_printer} tidak siap. Status: {status}")
                return False
            finally:
                win32print.ClosePrinter(handle)
        except Exception as e:
            cetak_log("error", f"[Service] Gagal mengecek printer {nama_printer}: {e}")
            return False

    def cetak_file(
        self,
        jalur_lengkap,
        target_printer,
        page_selection=None,
        print_options: PrintOptions | None = None,
    ):
        if not target_printer:
            cetak_log("error", "[Service] Nama printer tidak ditentukan")
            return {"berhasil": False, "job_id": None, "status": "error"}

        path = Path(jalur_lengkap)
        if not path.is_file():
            cetak_log("error", f"[Service] File tidak ditemukan: {jalur_lengkap}")
            return {"berhasil": False, "job_id": None, "status": "error"}

        if not self.cek_printer_ready(target_printer):
            return {"berhasil": False, "job_id": None, "status": "printer_not_ready"}

        try:
            cetak_log("info", f"[Service] Mengirim {jalur_lengkap} ke {target_printer}")
            strategy = next((item for item in self._print_strategies if item.supports(path)), None)
            if strategy is None:
                raise ValueError(f"Format file belum didukung untuk cetak: {path.suffix or '(tanpa ekstensi)'}")
            result = strategy.print_file(path, target_printer, page_selection, print_options)
            job_id = result.get("job_id")
            if job_id is not None:
                cetak_log("sukses", f"[Service] Job {job_id} masuk spooler {target_printer}")
            else:
                cetak_log(
                    "sukses",
                    f"[Service] Dokumen berhasil dikirim ke {target_printer}; "
                    "ID job tidak tersedia sehingga status lanjutannya tidak dapat dipantau",
                )
            return result
        except Exception as e:
            cetak_log("error", f"[Service] Gagal mengirim file ke {target_printer}: {e}")
            return {"berhasil": False, "job_id": None, "status": "error", "alasan": str(e)}

    def monitor_job(self, nama_printer, job_id, timeout=300):
        handle = win32print.OpenPrinter(nama_printer)
        try:
            waktu_mulai = time.time()
            status_sebelumnya = None

            while time.time() - waktu_mulai < timeout:
                try:
                    job = win32print.GetJob(handle, job_id, 1)
                    status = job.get("Status", 0)
                    status_sekarang = self._ubah_status_job(status)

                    if status_sekarang != status_sebelumnya:
                        cetak_log("info", f"[Service] Job {job_id}: {status_sekarang}")
                        status_sebelumnya = status_sekarang

                    if status_sekarang in ("error", "offline", "paperout", "deleted", "printed", "complete"):
                        return status_sekarang
                except Exception:
                    cetak_log("info", f"[Service] Job {job_id} sudah tidak ditemukan di spooler")
                    return "finished"
                time.sleep(1)

            cetak_log("warning", f"[Service] Monitoring Job {job_id} timeout")
            return "timeout"
        finally:
            win32print.ClosePrinter(handle)

    def _ubah_status_job(self, status):
        if status & win32print.JOB_STATUS_ERROR:   return "error"
        if status & win32print.JOB_STATUS_OFFLINE: return "offline"
        if status & win32print.JOB_STATUS_PAPEROUT: return "paperout"
        if status & win32print.JOB_STATUS_DELETING: return "deleted"
        if status & win32print.JOB_STATUS_PRINTED:  return "printed"
        if status & win32print.JOB_STATUS_COMPLETE: return "complete"
        if status & win32print.JOB_STATUS_PRINTING: return "printing"
        if status & win32print.JOB_STATUS_SPOOLING: return "spooling"
        return "queued"
