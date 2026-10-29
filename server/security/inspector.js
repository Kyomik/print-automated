import { createHash } from 'node:crypto';

/** Menjalankan check berurutan. Berhenti di block pertama; warn dikumpulkan. */
export function createInspector(checks) {
  return async function inspect(file) {
    const ctx = { file, type: null };
    const warnings = [];
    const sha256 = createHash('sha256').update(file.data).digest('hex');

    for (const check of checks) {
      const verdicts = [].concat((await check(ctx)) ?? []);
      for (const v of verdicts) {
        if (v.level === 'block') return { ok: false, reason: v.reason, warnings, sha256 };
        warnings.push(v.reason);
      }
    }
    return { ok: true, type: ctx.type, warnings, sha256 };
  };
}