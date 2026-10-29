"""User-facing copy for printer and spooler states."""

PRINT_STATUS_TEXT = {
    "queued": ("Masuk antrean printer. Menunggu giliran cetak.", "#067647"),
    "queued_unknown": ("Perintah diterima. Status antrean printer belum dapat diperiksa.", "#b54708"),
    "sent": ("Dokumen berhasil dikirim ke printer. Silakan periksa hasil cetaknya.", "#067647"),
    "spooling": ("Dokumen sedang disiapkan oleh printer.", "#2563eb"),
    "printing": ("Dokumen sedang dicetak.", "#2563eb"),
    "printed": ("Pencetakan selesai.", "#067647"),
    "complete": ("Pencetakan selesai.", "#067647"),
    "finished": ("Job sudah tidak ada di antrean. Periksa apakah hasil cetak sudah keluar.", "#b54708"),
    "error": ("Printer mengalami kendala saat mencetak.", "#b42318"),
    "offline": ("Printer sedang offline. Periksa koneksi printer.", "#b42318"),
    "paperout": ("Kertas printer habis. Isi kertas lalu coba lagi.", "#b42318"),
    "deleted": ("Job cetak dibatalkan atau dihapus dari antrean.", "#b54708"),
    "timeout": ("Status cetak belum diketahui. Periksa printer sebelum mencoba lagi.", "#b54708"),
}


def print_status_display(status):
    return PRINT_STATUS_TEXT.get(status, (f"Status cetak: {status}", "#b54708"))
