import tkinter as tk
from tkinter import ttk

from domain.automated_printing import PrintMode
from ui.components.busy_button import BusyButton
from ui.theme import ACCENT, MUTED, PANEL


def build_print_toolbar(parent, open_paper_settings, remove_selected, print_selected):
    footer = tk.Frame(parent, bg=PANEL, padx=22, pady=14,
                      highlightbackground="#e2e8f0", highlightthickness=1)
    footer.pack(fill="x", padx=28, pady=(0, 24))
    footer.columnconfigure(1, weight=1)
    printer_label = tk.Label(footer, text="PRINTER TUJUAN", font=("Segoe UI", 8, "bold"),
                             bg=PANEL, fg=MUTED)
    printer_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
    printer_var = tk.StringVar(master=parent, value=PrintMode.AUTOMATED.value)
    printer_box = ttk.Combobox(footer, textvariable=printer_var,
                               state="readonly", width=40,
                               values=[PrintMode.AUTOMATED.value])
    printer_box.configure(state="disabled")
    printer_box.grid(row=0, column=1, columnspan=3, sticky="ew")
    copies_style = ttk.Style(parent)
    copies_style.configure(
        "Copies.TSpinbox",
        padding=(8, 5),
        font=("Segoe UI", 11, "bold"),
        fieldbackground="#ffffff",
        foreground="#0f172a",
        arrowsize=13,
    )
    copies_card = tk.Frame(
        footer, bg="#f8fafc", padx=10, pady=5,
        highlightbackground="#cbd5e1", highlightthickness=1,
    )
    copies_card.grid(row=0, column=4, columnspan=2, sticky="ew", padx=(14, 0))
    copies_card.columnconfigure(1, weight=1)
    copies_label = tk.Label(
        copies_card, text="RANGKAP", font=("Segoe UI", 8, "bold"),
        bg="#f8fafc", fg=MUTED,
    )
    copies_label.grid(row=0, column=0, sticky="w", padx=(0, 8))
    copies_var = tk.StringVar(master=parent, value="1")
    copies_input = ttk.Spinbox(
        copies_card, from_=1, to=999, textvariable=copies_var,
        width=4, justify="center", style="Copies.TSpinbox",
    )
    copies_input.grid(row=0, column=1, sticky="e")
    settings_button = ttk.Button(footer, text="\u2699 Pengaturan kertas", command=open_paper_settings)
    settings_button.grid(row=1, column=1, sticky="w", pady=(10, 0))
    remove_button = ttk.Button(footer)
    remove_action = BusyButton(remove_button, "\U0001F5D1 Hapus", remove_selected,
                               "Menghapus")
    remove_action.set_enabled(False)
    remove_button.grid(row=1, column=4, padx=(0, 8), pady=(10, 0))
    print_button = ttk.Button(footer, style="Accent.TButton")
    print_action = BusyButton(print_button, "\U0001F5A8 Cetak dokumen", print_selected,
                              "Mengirim cetakan")
    print_action.set_enabled(False)
    print_button.grid(row=1, column=5, pady=(10, 0))
    status_label = tk.Label(footer, text="Pilih dokumen untuk memulai.",
                            bg=PANEL, fg=MUTED, font=("Segoe UI", 9), anchor="w")
    status_label.grid(row=2, column=0, columnspan=6, sticky="ew", pady=(12, 0))
    return {"printer_var": printer_var, "printer_box": printer_box,
            "printer_label": printer_label,
            "print_button": print_button, "print_action": print_action,
            "remove_action": remove_action,
            "settings_button": settings_button, "status_label": status_label,
            "copies_var": copies_var, "copies_input": copies_input}
