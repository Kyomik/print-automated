import { unzipSync } from 'fflate';
import { defineFileType, startsWith } from '../file-type.js';
import { block, warn } from '../verdict.js';

const MB = 1024 * 1024;
const MAX_ENTRIES = 2000;
const MAX_UNCOMPRESSED = 200 * MB;

function listEntries(data) {
  const entries = [];
  // filter -> false: hanya membaca daftar isi, tidak mengekstrak (aman dari zip bomb)
  unzipSync(data, {
    filter: (e) => {
      entries.push({ name: e.name, size: e.originalSize });
      return false;
    },
  });
  return entries;
}

function checkDocxContent({ file }) {
  let entries;
  try {
    entries = listEntries(file.data);
  } catch {
    return block('struktur dokumen rusak');
  }

  const names = entries.map((e) => e.name);
  const total = entries.reduce((sum, e) => sum + e.size, 0);
  const verdicts = [];

  if (entries.length > MAX_ENTRIES || total > MAX_UNCOMPRESSED) {
    return block('dokumen terlalu besar setelah dibuka');
  }
  if (!names.includes('word/document.xml')) return block('bukan dokumen Word');
  if (names.some((n) => /vbaProject\.bin$/i.test(n))) verdicts.push(block('dokumen berisi macro'));
  if (names.some((n) => /^word\/(embeddings|activeX)\//i.test(n))) verdicts.push(warn('dokumen berisi objek tertanam'));

  return verdicts;
}

export const docx = defineFileType({
  name: 'docx',
  extensions: ['docx'],
  mimes: ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
  maxBytes: 20 * MB,
  matches: startsWith(0x50, 0x4b, 0x03, 0x04), // ZIP
  checks: [checkDocxContent],
});