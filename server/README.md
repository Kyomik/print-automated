# ILO Print Server

Server untuk produk ILO Print. Server menghubungkan WhatsApp ke desktop print client melalui Socket.IO: menerima pesan dan lampiran WhatsApp, meneruskan status koneksi serta QR login, dan menerima laporan hasil cetak dari client.

## Kebutuhan

- Node.js yang mendukung `import.meta.dirname` (Node.js 20.11 atau lebih baru)
- npm
- Browser Chromium yang kompatibel dengan `puppeteer-core` untuk WhatsApp Web
- Opsional: ClamAV jika pemindaian lampiran diaktifkan

## Menjalankan server

Dari folder `server`, pasang dependency dan siapkan konfigurasi:

```bash
npm install
```

Buat file `.env` di folder ini. Contoh nilai:

```dotenv
PORT=3000
API_TOKEN=ganti-dengan-token-rahasia-yang-sama-dengan-client
MAX_PAYLOAD_MB=50
ENABLE_CLAMAV=false
CLAMAV_HOST=127.0.0.1
CLAMAV_PORT=3310
CLAMAV_FAIL_CLOSED=false
```

Atur nilai `API_TOKEN` yang sama pada client. Jangan commit `.env` atau kredensial. Jalankan server:

```bash
node app.js
```

Saat mulai, server membuka koneksi WhatsApp Web. Ikuti QR yang ditampilkan di terminal untuk menghubungkan akun. Sesi disimpan lokal di `.wwebjs_auth/` agar login tidak perlu diulang setiap kali server dijalankan. Simpan folder itu dengan aman dan jangan bagikan atau commit.

## Konfigurasi

| Variabel | Fungsi | Default |
| --- | --- | --- |
| `PORT` | Port Socket.IO server | `3000` |
| `API_TOKEN` | Token autentikasi client; wajib diisi | — |
| `MAX_PAYLOAD_MB` | Batas ukuran payload dalam MB | `50` |
| `ENABLE_CLAMAV` | Mengaktifkan pemindaian ClamAV (`true`/`false`) | `false` |
| `CLAMAV_HOST` | Host ClamAV | `127.0.0.1` |
| `CLAMAV_PORT` | Port ClamAV | `3310` |
| `CLAMAV_FAIL_CLOSED` | Menolak lampiran jika pemindaian gagal (`true`/`false`) | `false` |

Server melakukan pemeriksaan tipe dan ukuran lampiran; pemindaian antivirus dapat memakai ClamAV. Jika ClamAV diaktifkan, pastikan servicenya tersedia sesuai host dan port konfigurasi.

## Integrasi dengan client

Isi `SERVER_URL` dan `API_TOKEN` pada konfigurasi client dengan alamat server dan token yang sama. Server dan client menggunakan event Socket.IO berikut:

| Arah | Event | Fungsi |
| --- | --- | --- |
| Server → client | `whatsapp-qr` | Mengirim QR WhatsApp terbaru |
| Server → client | `whatsapp-status` | Mengirim status koneksi WhatsApp |
| Server → client | `whatsapp-incoming` | Meneruskan pesan, lampiran, atau kesalahan pemrosesan |
| Client → server | `kirim_pesan_wa` | Mengirim pesan teks WhatsApp |
| Client → server | `minta_status_wa` | Meminta status koneksi |
| Client → server | `minta_qr_wa` | Meminta QR terbaru |
| Client → server | `respons_cetak` | Melaporkan hasil atau status pencetakan |

Nama event didefinisikan di `interfaces/socket/protocol.js`. Payload pesan dan laporan cetak mengikuti kontrak yang dijelaskan pada README client; jaga kedua sisi tetap selaras saat mengubah kontrak.

## Struktur kode

- `app.js` — composition root yang merangkai adapter, use case, controller, dan memulai layanan.
- `application/` — use case untuk pesan, status, dan relay event WhatsApp.
- `domain/` — model, error, serta port aplikasi.
- `interfaces/socket/` — Socket.IO notifier, controller, dan definisi event.
- `infrastructure/` — adapter WhatsApp, Socket.IO, sesi lokal, dan lifecycle proses.
- `config/` — pembacaan variabel lingkungan dan konfigurasi WhatsApp.
- `security/` — validasi dan pemeriksaan lampiran.
- `shared/` — logger, retry, dan utilitas bersama.

## Pengembangan

`package.json` belum mendefinisikan test suite; perintah `npm test` saat ini hanya placeholder. Perubahan protokol sebaiknya diperbarui dan ditinjau bersama implementasi client.
