# WhatsApp Print Client

The client receives attachments from the Socket.IO server, previews them in a
desktop inbox, and submits the selected file to a Windows printer.

## Layers

- `application/print_workflow.py` coordinates receiving, printing, and reporting.
- `domain/ports.py` defines the interfaces the application depends on, while
  `domain/printer.py` contains typed printer capabilities and print options.
- `services/` contains infrastructure adapters for files, Socket.IO, Windows
  printer jobs (`PrinterService`) and driver capability discovery
  (`WindowsPrinterCapabilities`), document conversion, and rendered-page
  analysis (`DocumentAnalyzer`).
- `services/preview_strategies/` contains format-specific preview strategies
  selected by `PreviewStrategyFactory`; `PreviewRenderer` owns only the active
  preview session lifecycle. Text-only and unsupported-format previews are
  shared independently from the Word strategy.
- `domain/document_analysis.py` defines typed page measurements, physical page
  dimensions, and color-content results. The analyzer owns color classification
  and converts available source measurements to millimeters; the preview
  renderer only supplies the image and raw geometry.
- `services/document_page_inspector.py` inspects each page for automated print
  planning. `application/automated_printing.py` coordinates the use case;
  `application/automated_print_planner.py` resolves TOML rules against driver
  capabilities and groups adjacent pages with matching printer settings.
  `application/print_workflow.py` delegates to this use case.
- `services/printer_strategies/` selects a print strategy by file extension.
  Each format strategy is registered in `default_print_strategies()`; adding a
  format adds a strategy and a registration, without editing format-selection
  conditionals in the printer service.
- `ui/print_inbox.py` wires the window and coordinates its event loop.
  `ui/print_queue_controller.py` owns incoming files and selection;
  `ui/preview_controller.py` owns preview state and rendering interactions.
  Dedicated controllers also handle attachment work, print jobs, and paper
  settings. The composition root injects the Windows capability adapter into
  the printer service.
- `ui/components/` contains the header, queue, preview, and print toolbar widgets.
- `ui/theme.py` and `ui/print_status.py` centralize shared visual styling and status copy.
- `index.py` wires the adapters and application workflow together.

The print strategies use the Strategy pattern: images and PDFs are rasterized
and sent directly through a Windows GDI printer device context; DOCX files are
converted with Microsoft Word COM running invisibly, then printed through the
same GDI path. Printing no longer uses Windows `printto` file associations, so
PDF and image applications are not opened. DOCX printing and faithful DOCX
preview require Microsoft Word to be installed. Without it, the preview shows
extracted text and printing reports a clear Word availability error.

## Setup

From this directory, install the dependencies and start the client:

```bat
env\Scripts\python.exe -m pip install -r requirements.txt
env\Scripts\python.exe index.py
```

## Build aplikasi Windows

Pastikan Python Windows tersedia dengan dukungan Tcl/Tk. Pasang dependensi
proyek terlebih dahulu (termasuk PyInstaller):

```powershell
env\Scripts\python.exe -m pip install -r requirements.txt
```

Jalankan skrip build dari PowerShell di folder proyek:

```powershell
.\build_exe.ps1
```

Skrip menggunakan Python dari `env\Scripts\python.exe` jika tersedia; jika
tidak, skrip memakai perintah `python` yang ada di `PATH`. Skrip menjalankan
PyInstaller dalam mode `onedir` tanpa jendela konsol, lalu menyalin
`.env.example` dan `automated-print.toml` ke folder hasil. Aplikasi yang sudah
dibangun tersedia di `dist\IloPrintClient\IloPrintClient.exe`. Distribusikan
seluruh folder `dist\IloPrintClient`, bukan file EXE saja. Sebelum menjalankan
aplikasi, salin `.env.example` menjadi `.env` di folder tersebut dan isi
konfigurasinya.

Konfigurasi PyInstaller untuk build manual juga tersedia di
`IloPrintClient.spec`.

Application logs are written to
`%LOCALAPPDATA%\IloPrintClient\logs\client.log`; rotated log files are kept in
the same folder. Logging calls go through `ApplicationLogger` and the `LogSink`
port. `FileLogSink` is the configured adapter; a network-backed sink can replace
it in the composition root without changing the logging call sites.

The inbox keeps incoming files in the configured `FOLDER_SIMPAN` directory.
Choose a file from the left queue, inspect its preview, choose **Automated** or
a Windows printer from the destination list, then click **Cetak file terpilih**.
Atur **Rangkap** di samping daftar printer tujuan untuk memilih 1-999 salinan.
Nilai ini berlaku untuk **Cetak dokumen**, **Print all**, dan tombol cetak pada setiap file di antrean.
Printer discovery runs automatically when the app opens. PDF previews support page navigation and display
color-content classification and physical page dimensions when the file
provides enough information. PDFs and Word previews report page dimensions;
images need DPI metadata for a physical-size estimate.

Pilihan **Automated** pada dropdown printer tujuan menjadi pilihan awal. Memilih
printer Windows lain mengaktifkan pencetakan manual. Atur `automated-print.toml` dengan
aturan di bawah `[hitam_putih]` dan `[warna]`; nama subbagian adalah ukuran
kertas. Ukuran halaman dikenali dari dimensinya, termasuk ukuran standar seperti
`A4` (210 × 297 mm) dan `Folio` (216 × 330 mm), meskipun file tidak menyimpan
nama ukuran. Setiap kombinasi warna dan ukuran tetap perlu satu aturan TOML.
Setiap aturan wajib memuat `nama_print`; `sumber_kertas` opsional.
Contohnya:

```toml
[hitam_putih."A4 210x297"]
nama_print = "Brother DCP-L2540DW series"

[warna."A4 210x297"]
nama_print = "Printer warna kantor"
```

Saat **Automated** dipilih, client menganalisis isi warna dan ukuran tiap
halaman, lalu mengirim halaman dengan aturan yang cocok. `sumber_kertas` bersifat
opsional: jika tidak ditulis, driver memilih tray berdasarkan konfigurasi printer.
Jika perlu memaksa tray tertentu, isi dengan nama yang ditampilkan di
**Pengaturan kertas**. Ukuran kertas tetap mengikuti aturan TOML. Memilih printer
Windows lain menggunakan opsi **Pengaturan kertas** secara manual.

## Socket.IO event contract

| Direction | Event | Behavior |
| --- | --- | --- |
| Server to client | `whatsapp-qr` | Displays a WhatsApp QR in a desktop window. |
| Server to client | `whatsapp-status` | Logs connection status. |
| Server to client | `whatsapp-incoming` | Adds a file or processing error to the client. |
| Client to server | `kirim_pesan_wa` | Sends `nomorTujuan` and `isiPesan`. |
| Client to server | `minta_status_wa` | Requests a WhatsApp status snapshot. |
| Client to server | `minta_qr_wa` | Requests the current QR. |
| Client to server | `respons_cetak` | Reports queue, print, and failure status. |
