import { block } from '../verdict.js';

export function checkSize({ file, type }) {
  if (file.size > type.maxBytes) return block('ukuran file melebihi batas');
}