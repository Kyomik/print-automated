import { ConnectionStatus } from '../../domain/connection-status.js';
import { DeliveryError, NotConnectedError } from '../../domain/errors.js';
import { MessagingEvents, MessagingPort } from '../../domain/ports/messaging.port.js';
import { sleep } from '../../shared/sleep.js';
import { createWwebjsBrowserLifecycle } from './wwebjs-browser-lifecycle.js';
import { WWEBJS_MEDIA_TYPES } from './wwebjs-media-types.js';

const toChatId = (recipient) =>
  recipient.includes('@') ? recipient : `${recipient.replace(/\D/g, '')}@c.us`;

const isFatalBrowserError = (error) => {
  const msg = String(error?.message ?? error ?? '');
  const fatal = [
    'Execution context was destroyed',
    'Target page, context or browser has been closed',
    'Page crashed',
    'Protocol error',
    'Session closed',
    'r: r',
  ];

  return fatal.some((v) => msg.includes(v));
};

export class WwebjsMessagingAdapter extends MessagingPort {
  #createClient;
  #mapMessage;
  #sessionStore;
  #config;
  #logger;
  #browserLifecycle;

  #client = null;
  #status = ConnectionStatus.DISCONNECTED;
  #stopped = false;
  #restarting = false;

  constructor({ createClient, mapMessage, sessionStore, processKiller, config, logger }) {
    super();
    this.#createClient = createClient;
    this.#mapMessage = mapMessage;
    this.#sessionStore = sessionStore;
    this.#config = config;
    this.#logger = logger;
    this.#browserLifecycle = createWwebjsBrowserLifecycle({
      sessionDir: config.sessionDir,
      processKiller,
      config,
    });
  }

  // ---------- MessagingPort ----------

  getStatus() {
    return this.#status;
  }

  async start() {
    this.#stopped = false;
    await this.#connectWithRetry();
  }

  async stop() {
    this.#stopped = true;
    await this.#browserLifecycle.teardown(this.#detach());
    this.#setStatus(ConnectionStatus.DISCONNECTED);
    this.#logger.info('Dihentikan.');
  }

  async sendText(recipient, text) {
    if (!this.#client || this.#status !== ConnectionStatus.CONNECTED) {
      throw new NotConnectedError();
    }
    try {
      const sent = await this.#client.sendMessage(toChatId(recipient), text);
      return { messageId: sent.id._serialized };
    } catch (cause) {
      this.#logger.error('sendMessage gagal:', cause.message);
      throw new DeliveryError({ cause });
    }
  }

  // ---------- Lifecycle ----------

  async #connectWithRetry() {
    while (!this.#stopped) {
      this.#setStatus(ConnectionStatus.CONNECTING);
      await this.#browserLifecycle.killOrphanBrowsers();
      if (this.#stopped) return;

      const client = this.#buildClient();
      this.#client = client;
      this.#logger.info('Puppeteer diinisialisasi...');

      try {
        await client.initialize();
        return;
      } catch (err) {
        this.#logger.error('Gagal initialize:', err.message);
        if (this.#client === client) this.#client = null;
        await this.#browserLifecycle.teardown(client);
        if (this.#stopped) return;

        this.#logger.info(`Mencoba lagi dalam ${this.#config.retryDelayMs / 1000} detik...`);
        await sleep(this.#config.retryDelayMs);
      }
    }
  }

  async #restart({ wipe, browserAlreadyClosing = false }) {
    if (this.#restarting || this.#stopped) return;
    this.#restarting = true;

    try {
      await this.#browserLifecycle.teardown(this.#detach(), { browserAlreadyClosing });
      if (wipe) await this.#sessionStore.wipe();
    } finally {
      this.#restarting = false;
    }

    if (!this.#stopped) await this.#connectWithRetry(); // client baru -> QR baru
  }

  #restartSafely(options) {
    this.#restart(options).catch((err) => this.#logger.error('Restart gagal:', err.message));
  }

  // ---------- Client wiring ----------

  #buildClient() {
    const client = this.#createClient();

    // Abaikan event dari client lama / saat sudah dihentikan
    const guarded = (handler) => (...args) => {
      if (!this.#stopped && this.#client === client) handler(...args);
    };

    client.on('qr', guarded((qr) => {
      this.#setStatus(ConnectionStatus.QR);
      this.emit(MessagingEvents.QR, qr);
    }));

    client.on('authenticated', guarded(() => {
      this.#setStatus(ConnectionStatus.CONNECTING); // QR sudah discan / sesi dipulihkan
    }));

    client.on('ready', guarded(() => {
      this.#setStatus(ConnectionStatus.CONNECTED);
    }));

    client.on('message_create', guarded((msg) => {
      // Recent WhatsApp Web builds may expose the serialized message ID as `$1`.
      // whatsapp-web.js still reads `_serialized` inside downloadMedia().
      if (msg?.id && msg.id._serialized == null && typeof msg.id.$1 === 'string') {
        msg.id._serialized = msg.id.$1;
      }
      // Filter first: chat teks dan pesan grup tidak diproses maupun dicetak.
      if (this.#shouldRelay(msg)) {
        this.#relayMessage(msg).catch((error) => {
          this.#logger.error('Relay message gagal:', error?.message ?? error);
        });
      }
    }));

    client.on('auth_failure', guarded((reason) => {
      this.#logger.error(`auth_failure: ${reason}`);
      this.#restartSafely({ wipe: true });
    }));

    client.on('disconnected', guarded((reason) => {
      this.#logger.info(`Terputus: ${reason}`);
      this.#setStatus(ConnectionStatus.DISCONNECTED);
      // whatsapp-web.js calls destroy() immediately after emitting this event.
      // Wait for that close instead of destroying the same browser a second time.
      this.#restartSafely({ wipe: reason === 'LOGOUT', browserAlreadyClosing: true });
    }));

    return client;
  }

  async #relayMessage(msg) {
    try {
      const mapped = await this.#mapMessage(msg);

      if (!mapped) return;

      this.emit(MessagingEvents.MESSAGE, mapped);

      if (mapped.attachmentFailed) {
        this.#logger.warn(`Attachment gagal diproses dari ${mapped.from}: ${mapped.attachmentError}`);
      }

      return mapped;
    } catch (error) {
      this.#logger.error('Relay message gagal:', error?.message ?? error);

      if (isFatalBrowserError(error)) {
        this.#logger.warn('Browser/WhatsApp context rusak. Restart client WA...');
        this.#restartSafely({ wipe: false });
        return;
      }

      throw error;
    }
  }

  // ---------- Helpers ----------
  #shouldRelay(msg) {
    if (!msg || !msg.from) return false;

    // Group messages normally use @g.us. `author` is also present on
    // whatsapp-web.js messages sent by a group participant.
    if (msg.from.endsWith('@g.us') || msg.author) return false;

    // Stickers are media too, so exclude them before download/mapping.
    if (msg.type === 'sticker') return false;

    // Jika pesan berasal dari diri sendiri (self-chat), izinkan jika targetnya adalah diri sendiri
    if (msg.fromMe) {
      const myId = this.#client?.info?.wid?._serialized;
      const isSelfChat = msg.to === myId || msg.to === msg.from;
      if (!isSelfChat) return false;
    }

    const isPrivate =
      msg.from.endsWith('@c.us') ||
      msg.from.endsWith('@lid') ||
      msg.from.endsWith('@s.whatsapp.net');
    if (!isPrivate) return false;

    // file/media WA bisa datang dengan tipe seperti image, video, document, audio, sticker
    return msg.hasMedia || WWEBJS_MEDIA_TYPES.includes(msg.type);
  }

  #setStatus(next) {
    if (this.#status === next) return; // hanya perubahan yang dipancarkan
    this.#status = next;
    this.emit(MessagingEvents.STATUS, next);
  }

  #detach() {
    const client = this.#client;
    this.#client = null;
    return client;
  }
}
