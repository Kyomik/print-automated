import qrcode from 'qrcode-terminal';
import { MessagingEvents } from '../../domain/ports/messaging.port.js';

// Observer opsional: mencetak QR di terminal server
export function attachTerminalQrPrinter(messaging) {
  messaging.on(MessagingEvents.QR, (qr) => {
    console.log('\n=== SILAKAN SCAN QR CODE DI BAWAH INI ===');
    qrcode.generate(qr, { small: true });
  });
}