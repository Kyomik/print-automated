import tkinter as tk
from tkinter import ttk

from ui.components.busy_button import BusyButton
from ui.theme import ACCENT, MUTED, NAV, PANEL


def build_preview_panel(parent, change_page, commit_page_selection):
    panel = tk.Frame(parent, bg=PANEL, padx=22, pady=20,
                     highlightbackground="#e2e8f0", highlightthickness=1)
    panel.grid(row=0, column=1, sticky="nsew")
    panel.rowconfigure(1, weight=1)
    panel.columnconfigure(0, weight=1)
    info = tk.Frame(panel, bg=PANEL)
    info.grid(row=0, column=0, sticky="ew", pady=(0, 16))
    info.columnconfigure(0, weight=1)
    tk.Label(info, text="PRATINJAU", font=("Segoe UI", 9, "bold"),
             bg=PANEL, fg=ACCENT).grid(row=0, column=0, sticky="w", pady=(0, 6))
    name_label = tk.Label(info, text="Belum ada dokumen dipilih",
                          font=("Segoe UI", 15, "bold"), bg=PANEL,
                          fg=NAV, anchor="w")
    name_label.grid(row=1, column=0, sticky="ew")
    meta_label = tk.Label(info, text="Pilih file dari antrean untuk melihat tampilannya.",
                          font=("Segoe UI", 9), bg=PANEL, fg=MUTED, anchor="w")
    meta_label.grid(row=2, column=0, sticky="ew", pady=(4, 0))
    pager = tk.Frame(info, bg=PANEL)
    pager.grid(row=1, column=1, rowspan=2, padx=(12, 0))
    prev_button = ttk.Button(pager, text="‹", width=3, command=lambda: change_page(-1))
    prev_action = BusyButton(prev_button, "‹", lambda: change_page(-1), "Memuat")
    prev_action.set_enabled(False)
    prev_button.pack(side="left")
    page_var = tk.StringVar(value="")
    page_entry = ttk.Entry(pager, textvariable=page_var, width=6, justify="center")
    page_entry.pack(side="left", padx=(6, 0))
    page_entry.bind("<Return>", lambda _event: commit_page_selection())
    page_entry.bind("<FocusOut>", lambda _event: commit_page_selection())
    page_total = tk.Label(pager, text="", font=("Segoe UI", 9, "bold"),
                          bg=PANEL, fg=MUTED)
    page_total.pack(side="left", padx=(2, 6))
    next_button = ttk.Button(pager, text="›", width=3, command=lambda: change_page(1))
    next_action = BusyButton(next_button, "›", lambda: change_page(1), "Memuat")
    next_action.set_enabled(False)
    next_button.pack(side="left", padx=(4, 0))

    preview_area = tk.Frame(panel, bg="#f1f5f9",
                            highlightbackground="#e2e8f0", highlightthickness=1)
    preview_area.grid(row=1, column=0, sticky="nsew")
    preview_area.rowconfigure(0, weight=1)
    preview_area.columnconfigure(0, weight=1)
    preview_label = tk.Label(preview_area, text="Preview dokumen akan tampil di sini",
                             bg="#f1f5f9", fg=MUTED, font=("Segoe UI", 11))
    preview_label.grid(row=0, column=0, sticky="nsew")
    return {"preview_area": preview_area, "preview_label": preview_label,
            "name_label": name_label, "meta_label": meta_label,
            "page_entry": page_entry, "page_var": page_var,
            "page_total": page_total, "prev_page_action": prev_action,
            "next_page_action": next_action}
