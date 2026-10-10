import { Server } from 'socket.io';

export class SocketServer {
  #io = null;
  #port;
  #authenticator;
  #maxPayloadBytes;
  #logger;

  constructor({ port, authenticator, maxPayloadBytes, logger }) {
    this.#port = port;
    this.#authenticator = authenticator;
    this.#maxPayloadBytes = maxPayloadBytes;
    this.#logger = logger;
  }

  /** @param {Array<(socket) => void>} controllers */
  start(controllers = []) {
    // Client berupa program (bukan browser), jadi CORS tidak diperlukan
    this.#io = new Server(this.#port, { maxHttpBufferSize: this.#maxPayloadBytes });

    // Hanya koneksi dengan token valid yang boleh masuk
    this.#io.use((socket, next) => {
      const ok = this.#authenticator.authenticate(socket.handshake.auth?.token);
      next(ok ? undefined : new Error('unauthorized'));
    });

    this.#io.on('connection', (socket) => {
      this.#logger.info(`Klien terhubung: ${socket.id}`);
      socket.on('disconnect', () => this.#logger.info(`Klien terputus: ${socket.id}`));
      controllers.forEach((register) => register(socket));
    });

    this.#logger.info(`Server aktif di port ${this.#port}`);
  }

  /** Dikirim langsung ke semua klien yang terhubung saat ini (semuanya sudah terautentikasi). */
  emit(event, payload) {
    this.#io?.emit(event, payload);
  }

  stop() {
    return new Promise((resolve) => {
      if (!this.#io) return resolve();
      this.#io.close(() => resolve());
    });
  }
}