/**
 * @typedef {Object} CheckContext
 * @property {{ data: Buffer, size: number, mimeType?: string }} file
 * @property {FileType | null} type
 *
 * @typedef {(ctx: CheckContext) => (Verdict | Verdict[] | void | Promise<Verdict | Verdict[] | void>)} Check
 *
 * @typedef {Object} FileType
 * @property {string} name
 * @property {readonly string[]} extensions  ekstensi pertama dipakai sebagai nama file hasil
 * @property {readonly string[]} mimes       MIME pertama dipakai sebagai MIME hasil
 * @property {number} maxBytes
 * @property {(data: Buffer) => boolean} matches  cocokkan magic bytes
 * @property {readonly Check[]} checks
 */

const fail = (name, msg) => {
  throw new Error(`FileType "${name ?? '?'}": ${msg}`);
};

/** @returns {FileType} */
export function defineFileType(spec) {
  const { name, extensions, mimes, maxBytes, matches, checks = [] } = spec;

  if (!name) fail(name, 'name wajib');
  if (!Array.isArray(extensions) || extensions.length === 0) fail(name, 'extensions wajib');
  if (!Array.isArray(mimes) || mimes.length === 0) fail(name, 'mimes wajib');
  if (!Number.isFinite(maxBytes) || maxBytes <= 0) fail(name, 'maxBytes harus angka positif');
  if (typeof matches !== 'function') fail(name, 'matches harus function');
  if (!checks.every((c) => typeof c === 'function')) fail(name, 'checks harus berisi function');

  return Object.freeze({
    name,
    extensions: Object.freeze([...extensions]),
    mimes: Object.freeze([...mimes]),
    maxBytes,
    matches,
    checks: Object.freeze([...checks]),
  });
}

// Pembantu pencocok magic bytes, dipakai file-types/*
export const startsWith = (...bytes) => (buf) => bytes.every((b, i) => buf[i] === b);
export const asciiAt = (buf, offset, text) =>
  buf.subarray(offset, offset + text.length).toString('latin1') === text;