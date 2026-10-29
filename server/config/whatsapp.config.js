import path from 'node:path';

const clientId = 'sesi-utama';
const authPath = path.resolve(import.meta.dirname, '..', '..', '.wwebjs_auth'); // <server>/.wwebjs_auth

export const whatsappConfig = Object.freeze({
  clientId,
  authPath,
  sessionDir: path.join(authPath, `session-${clientId}`),
  retryDelayMs: 15_000,
  shutdownTimeoutMs: 2_000,
  puppeteer: {
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dns-over-https',
      '--disable-dev-shm-usage',
    ],
  },
});