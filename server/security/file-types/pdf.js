import { defineFileType, asciiAt } from '../file-type.js';
import { block, warn } from '../verdict.js';

const MB = 1024 * 1024;

// Pola -> verdict. Menambah aturan = menambah satu baris.
const RULES = [
  { pattern: /\/Launch/,       verdict: block('PDF dapat meluncurkan program (/Launch)') },
  { pattern: /\/JavaScript/,   verdict: warn('PDF berisi JavaScript') },
  { pattern: /\/JS\b/,         verdict: warn('PDF berisi JavaScript') },
  { pattern: /\/EmbeddedFile/, verdict: warn('PDF membawa file tertanam') },
  { pattern: /\/RichMedia/,    verdict: warn('PDF berisi rich media') },
];

function checkPdfContent({ file }) {
  const text = file.data
    .toString('latin1')
    // bongkar penyamaran nama seperti /#4AavaScript
    .replace(/#([0-9a-fA-F]{2})/g, (_, hex) => String.fromCharCode(parseInt(hex, 16)));

  const found = RULES.filter((r) => r.pattern.test(text)).map((r) => r.verdict);
  return [...new Map(found.map((v) => [v.reason, v])).values()]; // buang duplikat (/JavaScript dan /JS)
}

export const pdf = defineFileType({
  name: 'pdf',
  extensions: ['pdf'],
  mimes: ['application/pdf'],
  maxBytes: 20 * MB,
  matches: (buf) => {
    if (!buf || buf.length < 5) return false;
    return buf.subarray(0, 1024).toString('latin1').includes('%PDF-');
  },
  checks: [checkPdfContent],
});