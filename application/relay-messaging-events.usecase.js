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
      [MessagingEvents.QR]: safe((qr) => notifier.notifyQr(qr)),
      [MessagingEvents.STATUS]: safe((status) => {
        logger.info(`Status: ${status}`);
        notifier.notifyStatus(status);
      }),
      [MessagingEvents.MESSAGE]: safe((message) => {
        console.log(message)
        if (message.isGroup) return;                          // abaikan grup
        if (!message.attachment && !message.attachmentFailed) return; // abaikan yang tanpa file'
        
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