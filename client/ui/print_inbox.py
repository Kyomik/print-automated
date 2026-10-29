"""Desktop inbox for previewing WhatsApp attachments before printing."""

from __future__ import annotations

from queue import Empty, Queue
from threading import Thread
from dataclasses import replace
import tkinter as tk
from tkinter import ttk
import qrcode
from PIL import ImageTk

from application.print_workflow import PrintWorkflow
from services.document_analyzer import DocumentAnalyzer
from ui.components.header import build_header
from ui.components.print_toolbar import build_print_toolbar
from ui.components.preview_panel import build_preview_panel
from ui.components.queue_panel import QueuePanel
from ui.attachment_controller import AttachmentController
from ui.print_controller import PrintController
from ui.printer_settings_controller import PrinterSettingsController
from ui.preview_controller import PreviewController
from ui.print_queue_controller import PrintQueueController
from ui.theme import ACCENT, BG, MUTED
from utils.logger import cetak_log

from ui.print_status import print_status_display
from domain.automated_printing import PrintMode


# A busy socket must not monopolize a Tk event-loop iteration. The remaining
# entries stay in Queue and are handled on the next scheduled poll.
_MAX_RESULTS_PER_POLL = 12
_MAX_INCOMING_PER_POLL = 8


class PrintInbox:
    def __init__(self, workflow: PrintWorkflow, document_analyzer=None):
        self.workflow = workflow
        self.root = tk.Tk()
        self.root.title("Ilo • Cetak WhatsApp")
        self.root.geometry("1180x760")
        self.root.minsize(900, 620)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.results = Queue()
        self._qr_window = None
        self.attachments = AttachmentController(
            workflow,
            self.results,
            analyzer=(
                document_analyzer
                if document_analyzer is not None
                else DocumentAnalyzer()
            ),
        )
        self.queue = PrintQueueController(self.attachments)
        self.printer_controller = PrintController(workflow, self.results)
        self.printer_settings = PrinterSettingsController(
            self.root, self.printer_controller, lambda: self.printer_var.get()
        )
        self.printers = []
        self._toolbar_print_item = None
        self._print_all_items = set()

        self._build_ui()
        self.printer_controller.discover_printers()
        self.root.after(150, self._poll_queues)

    def _build_ui(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TCombobox", padding=8, fieldbackground="#ffffff")
        style.configure("TButton", padding=(12, 9), font=("Segoe UI", 9))
        style.configure("Accent.TButton", padding=(16, 10), font=("Segoe UI", 9, "bold"),
                        background=ACCENT, foreground="#ffffff")
        style.map("Accent.TButton", background=[("active", "#1d4ed8"), ("disabled", "#9bbcf8")],
                  foreground=[("disabled", "#f4f7ff")])

        self.connection_status, self.reconnect_button = build_header(
            self.root, self._request_reconnect
        )

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=28, pady=(0, 16))
        body.columnconfigure(0, weight=0, minsize=340)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self.queue_panel = QueuePanel(
            body, self._select_file_index, self._remove_item, self._print_item,
            self._clear_all, self._print_all,
        )
        preview = build_preview_panel(body, self._change_page, self._commit_page_selection)
        self.preview = PreviewController(
            preview, self.queue, self.attachments, self._set_status, self._refresh_file_list
        )
        toolbar = build_print_toolbar(
            self.root, self.printer_settings.open, self._remove_selected,
            self._print_selected,
        )
        for name, widget in toolbar.items():
            setattr(self, name, widget)
        self.printer_settings.set_button(self.settings_button)
        self.printer_box.bind("<<ComboboxSelected>>", self._handle_printer_selection)
        self._handle_printer_selection()
        self._refresh_file_list()

    def enqueue(self, payload):
        """Socket callback; safe to call from the Socket.IO background thread."""
        self.queue.enqueue(payload)

    def show_whatsapp_qr(self, value):
        """Schedule QR display on Tk's event loop from a socket callback."""
        self.results.put({"kind": "whatsapp_qr", "value": value})

    def run(self):
        self.root.mainloop()

    def close(self):
        try:
            self.attachments.close(self.queue.items)
            self.printer_controller.close()
            Thread(target=self.workflow.close, daemon=True).start()
        except Exception:
            pass
        self.root.destroy()

    def _poll_queues(self):
        # Keep the poll alive even if one queue update raises unexpectedly.
        self.root.after(150, self._poll_queues)

        # Snapshot completed work before submitting new attachments. This
        # keeps fast workers from skipping the visible loading state.
        pending_results = []
        while len(pending_results) < _MAX_RESULTS_PER_POLL:
            try:
                pending_results.append(self.results.get_nowait())
            except Empty:
                break

        received_items, should_show_selection = self.queue.accept_pending(_MAX_INCOMING_PER_POLL)
        if received_items:
            self._refresh_file_list()
            if should_show_selection:
                self.preview.show_selected()
            self.status_label.configure(
                text="File diterima. Sedang menyiapkan preview…", fg=ACCENT
            )

        preview_list_dirty = False
        for result in pending_results:
            if isinstance(result, dict) and result.get("kind", "").startswith("preview_"):
                if result["kind"] in ("preview_page_ready", "preview_page_error"):
                    self.preview.handle_page_result(result)
                elif result["kind"] == "preview_display_ready":
                    self.preview.handle_display_result(result)
                else:
                    self.preview.handle_item_result(result, refresh=False)
                    preview_list_dirty = True
            elif isinstance(result, dict) and result.get("kind") == "printer_list":
                self._handle_printer_list_result(result)
            elif isinstance(result, dict) and result.get("kind") == "printer_capabilities":
                self.printer_settings.handle_capabilities_result(result)
            elif isinstance(result, dict) and result.get("kind") == "whatsapp_qr":
                self._show_whatsapp_qr(result["value"])
            elif isinstance(result, dict) and result.get("kind") == "connection_status":
                self._show_connection_status(result)
            elif isinstance(result, dict) and result.get("kind") == "incoming_error":
                self.status_label.configure(
                    text=f"File gagal diterima: {result['error']}", fg="#b42318"
                )
            else:
                self._handle_print_result(result)

        if preview_list_dirty:
            self._refresh_file_list()

    def _request_reconnect(self):
        self.reconnect_button.configure(state="disabled", text="Mencoba…")
        self.workflow.socket_service.reconnect()

    def connection_changed(self, connected, message):
        """Socket callback; queue the update for Tk's event loop."""
        self.results.put({"kind": "connection_status", "connected": connected,
                          "message": message})

    def _show_connection_status(self, result):
        connected = result["connected"]
        self.connection_status.configure(
            text=f"● {result['message']}", fg="#067647" if connected else "#b42318"
        )
        if connected:
            self.reconnect_button.pack_forget()
        else:
            self.reconnect_button.configure(state="normal", text="Sambungkan ulang")
            if not self.reconnect_button.winfo_manager():
                self.reconnect_button.pack(side="right", padx=(12, 0))

    def _show_whatsapp_qr(self, value):
        if self._qr_window is not None:
            try:
                if self._qr_window.winfo_exists():
                    self._qr_window.destroy()
            except tk.TclError:
                pass
        self._qr_window = tk.Toplevel(self.root)
        self._qr_window.title("Hubungkan WhatsApp")
        self._qr_window.resizable(False, False)
        self._qr_window.transient(self.root)
        image = qrcode.make(value).resize((320, 320))
        photo = ImageTk.PhotoImage(image)
        label = tk.Label(self._qr_window, image=photo, padx=16, pady=16)
        label.image = photo
        label.pack()
        tk.Label(
            self._qr_window,
            text="Pindai QR ini dengan WhatsApp untuk menghubungkan sesi.",
            padx=16,
        ).pack(pady=(0, 16))

    def _refresh_file_list(self):
        self.queue_panel.set_printer_available(self._can_print_with_current_mode())
        self.queue_panel.render(self.queue.items, self.queue.selected_index)
        self._update_action_states()

    def _update_action_states(self):
        selected_item = (
            self.queue.selected_item
        )
        has_selection = selected_item is not None
        self.remove_action.set_enabled(has_selection)
        can_print = bool(
            selected_item and selected_item.get("jalur")
            and not selected_item.get("loading") and not selected_item.get("printing")
            and self._can_print_with_current_mode()
        )
        self.print_action.set_enabled(can_print)

        has_printers = bool(self.printers)
        self.printer_box.configure(state="readonly" if has_printers else "disabled")
        self.preview.update_action_states()

    def _can_print_with_current_mode(self):
        return self._is_automated_selection() or self.printer_var.get() in self.printers

    def _is_automated_selection(self):
        return self.printer_var.get() == PrintMode.AUTOMATED.value

    def _select_file_index(self, index):
        self.preview.select(index)

    def _change_page(self, amount):
        return self.preview.change_page(amount)

    def _commit_page_selection(self):
        self.preview.commit_page_selection()

    def _set_status(self, message, color):
        self.status_label.configure(text=message, fg=color)

    def _handle_printer_selection(self, _event=None):
        automatic = self._is_automated_selection()
        self.printer_label.configure(text="PRINTER TUJUAN")
        self.printer_settings.reset()
        self.printer_settings.set_printer_available(
            bool(self.printers and self.printer_var.get() and not automatic)
        )
        self.queue_panel.set_printer_available(self._can_print_with_current_mode())
        self._update_action_states()

    def _handle_printer_list_result(self, result):
        self.printer_controller.loading_printers = False
        if result.get("error"):
            self.status_label.configure(text=f"Gagal mendeteksi printer: {result['error']}", fg="#b42318")
            self._refresh_file_list()
            return
        previous_printer = self.printer_var.get()
        self.printers = result["printers"]
        self.printer_box["values"] = [PrintMode.AUTOMATED.value, *self.printers]
        if previous_printer == PrintMode.AUTOMATED.value:
            self.printer_var.set(PrintMode.AUTOMATED.value)
        elif previous_printer in self.printers:
            self.printer_var.set(previous_printer)
        else:
            self.printer_var.set(PrintMode.AUTOMATED.value)
        if self.printer_var.get() != previous_printer:
            self.printer_settings.reset()
        if not self.printers:
            self.status_label.configure(text="Tidak ada printer terdeteksi", fg="#b42318")
        self._handle_printer_selection()
        self._refresh_file_list()

    def _remove_selected(self):
        item = self.queue.selected_item
        if item is None:
            return True
        self._remove_item(item)
        return True

    def _remove_item(self, item):
        removed = self.queue.remove(item)
        if removed is None:
            return
        removed_index, item = removed
        self._refresh_file_list()
        self.preview.dispose_item(item)
        if self.queue.items:
            index = min(removed_index, len(self.queue.items) - 1)
            next_item = self.queue.select(index, mark_as_read=False)
            self._refresh_file_list()
            self.preview.show_item(next_item)
        else:
            self.preview.show_empty()
        self._update_action_states()
        self.status_label.configure(
            text=f"Dikeluarkan dari antrean: {item['nama_file']}", fg=MUTED
        )

    def _clear_all(self):
        removed_items = self.queue.clear()
        self._refresh_file_list()
        for item in removed_items:
            self.preview.dispose_item(item)
        self.preview.show_empty()
        self._update_action_states()
        self.status_label.configure(
            text=f"{len(removed_items)} file dihapus dari antrean.", fg=MUTED
        )

    def _print_selected(self):
        item = self.queue.selected_item
        if item is None:
            self.status_label.configure(text="Pilih file yang ingin dicetak", fg="#b54708")
            return True
        should_finish = self._print_item(item)
        if not should_finish:
            self._toolbar_print_item = item
        return should_finish

    def _print_item(self, item):
        try:
            print_options = self._selected_print_options()
        except ValueError as error:
            self.status_label.configure(text=str(error), fg="#b42318")
            return True
        printer = self.printer_var.get()
        automatic = self._is_automated_selection()
        if not automatic and not printer:
            self.status_label.configure(text="Pilih printer terlebih dahulu", fg="#b42318")
            return True
        if item.get("printing"):
            return True
        if item.get("loading") or not item.get("jalur"):
            self.status_label.configure(text="File masih disiapkan atau tidak dapat dicetak.", fg="#b54708")
            return True
        item["printing"] = True
        self.queue_panel.mark_item_printing(item, True)
        self._refresh_file_list()
        destination = "printer dari TOML" if automatic else printer
        self.status_label.configure(text=f"Mengantrekan {item['nama_file']} ke {destination}…", fg=ACCENT)
        self.printer_controller.submit(
            item, printer, item.get("page_selection"), print_options,
            PrintMode.AUTOMATED if automatic else PrintMode.MANUAL,
        )
        return False

    def _print_all(self):
        try:
            print_options = self._selected_print_options()
        except ValueError as error:
            self.status_label.configure(text=str(error), fg="#b42318")
            return True
        printer = self.printer_var.get()
        automatic = self._is_automated_selection()
        if not automatic and not printer:
            self.status_label.configure(text="Pilih printer terlebih dahulu", fg="#b42318")
            return True
        eligible = [item for item in self.queue.items
                    if item.get("jalur") and not item.get("loading") and not item.get("printing")]
        if not eligible:
            self.status_label.configure(text="Tidak ada file siap cetak di antrean.", fg="#b54708")
            return True
        self._print_all_items = {id(item) for item in eligible}
        for item in eligible:
            item["printing"] = True
            self.queue_panel.mark_item_printing(item, True)
            self.printer_controller.submit(item, printer, None, print_options,
                                           PrintMode.AUTOMATED if automatic else PrintMode.MANUAL)
        self._refresh_file_list()
        self.status_label.configure(text=f"{len(eligible)} file diantrekan untuk dicetak.", fg=ACCENT)
        return False

    def _selected_copies(self):
        value = self.copies_var.get().strip()
        try:
            copies = int(value)
        except ValueError as error:
            raise ValueError("Jumlah rangkap harus bilangan bulat antara 1 dan 999.") from error
        if not 1 <= copies <= 999:
            raise ValueError("Jumlah rangkap harus antara 1 dan 999.")
        return copies

    def _selected_print_options(self):
        return replace(self.printer_settings.options, copies=self._selected_copies())

    def _handle_print_result(self, event):
        item = event["item"]
        status = event["status"]
        if event.get("monitored"):
            cetak_log("info", f"[Print Inbox] Job untuk {item['nama_file']}: {status}")
        complete = event.get("monitored") or status in {"sent", "gagal", "printer_not_ready"}
        if complete:
            item["printing"] = False
            self.queue_panel.mark_item_printing(item, False)
            self._print_all_items.discard(id(item))
            if not self._print_all_items:
                self.queue_panel.finish_print_all()
            if self._toolbar_print_item is item:
                self.print_action.finish()
                self._toolbar_print_item = None
        self._refresh_file_list()

        if status == "printer_not_ready":
            self.status_label.configure(text="Printer belum siap", fg="#b42318")
        elif status == "gagal":
            self.status_label.configure(text=f"Gagal mencetak {item['nama_file']}: {event.get('reason', 'error')}",
                                        fg="#b42318")
        else:
            message, color = print_status_display(status)
            self.status_label.configure(text=f"{item['nama_file']}: {message}", fg=color)

