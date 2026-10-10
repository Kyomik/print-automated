// Satu-satunya tempat nama event. Ubah di sini jika kontrak dengan client berubah.
export const ServerEvents = Object.freeze({
  QR: 'whatsapp-qr',
  STATUS: 'whatsapp-status',
  INCOMING: 'whatsapp-incoming',
});

export const ClientEvents = Object.freeze({
  SEND_TEXT: 'kirim_pesan_wa',
  GET_STATUS: 'minta_status_wa',
  PRINT_RESULT: 'respons_cetak',
});