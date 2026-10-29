"""Run printer discovery and print submissions away from Tk's event loop."""

from threading import Thread

from application.print_dispatcher import PrintDispatcher


class PrintController:
    def __init__(self, workflow, result_queue):
        self.workflow = workflow
        self.result_queue = result_queue
        self.loading_printers = False
        self.dispatcher = PrintDispatcher(workflow, self._enqueue_print_result)

    def discover_printers(self):
        if self.loading_printers:
            return False
        self.loading_printers = True
        Thread(target=self._load_printers, name="printer-discovery", daemon=True).start()
        return False

    def submit(self, item, printer, page_selection=None, print_options=None, print_mode=None):
        from domain.automated_printing import PrintMode
        self.dispatcher.submit(item, printer, page_selection, print_options, print_mode or PrintMode.AUTOMATED)

    def load_capabilities(self, printer):
        Thread(target=self._load_capabilities, args=(printer,), name="printer-capabilities", daemon=True).start()

    def close(self):
        self.dispatcher.close()

    def _load_printers(self):
        try:
            printers = self.workflow.available_printers()
            self.result_queue.put({
                "kind": "printer_list",
                "printers": printers,
            })
            Thread(
                target=self._warm_printer_capabilities,
                args=(printers,),
                name="printer-capability-warmup",
                daemon=True,
            ).start()
        except Exception as error:
            self.result_queue.put({"kind": "printer_list", "error": error})

    def _warm_printer_capabilities(self, printers):
        for printer in printers:
            try:
                self.workflow.printer_capabilities(printer)
            except Exception:
                # A broken or unavailable queue should not prevent the others
                # from loading, and will be reported if its settings are opened.
                continue

    def _load_capabilities(self, printer):
        try:
            capabilities = self.workflow.printer_capabilities(printer)
            self.result_queue.put({"kind": "printer_capabilities", "printer": printer, "capabilities": capabilities})
        except Exception as error:
            self.result_queue.put({"kind": "printer_capabilities", "printer": printer, "error": error})

    def _enqueue_print_result(self, event):
        self.result_queue.put({"kind": "print_result", **event})
