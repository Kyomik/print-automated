import { ALLOWED_FILE_TYPES } from '../file-types/index.js';
import { block } from '../verdict.js';

export function detectType(ctx) {
  ctx.type = ALLOWED_FILE_TYPES.find((t) => t.matches(ctx.file.data)) ?? null;
  if (!ctx.type) return block('jenis file tidak diizinkan');
}