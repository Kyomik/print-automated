import path from 'node:path';
import { createAttachment, createIncomingMessage } from '../../domain/incoming-message.js';
import { retry, withTimeout } from '../../shared/retry.js';

const safeName = (name) =>
  path.basename(name ?? '').replace(/[^\w.\- ]/g, '_').slice(0, 100);

export function createWwebjsMessageMapper({ logger, inspectAttachment, downloadTimeoutMs = 60_000 }) {
  const download = (msg) =>
    retry(
      async () => {
        const media = await withTimeout(
            msg.downloadMedia(),
            downloadTimeoutMs,
            'unduhan melewati batas waktu'
        );
        if (!media) throw new Error('media tidak tersedia (kedaluwarsa atau belum tersinkron)');
        return media;
      },
      {
        onRetry: (error, n) =>
            logger.warn(`Unduh gagal (percobaan ${n}) untuk ${msg.id.id}: ${error.stack ?? error.message}`),
        }
    );

  return async function mapMessage(msg) {
    let attachment = null;
    let attachmentFailed = false;
    let attachmentRejected = false;
    let attachmentError = null;
    let attachmentWarnings = [];
    let attachmentHash = null;

    if (msg.hasMedia) {
      try {
        const media = await download(msg);
        const data = Buffer.from(media.data, 'base64');
        const verdict = await inspectAttachment({
          mimeType: media.mimetype,
          size: data.length,
          data,
        });

        attachmentHash = verdict.sha256;
        attachmentWarnings = verdict.warnings;

        if (verdict.ok) {
          attachment = createAttachment({
            fileName: `${msg.id.id}.${verdict.type.extensions[0]}`, // dibuat server
            originalName: safeName(media.filename),                 // hanya informasi
            mimeType: verdict.type.mimes[0],
            data,
          });
        } else {
          attachmentRejected = true;
          attachmentError = verdict.reason;
          logger.warn(`File dari ${msg.from} ditolak: ${verdict.reason} (sha256 ${verdict.sha256})`);
        }
      } catch (error) {
        attachmentFailed = true;
        attachmentError = error.message;
        logger.error(`Unduh menyerah (${msg.type}) dari ${msg.from}: ${error.message}`);
      }
    }

    return createIncomingMessage({
      id: msg.id._serialized,
      from: msg.from,
      author: msg.author ?? null,
      isGroup: msg.from.endsWith('@g.us'),
      timestamp: msg.timestamp,
      type: msg.type,
      body: msg.body ?? '',
      attachment,
      attachmentFailed,
      attachmentRejected,
      attachmentError,
      attachmentWarnings,
      attachmentHash,
    });
  };
}