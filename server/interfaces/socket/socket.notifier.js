import { NotifierPort } from '../../domain/ports/notifier.port.js';
import { ServerEvents } from './protocol.js';

export class SocketNotifier extends NotifierPort {
  #server;
  #latestQr = null;

  constructor(socketServer) {
    super();
    this.#server = socketServer;
  }

  notifyQr(qr) {
    this.#latestQr = qr;
    this.#server.emit(ServerEvents.QR, { qr });
  }

  getLatestQr() {
    return this.#latestQr;
  }

  notifyStatus(status) {
    if (status !== 'qr') this.#latestQr = null;
    this.#server.emit(ServerEvents.STATUS, { status });
  }

  // Metadata dan file dikirim bersamaan; Buffer dikirim sebagai binary oleh Socket.IO
  notifyIncomingMessage(message) {
    const { attachment, ...meta } = message;
    this.#server.emit(ServerEvents.INCOMING, {
      message: meta,
      file: attachment && {
        name: attachment.fileName,
        originalName: attachment.originalName,
        mimeType: attachment.mimeType,
        size: attachment.size,
        data: attachment.data,
      },
    });
  }
}
