import { EventEmitter } from 'node:events';

export const MessagingEvents = Object.freeze({
  QR: 'qr',                // (qrString)
  STATUS: 'status',        // (ConnectionStatus), hanya saat berubah
  MESSAGE: 'message',      // (IncomingMessage)
});

const notImplemented = (name) => {
  throw new Error(`${name}() belum diimplementasikan`);
};

/** Kontrak mesin pesan. Implementasi memancarkan MessagingEvents. */
export class MessagingPort extends EventEmitter {
  async start() { notImplemented('start'); }
  async stop() { notImplemented('stop'); }
  getStatus() { notImplemented('getStatus'); }
  async sendText(_recipient, _text) { notImplemented('sendText'); }
}