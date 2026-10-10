import { ClientEvents } from '../protocol.js';

export function createPrintController({ logger }) {
  return (socket) => {
    socket.on(ClientEvents.PRINT_RESULT, (data) => {
      logger.info(`Klien ${socket.id} melapor hasil cetak:`, data);
    });
  };
}