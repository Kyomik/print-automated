import fs from 'node:fs/promises';
import { sleep } from '../../shared/sleep.js';

export class LocalSessionStore {
  #sessionDir;
  #logger;

  constructor({ sessionDir, logger }) {
    this.#sessionDir = sessionDir;
    this.#logger = logger;
  }

  async wipe() {
    await sleep(1500); // Windows: beri waktu file dilepas
    try {
      await fs.rm(this.#sessionDir, {
        recursive: true,
        force: true,
        maxRetries: 10,
        retryDelay: 500,
      });
      this.#logger.info('Folder sesi dihapus.');
    } catch (err) {
      this.#logger.error('Gagal menghapus sesi:', err.code, err.message);
    }
  }
}