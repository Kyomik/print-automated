import pkg from 'whatsapp-web.js';

const { Client, LocalAuth } = pkg;

export function createWwebjsClient({ clientId, authPath, puppeteer }) {
  return new Client({
    authStrategy: new LocalAuth({ clientId, dataPath: authPath }),
    puppeteer,
  });
}