import { warn } from '../verdict.js';

// Klaim MIME dari pengirim tidak konsisten dengan isi: indikator lemah, jadi hanya peringatan
export function checkMime({ file, type }) {
  const declared = (file.mimeType ?? '').split(';')[0].trim().toLowerCase();
  if (!type.mimes.includes(declared)) return warn('tipe yang diklaim tidak cocok dengan isi file');
}