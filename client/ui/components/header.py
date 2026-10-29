import tkinter as tk

from ui.theme import ACCENT, BG, MUTED


def build_header(parent, reconnect):
    header = tk.Frame(parent, bg=BG)
    header.pack(fill="x", padx=28, pady=(24, 18))
    top = tk.Frame(header, bg=BG)
    top.pack(fill="x")
    tk.Label(top, text="DOKUMEN MASUK", font=("Segoe UI", 9, "bold"),
             bg=BG, fg=ACCENT).pack(side="left")
    status = tk.Label(top, text="Menghubungkan ke server…", font=("Segoe UI", 9, "bold"),
                      bg=BG, fg=MUTED)
    status.pack(side="right", padx=(12, 0))
    button = tk.Button(top, text="Sambungkan ulang", command=reconnect,
                       font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                       bg=ACCENT, fg="#ffffff", activebackground="#1d4ed8",
                       activeforeground="#ffffff", padx=12, pady=7,
                       disabledforeground="#ffffff")
    button.pack(side="right", padx=(12, 0))
    return status, button
    tk.Label(header, text="Tinjau lalu cetak", font=("Segoe UI", 23, "bold"),
             bg=BG, fg=NAV).pack(anchor="w", pady=(3, 2))
    tk.Label(header, text="File dari WhatsApp akan muncul di sini sebelum dikirim ke printer.",
             font=("Segoe UI", 10), bg=BG, fg=MUTED).pack(anchor="w")
