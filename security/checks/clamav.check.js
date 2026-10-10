import { block } from '../verdict.js';

export function createClamavCheck(options) {
  return async ({ file }) => {
    try {
      const result = await scanBuffer(file.data, options);
      if (result.infected) return block(`virus terdeteksi (${result.signature})`);
    } catch {
      // fail closed: pemindai mati -> file ditolak, bukan diloloskan
      if (options.failClosed) return block('pemindai antivirus tidak tersedia');
    }
  };
}