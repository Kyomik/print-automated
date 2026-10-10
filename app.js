import { env } from './config/env.js';
import { whatsappConfig } from './config/whatsapp.config.js';

import { createLogger } from './shared/logger.js';

import { SendTextMessage } from './application/send-text-message.usecase.js';
import { GetConnectionStatus } from './application/get-connection-status.usecase.js';
import { RelayMessagingEvents } from './application/relay-messaging-events.usecase.js';

import { SocketNotifier } from './interfaces/socket/socket.notifier.js';
import { createWhatsAppController } from './interfaces/socket/controllers/whatsapp.controller.js';
import { createPrintController } from './interfaces/socket/controllers/print.controller.js';

import { WwebjsMessagingAdapter } from './infrastructure/whatsapp/wwebjs-messaging.adapter.js';
import { createWwebjsClient } from './infrastructure/whatsapp/wwebjs-client.factory.js';
import { createWwebjsMessageMapper } from './infrastructure/whatsapp/wwebjs-message.mapper.js';
import { LocalSessionStore } from './infrastructure/whatsapp/local-session.store.js';
import { SocketServer } from './infrastructure/socket/socket.server.js';
import { TokenAuthenticator } from './infrastructure/socket/token.authenticator.js';
import { attachTerminalQrPrinter } from './infrastructure/terminal/terminal-qr.printer.js';
import { ProcessKiller } from './infrastructure/runtime/process-killer.js';
import { registerGracefulShutdown } from './infrastructure/runtime/graceful-shutdown.js';

import { inspectAttachment } from './security/index.js';

const appLogger = createLogger('App');

process.on('unhandledRejection', (err) => {
  appLogger.error('Unhandled rejection:', err?.message ?? err);
});

// ---- Infrastructure ----
const messaging = new WwebjsMessagingAdapter({
  createClient: () => createWwebjsClient(whatsappConfig),
  mapMessage: createWwebjsMessageMapper({
    logger: createLogger('WA Mapper'),
    inspectAttachment,
  }),
  sessionStore: new LocalSessionStore({
    sessionDir: whatsappConfig.sessionDir,
    logger: createLogger('Session'),
  }),
  processKiller: new ProcessKiller(),
  config: whatsappConfig,
  logger: createLogger('WhatsApp'),
});

const socketServer = new SocketServer({
  port: env.port,
  authenticator: new TokenAuthenticator(env.apiToken),
  maxPayloadBytes: env.maxPayloadBytes,
  logger: createLogger('Socket'),
});

// ---- Interfaces ----
const notifier = new SocketNotifier(socketServer);

// ---- Application ----
const sendTextMessage = new SendTextMessage({ messaging });
const getConnectionStatus = new GetConnectionStatus({ messaging });
const relay = new RelayMessagingEvents({ messaging, notifier, logger: createLogger('Relay') });

// ---- Run ----
socketServer.start([
  createWhatsAppController({ sendTextMessage, getConnectionStatus, logger: createLogger('WA Controller') }),
  createPrintController({ logger: createLogger('Print') }),
]);

relay.start(); // harus sebelum messaging.start() agar tidak ada event terlewat
if (env.printQrToTerminal) attachTerminalQrPrinter(messaging);

messaging.start().catch((err) => appLogger.error('WhatsApp gagal start:', err.message));

registerGracefulShutdown(
  [
    { name: 'WhatsApp', stop: () => messaging.stop() },
    { name: 'Socket', stop: () => socketServer.stop() },
  ],
  { logger: appLogger }
);