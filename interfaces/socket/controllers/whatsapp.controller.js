import { DomainError } from '../../../domain/errors.js';
import { ClientEvents } from '../protocol.js';

export function createWhatsAppController({ sendTextMessage, getConnectionStatus, logger }) {
  return (socket) => {
    socket.on(ClientEvents.SEND_TEXT, async (payload, ack) => {
      const reply = typeof ack === 'function' ? ack : () => {};
      try {
        await sendTextMessage.execute({
          recipient: payload?.nomorTujuan,
          text: payload?.isiPesan,
        });
        reply({ ok: true });
      } catch (error) {
        logger.warn(`Kirim pesan gagal: ${error.message}`);
        reply({
          ok: false,
          // detail internal tidak dibocorkan ke client
          error: error instanceof DomainError ? error.message : 'Kesalahan internal',
        });
      }
    });

    // Pull opsional: hanya status, QR tidak pernah ikut
    socket.on(ClientEvents.GET_STATUS, (ack) => {
      if (typeof ack === 'function') ack(getConnectionStatus.execute());
    });
  };
}