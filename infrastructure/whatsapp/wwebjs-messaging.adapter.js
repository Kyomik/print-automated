import { ConnectionStatus } from '../../domain/connection-status.js';
import { DeliveryError, NotConnectedError } from '../../domain/errors.js';
import { MessagingEvents, MessagingPort } from '../../domain/ports/messaging.port.js';
import { sleep } from '../../shared/sleep.js';

const toChatId = (recipient) =>
  recipient.includes('@') ? recipient : `${recipient.replace(/\D/g, '')}@c.us`;

export class WwebjsMessagingAdapter extends MessagingPort {
  #createClient;
  #mapMessage;
  #sessionStore;
  #processKiller;
  #config;
  #logger;

  #client = null;
  #status = ConnectionStatus.DISCONNECTED;
  #stopped = false;
  #restarting = false;

  constructor({ createClient, mapMessage, sessionStore, processKiller, config, logger }) {
    super();
    this.#createClient = createClient;
    this.#mapMessage = mapMessage;
    this.#sessionStore = sessionStore;
    this.#processKiller = processKiller;
    this.#config = config;
    this.#logger = logger;
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
    await this.#teardown(this.#detach());
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
      await this.#killOrphanBrowsers();
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
        await this.#teardown(client);
        if (this.#stopped) return;

        this.#logger.info(`Mencoba lagi dalam ${this.#config.retryDelayMs / 1000} detik...`);
        await sleep(this.#config.retryDelayMs);
      }
    }
  }

  async #restart({ wipe }) {
    if (this.#restarting || this.#stopped) return;
    this.#restarting = true;

    try {
      await this.#teardown(this.#detach());
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

    client.on('message', guarded((msg) => {
        if (this.#shouldRelay(msg)) this.#relayMessage(msg);
    }));

    client.on('auth_failure', guarded((reason) => {
      this.#logger.error(`auth_failure: ${reason}`);
      this.#restartSafely({ wipe: true });
    }));

    client.on('disconnected', guarded((reason) => {
      this.#logger.info(`Terputus: ${reason}`);
      this.#setStatus(ConnectionStatus.DISCONNECTED);
      this.#restartSafely({ wipe: reason === 'LOGOUT' });
    }));

    return client;
  }

  async #relayMessage(msg) {
    try {
      this.emit(MessagingEvents.MESSAGE, await this.#mapMessage(msg));
    } catch (error) {
      this.#logger.error('Gagal memproses pesan masuk:', error.message);
    }
  }

  // ---------- Helpers ----------
  #shouldRelay(msg) {
    const isPrivate = msg.from.endsWith('@c.us') || msg.from.endsWith('@lid');
    return isPrivate && msg.hasMedia;
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

  #killOrphanBrowsers() {
    return this.#processKiller.killByCommandLine(this.#config.sessionDir);
  }

  // Satu-satunya tempat yang menutup browser
  async #teardown(client) {
    if (!client) return;

    client.removeAllListeners();
    await Promise.race([
      client.destroy().catch(() => {}),
      sleep(this.#config.shutdownTimeoutMs),
    ]);
    await sleep(500); // Windows melepas file lock
    await this.#killOrphanBrowsers();
  }
}