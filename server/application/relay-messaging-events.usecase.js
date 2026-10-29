import { MessagingEvents } from '../domain/ports/messaging.port.js';

/** Meneruskan event dari mesin pesan ke notifier. Hanya meneruskan, tidak menyimpan state. */
export class RelayMessagingEvents {
  #messaging;
  #handlers;

  constructor({ messaging, notifier, logger }) {
    this.#messaging = messaging;

    const safe = (fn) => (payload) => {
      try {
        fn(payload);
      } catch (error) {
        logger.error('Gagal meneruskan event:', error.message);
      }
    };

    this.#handlers = {
      [MessagingEvents.QR]: safe((qr) => {
        logger.info('QR WhatsApp dibuat; dikirim ke client.');
        notifier.notifyQr(qr);
      }),
      [MessagingEvents.STATUS]: safe((status) => {
        logger.info(`Status: ${status}`);
        notifier.notifyStatus(status);
      }),
      [MessagingEvents.MESSAGE]: safe((message) => {
        if (message.isGroup) return; // abaikan grup
        // Hanya abaikan jika benar-benar pesan teks biasa tanpa file
        if (!message.attachment && !message.attachmentFailed && !message.attachmentRejected) return;
        
        logger.info(`Pesan masuk dari ${message.from} (${message.type})`);
        notifier.notifyIncomingMessage(message);
      }),
    };
  }

  start() {
    for (const [event, handler] of Object.entries(this.#handlers)) {
      this.#messaging.on(event, handler);
    }
  }

  stop() {
    for (const [event, handler] of Object.entries(this.#handlers)) {
      this.#messaging.off(event, handler);
    }
  }
}
