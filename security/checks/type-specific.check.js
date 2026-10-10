// Menjalankan check milik jenis file yang terdeteksi
export async function checkTypeSpecific(ctx) {
  const results = [];
  for (const check of ctx.type.checks) {
    results.push(await check(ctx));
  }
  return results.flat().filter(Boolean);
}