"""Print raster pages directly to a Windows printer device context."""

from collections.abc import Iterable
from PIL import Image, ImageWin
from domain.printer import PrintOptions
import win32ui
import win32gui
import win32con


class WindowsGdiPrinter:
    def print_pages(
        self,
        pages: Iterable[Image.Image],
        printer_name: str,
        title: str,
        print_options: PrintOptions | None = None,
    ) -> int:
        if print_options and (print_options.has_overrides or print_options.copies != 1):
            devmode = self._printer_devmode(printer_name, print_options)
            device_handle = win32gui.CreateDC("WINSPOOL", printer_name, devmode)
            if not device_handle:
                raise RuntimeError(f"Tidak dapat membuat koneksi cetak ke {printer_name}")
            device = win32ui.CreateDCFromHandle(device_handle)
        else:
            device = win32ui.CreateDC()
            device.CreatePrinterDC(printer_name)
        job_id = None
        document_started = False
        try:
            job_id = device.StartDoc(title)
            document_started = True
            page_width = device.GetDeviceCaps(win32con.HORZRES)
            page_height = device.GetDeviceCaps(win32con.VERTRES)

            for page in pages:
                image = page.convert("RGB")
                scale = min(page_width / image.width, page_height / image.height)
                width = max(1, round(image.width * scale))
                height = max(1, round(image.height * scale))
                left = (page_width - width) // 2
                top = (page_height - height) // 2

                device.StartPage()
                ImageWin.Dib(image).draw(
                    device.GetHandleOutput(),
                    (left, top, left + width, top + height),
                )
                device.EndPage()

            device.EndDoc()
            document_started = False
            return job_id
        except Exception:
            if document_started:
                try:
                    device.AbortDoc()
                except Exception:
                    pass
            raise
        finally:
            device.DeleteDC()

    @staticmethod
    def _printer_devmode(printer_name, print_options: PrintOptions | None):
        if not print_options or not (print_options.has_overrides or print_options.copies != 1):
            return None
        import win32print

        handle = win32print.OpenPrinter(printer_name)
        try:
            devmode = win32print.GetPrinter(handle, 2).get("pDevMode")
            if devmode is None:
                return None
            if print_options.source_id is not None:
                devmode.DefaultSource = int(print_options.source_id)
                devmode.Fields |= win32con.DM_DEFAULTSOURCE
            if print_options.paper_id is not None:
                devmode.PaperSize = int(print_options.paper_id)
                devmode.Fields |= win32con.DM_PAPERSIZE
            if print_options.copies != 1:
                devmode.Copies = print_options.copies
                devmode.Fields |= win32con.DM_COPIES
                devmode.Collate = win32con.DMCOLLATE_TRUE
                devmode.Fields |= win32con.DM_COLLATE
            return devmode
        finally:
            win32print.ClosePrinter(handle)
