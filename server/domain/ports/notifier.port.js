const notImplemented = (name) => {
  throw new Error(`${name}() belum diimplementasikan`);
};

/** Kontrak pemberi kabar ke pihak luar (client). */
export class NotifierPort {
  notifyQr(_qr) { notImplemented('notifyQr'); }
  notifyStatus(_status) { notImplemented('notifyStatus'); }
  notifyIncomingMessage(_message) { notImplemented('notifyIncomingMessage'); }
}