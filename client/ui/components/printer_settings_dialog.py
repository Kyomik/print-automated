"""Dialog for choosing paper source and size reported by a printer driver."""

from collections import Counter
import tkinter as tk
from tkinter import ttk

from domain.printer import PrinterCapabilities, PrintOptions
from ui.theme import BG, MUTED, PANEL


class PrinterSettingsDialog:
    def __init__(self, parent, printer_name, initial_options: PrintOptions, on_save):
        self.window = tk.Toplevel(parent)
        self.window.title("Pengaturan kertas")
        self.window.transient(parent)
        self.window.grab_set()
        self.window.resizable(False, False)
        self.window.configure(bg=BG)
        self.on_save = on_save
        self.initial_options = initial_options or PrintOptions()
        self.capabilities = None
        self._source_ids = {}
        self._paper_ids = {}

        card = tk.Frame(self.window, bg=PANEL, padx=24, pady=22)
        card.pack(fill="both", expand=True, padx=16, pady=16)
        tk.Label(card, text="Pengaturan kertas", bg=PANEL, fg="#172033",
                 font=("Segoe UI", 15, "bold")).pack(anchor="w")
        tk.Label(card, text=printer_name, bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 16))

        self.source_var = tk.StringVar(master=self.window, value="Bawaan printer")
        self.paper_var = tk.StringVar(master=self.window, value="Bawaan printer")
        self.source_box = self._choice(card, "Sumber kertas", self.source_var)
        self.paper_box = self._choice(card, "Ukuran kertas", self.paper_var)
        self.help_label = tk.Label(
            card, text="Memuat pilihan dari driver printer…", bg=PANEL, fg=MUTED,
            font=("Segoe UI", 9), anchor="w", wraplength=360, justify="left",
        )
        self.help_label.pack(fill="x", pady=(14, 4))

        actions = tk.Frame(card, bg=PANEL)
        actions.pack(fill="x", pady=(16, 0))
        self.save_button = ttk.Button(actions, text="Terapkan", style="Accent.TButton",
                                      command=self._save, state="disabled")
        self.save_button.pack(side="right")
        ttk.Button(actions, text="Batal", command=self.window.destroy).pack(side="right", padx=(0, 8))
        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)
        self.window.update_idletasks()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - self.window.winfo_width()) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - self.window.winfo_height()) // 2)
        self.window.geometry(f"+{x}+{y}")

    @staticmethod
    def _choice(parent, label, variable):
        tk.Label(parent, text=label, bg=PANEL, fg="#344054",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8, 5))
        box = ttk.Combobox(parent, textvariable=variable, state="disabled", width=48)
        box.pack(fill="x")
        return box

    def set_capabilities(self, capabilities: PrinterCapabilities | None, error=None):
        if not self.window.winfo_exists():
            return
        if error:
            self.help_label.configure(
                text=f"Pilihan kertas tidak dapat dibaca ({error}). Pencetakan tetap memakai bawaan printer."
            )
            self.save_button.configure(state="normal")
            return

        self.capabilities = capabilities
        sources = capabilities.sources
        papers = capabilities.paper_sizes
        self._source_ids = self._populate(
            self.source_box, self.source_var, sources, self.initial_options.source_id
        )
        self._paper_ids = self._populate(
            self.paper_box, self.paper_var, papers, self.initial_options.paper_id
        )
        available = []
        if sources:
            available.append(f"{len(sources)} sumber kertas")
        if papers:
            available.append(f"{len(papers)} ukuran")
        self.help_label.configure(
            text=(" · ".join(available) + " tersedia dari driver printer."
                  if available else "Driver tidak melaporkan pilihan tambahan. Bawaan printer akan digunakan.")
        )
        self.save_button.configure(state="normal")

    @staticmethod
    def _populate(box, variable, choices, selected_id):
        name_counts = Counter(choice.name for choice in choices)
        labels_by_name = {
            choice.id: (
                f"{choice.name} (ID {choice.id})"
                if name_counts[choice.name] > 1 else choice.name
            )
            for choice in choices
        }
        ids_by_label = {label: choice_id for choice_id, label in labels_by_name.items()}
        labels = ["Bawaan printer"] + list(ids_by_label)
        box.configure(values=labels, state="readonly" if choices else "disabled")
        variable.set(labels_by_name.get(selected_id, "Bawaan printer"))
        return ids_by_label

    def _save(self):
        if self.capabilities is None:
            options = self.initial_options
        else:
            options = PrintOptions(
                source_id=self._source_ids.get(self.source_var.get()),
                paper_id=self._paper_ids.get(self.paper_var.get()),
            )
        self.on_save(options)
        self.window.destroy()
