"""Queue list presentation and row interactions for the print inbox."""

import tkinter as tk
from tkinter import ttk

from ui.components.busy_button import BusyButton
from ui.theme import ACCENT, MUTED, NAV, PANEL

_QUEUE_NAME_LIMIT = 15
_QUEUE_PRINT_BUTTON_WIDTH = 10


class QueuePanel:
    def __init__(self, parent, on_select, on_remove, on_print,
                 on_clear_all, on_print_all):
        self.on_select = on_select
        self.on_remove = on_remove
        self.on_print = on_print
        self.on_clear_all = on_clear_all
        self.on_print_all = on_print_all
        self.rows = {}
        self.items = []
        self.selected_index = None
        self.printer_available = False
        self._scrollable = False

        self.frame = tk.Frame(parent, bg=PANEL, padx=18, pady=18,
                              highlightbackground="#e2e8f0", highlightthickness=1)
        self.frame.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        self.frame.rowconfigure(2, weight=1)
        self.frame.columnconfigure(0, weight=1)

        header = tk.Frame(self.frame, bg=PANEL)
        header.grid(row=0, column=0, sticky="ew")
        tk.Label(header, text="Antrean file", font=("Segoe UI", 14, "bold"),
                 bg=PANEL, fg=NAV).pack(side="left")
        self.count_label = tk.Label(header, text="0 file", font=("Segoe UI", 9, "bold"),
                                    bg="#eaf1ff", fg=ACCENT, padx=9, pady=4)
        self.count_label.pack(side="right")
        actions = tk.Frame(self.frame, bg=PANEL)
        actions.grid(row=1, column=0, sticky="ew", pady=(8, 12))
        self.clear_all_button = ttk.Button(actions)
        self.clear_all_action = BusyButton(
            self.clear_all_button, "\U0001F5D1 Hapus semua", self.on_clear_all,
            "Menghapus",
        )
        self.clear_all_button.pack(side="left")
        self.print_all_button = ttk.Button(actions)
        self.print_all_action = BusyButton(
            self.print_all_button, "\U0001F5A8 Print all", self.on_print_all,
            "Mencetak antrean",
        )
        self.print_all_button.pack(side="right")

        self.list_frame = tk.Frame(self.frame, bg="#f8fafc", highlightbackground="#e2e8f0",
                                   highlightthickness=1)
        self.list_frame.grid(row=2, column=0, sticky="nsew")
        self.canvas = tk.Canvas(self.list_frame, bg="#f8fafc", highlightthickness=0,
                                borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self.list_frame, orient="vertical", command=self.canvas.yview)
        self.rows_frame = tk.Frame(self.canvas, bg="#f8fafc")
        self.rows_frame.columnconfigure(0, weight=1)
        self.rows_window = self.canvas.create_window((0, 0), window=self.rows_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.scrollbar.state(["disabled"])
        self.rows_frame.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_rows)
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.bind(sequence, self._on_mousewheel, add="+")
            self.rows_frame.bind(sequence, self._on_mousewheel, add="+")
        self.empty_label = tk.Label(self.frame, text="File baru akan muncul di antrean ini.",
                                    font=("Segoe UI", 9), bg=PANEL, fg=MUTED)
        self.empty_label.grid(row=3, column=0, sticky="w", pady=(12, 0))

    def _update_scroll_region(self, _event=None, reset_to_top=False):
        if not self.items:
            self._scrollable = False
            self.canvas.configure(scrollregion=(0, 0, 0, 0))
            self.canvas.yview_moveto(0)
            self.scrollbar.state(["disabled"])
            return
        bounds = self.canvas.bbox("all")
        self.canvas.configure(scrollregion=bounds or (0, 0, 0, 0))
        content_height = (bounds[3] - bounds[1]) if bounds else 0
        self._scrollable = content_height > self.canvas.winfo_height()
        if not self._scrollable:
            self.canvas.yview_moveto(0)
            self.scrollbar.state(["disabled"])
        else:
            self.scrollbar.state(["!disabled"])
            if reset_to_top:
                self.canvas.yview_moveto(0)

    def _resize_rows(self, event):
        self.canvas.itemconfigure(self.rows_window, width=event.width)
        self._update_scroll_region()

    def _on_mousewheel(self, event):
        if not self._scrollable:
            return "break"
        if getattr(event, "num", None) == 4:
            amount = -1
        elif getattr(event, "num", None) == 5:
            amount = 1
        else:
            delta = getattr(event, "delta", 0)
            amount = -int(delta / 120) if delta else 0
            if amount == 0 and delta:
                amount = -1 if delta > 0 else 1
        if amount:
            self.canvas.yview_scroll(amount, "units")
        return "break"

    def _create_row(self, item):
        row = tk.Frame(self.rows_frame, padx=0, pady=0, highlightthickness=0)
        marker = tk.Frame(row, width=4, height=38)
        marker.pack_propagate(False)
        marker.pack(side="left")
        details = tk.Frame(row, padx=9, pady=8)
        details.pack(side="left", fill="both", expand=True)
        name = tk.Label(details, text=self._short_name(item["nama_file"]),
                        width=_QUEUE_NAME_LIMIT + 3, font=("Segoe UI", 9, "bold"),
                        anchor="w")
        name.pack(fill="x")
        status = tk.Label(details, font=("Segoe UI", 8), anchor="w")
        status.pack(fill="x", pady=(2, 0))
        remove = tk.Button(
            row, font=("Segoe UI", 11), fg=MUTED, activebackground="#fee4e2",
            activeforeground="#b42318", relief="flat", borderwidth=0,
            cursor="hand2", width=3,
        )
        remove_action = BusyButton(
            remove, "\u00d7", lambda row_item=item: self.on_remove(row_item),
            "Menghapus",
        )
        remove.pack(side="right", padx=(6, 0))
        print_button = ttk.Button(row, width=_QUEUE_PRINT_BUTTON_WIDTH)
        print_action = BusyButton(
            print_button, "\U0001F5A8 Print",
            lambda row_item=item: self.on_print(row_item), "Mencetak",
        )
        print_button.pack(side="right", padx=(4, 0))
        widgets = (row, marker, details, name, status, remove)
        row_data = {"frame": row, "marker": marker, "name": name,
                    "status": status, "remove": remove,
                    "print": print_button, "print_action": print_action,
                    "remove_action": remove_action, "widgets": widgets,
                    "style_signature": None, "packed": False}
        for widget in widgets:
            widget.bind("<Button-1>", lambda _event, row_item=item: self._select_item(row_item))
            for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                widget.bind(sequence, self._on_mousewheel, add="+")
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            print_button.bind(sequence, self._on_mousewheel, add="+")
        self.rows[id(item)] = row_data
        return row_data

    def _style_row(self, row_data, item, selected):
        loading = item.get("loading")
        printing = item.get("printing")
        can_print = (self.printer_available and bool(item.get("jalur"))
                     and not loading and not printing)
        signature = (
            item["nama_file"], selected, item.get("is_new"), loading, printing, can_print
        )
        if row_data["style_signature"] == signature:
            return
        row_data["style_signature"] = signature
        bg = "#eaf1ff" if selected else "#f8fafc"
        for widget in row_data["widgets"]:
            widget.configure(bg=bg)
        row_data["name"].configure(text=self._short_name(item["nama_file"]), fg=NAV)
        row_data["marker"].configure(bg=ACCENT if item.get("is_new") else bg)
        row_data["status"].configure(text="Memuat" if loading else "Siap",
                                     fg=ACCENT if loading else "#067647")
        row_data["print_action"].set_enabled(can_print)

    @staticmethod
    def _short_name(name):
        name = str(name)
        if len(name) <= _QUEUE_NAME_LIMIT:
            return name
        return f"{name[:_QUEUE_NAME_LIMIT]}..."

    def render(self, items, selected_index):
        was_empty = not self.items
        active_ids = {id(item) for item in items}
        for item_id in tuple(self.rows):
            if item_id not in active_ids:
                row_data = self.rows.pop(item_id)
                row_data["print_action"].finish()
                row_data["remove_action"].finish()
                row_data["frame"].destroy()
        self.items = items
        self.count_label.configure(text=f"{len(items)} file")

        # Create every missing row before using its widget as a pack anchor.
        for index, item in enumerate(items):
            row_data = self.rows.get(id(item)) or self._create_row(item)
            self._style_row(row_data, item, index == selected_index)
            if not row_data["packed"]:
                next_row = next(
                    (self.rows[id(next_item)]["frame"]
                     for next_item in items[index + 1:]
                     if id(next_item) in self.rows and self.rows[id(next_item)]["packed"]),
                    None,
                )
                if next_row is None:
                    row_data["frame"].pack(fill="x", padx=3, pady=2)
                else:
                    row_data["frame"].pack(fill="x", padx=3, pady=2, before=next_row)
                row_data["packed"] = True

        if items:
            self.empty_label.grid_remove()
        else:
            self.empty_label.grid()
        has_items = bool(items)
        self.clear_all_action.set_enabled(has_items)
        has_printable_items = any(
            item.get("jalur") and not item.get("loading") and not item.get("printing")
            for item in items
        )
        self.print_all_action.set_enabled(has_printable_items and self.printer_available)
        self.selected_index = selected_index
        self._update_scroll_region(reset_to_top=was_empty and bool(items))

    def set_printer_available(self, available):
        self.printer_available = available
        has_printable_items = any(
            item.get("jalur") and not item.get("loading") and not item.get("printing")
            for item in self.items
        )
        self.print_all_action.set_enabled(has_printable_items and available)

    def mark_item_printing(self, item, printing):
        row_data = self.rows.get(id(item))
        if row_data is None:
            return
        if printing:
            row_data["print_action"].begin()
        else:
            row_data["print_action"].finish()

    def finish_print_all(self):
        self.print_all_action.finish()

    def _select_item(self, item):
        index = next((i for i, candidate in enumerate(self.items) if candidate is item), None)
        if index is not None:
            self.on_select(index)
