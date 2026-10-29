"""Coordinate printer paper settings without putting driver work in the window."""

import tkinter as tk

from domain.printer import PrintOptions
from ui.components.printer_settings_dialog import PrinterSettingsDialog


class PrinterSettingsController:
    def __init__(self, parent, print_controller, selected_printer):
        self._parent = parent
        self._print_controller = print_controller
        self._selected_printer = selected_printer
        self._settings_button = None
        self._dialog = None
        self._printer = None
        self._options = PrintOptions()

    @property
    def options(self) -> PrintOptions:
        return self._options

    def set_button(self, button):
        self._settings_button = button
        self.set_printer_available(bool(self._selected_printer()))
        self._update_button()

    def set_printer_available(self, available):
        if self._settings_button is not None:
            self._settings_button.configure(state="normal" if available else "disabled")

    def reset(self, _event=None):
        self._options = PrintOptions()
        self._printer = None
        if self._dialog is not None:
            try:
                self._dialog.window.destroy()
            except tk.TclError:
                pass
            self._dialog = None
        self._update_button()

    def open(self):
        printer = self._selected_printer()
        if not printer:
            return
        self._printer = printer
        self._dialog = PrinterSettingsDialog(
            self._parent, printer, self._options, self._save_options
        )
        self._print_controller.load_capabilities(printer)

    def handle_capabilities_result(self, result):
        if result.get("printer") != self._printer or self._dialog is None:
            return
        try:
            if self._dialog.window.winfo_exists():
                self._dialog.set_capabilities(
                    result.get("capabilities"), result.get("error")
                )
        except tk.TclError:
            self._dialog = None

    def _save_options(self, options):
        self._options = options
        self._update_button()

    def _update_button(self):
        if self._settings_button is None:
            return
        label = (
            "⚙ Pengaturan kertas: Diatur"
            if self._options.has_overrides else "⚙ Pengaturan kertas"
        )
        self._settings_button.configure(text=label)
