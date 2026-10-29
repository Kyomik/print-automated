"""Windows spooler adapter for driver-reported paper capabilities."""

import win32con
import win32print

from domain.printer import PrinterCapabilities, PrinterChoice


class WindowsPrinterCapabilities:
    def get_capabilities(self, printer_name: str) -> PrinterCapabilities:
        handle = win32print.OpenPrinter(printer_name)
        try:
            printer_info = win32print.GetPrinter(handle, 2)
            port_name = printer_info.get("pPortName")
            devmode = printer_info.get("pDevMode")
            return PrinterCapabilities(
                sources=self._choices(
                    printer_name, port_name, devmode,
                    win32con.DC_BINS, win32con.DC_BINNAMES,
                ),
                paper_sizes=self._choices(
                    printer_name, port_name, devmode,
                    win32con.DC_PAPERS, win32con.DC_PAPERNAMES,
                ),
            )
        finally:
            win32print.ClosePrinter(handle)

    @staticmethod
    def _choices(
        printer_name,
        port_name,
        devmode,
        id_capability,
        name_capability,
    ) -> tuple[PrinterChoice, ...]:
        ids = win32print.DeviceCapabilities(
            printer_name, port_name, id_capability, devmode
        ) or []
        names = win32print.DeviceCapabilities(
            printer_name, port_name, name_capability, devmode
        ) or []
        return tuple(
            PrinterChoice(int(choice_id), str(name).replace("\x00", "").strip())
            for choice_id, name in zip(ids, names)
        )
