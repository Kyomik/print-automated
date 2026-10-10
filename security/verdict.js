/**
 * @typedef {{ level: 'block' | 'warn', reason: string }} Verdict
 * block = file ditolak, warn = file tetap diteruskan dengan peringatan
 */
export const block = (reason) => ({ level: 'block', reason });
export const warn = (reason) => ({ level: 'warn', reason });