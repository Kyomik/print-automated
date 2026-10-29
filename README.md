# ILO Print

ILO Print adalah satu produk yang terdiri dari server WhatsApp dan aplikasi desktop Windows untuk menerima serta mencetak lampiran.

## Struktur repo

- [`server/`](server/) — server Node.js, integrasi WhatsApp Web, dan Socket.IO.
- [`client/`](client/) — aplikasi desktop Windows untuk antrean, pratinjau, dan pencetakan dokumen.
- [`.gitignore`](.gitignore) — mengecualikan konfigurasi rahasia, sesi lokal, dependency, cache, dan hasil build.

## Menjalankan server

Pasang Node.js dan npm, lalu dari folder repo jalankan:

```powershell
cd server
npm install
Copy-Item .env.example .env
```

Isi `server/.env`, terutama `API_TOKEN`. Jalankan server:

```powershell
node app.js
```

Server menampilkan QR WhatsApp di terminal saat pertama kali perlu menghubungkan akun. Detail konfigurasi ada di [`server/README.md`](server/README.md).

## Menjalankan client

Ikuti panduan setup di [`client/README.md`](client/README.md). Atur `SERVER_URL` ke alamat server dan gunakan `API_TOKEN` yang sama dengan server. Untuk membuat aplikasi Windows, jalankan `client/build_exe.ps1` dari PowerShell.

## Kontrak komunikasi

Server dan client berkomunikasi melalui Socket.IO. Daftar event server ada di [`server/interfaces/socket/protocol.js`](server/interfaces/socket/protocol.js); tabel event dan dokumentasi fitur client ada di README masing-masing. Perbarui kedua sisi saat kontrak event berubah.

## Data lokal

File `.env`, sesi autentikasi WhatsApp, folder `simulation`, dependency, cache, dan hasil build bersifat lokal dan tidak dilacak oleh Git.
