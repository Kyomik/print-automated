import path from 'node:path';
import { createAttachment, createIncomingMessage } from '../../domain/incoming-message.js';
import { retry, withTimeout } from '../../shared/retry.js';
import { downloadWwebjsMediaFallback } from './wwebjs-media-downloader.js';
import { WWEBJS_MEDIA_TYPES } from './wwebjs-media-types.js';

const safeName = (name) =>
  path.basename(name ?? '').replace(/[^\w.\- ]/g, '_').slice(0, 100);

const shouldRetryDownload = (error) => {
  const msg = String(error?.message ?? error ?? '');
  const fatal = [
    'Execution context was destroyed',
    'Target page, context or browser has been closed',
    'Page crashed',
    'Protocol error',
    'Session closed',
    'r: r',
  ];
  // Treat downloadMedia default failure as non-retriable.
  if (msg.includes('downloadMedia default gagal')) return false;
  return !fatal.some((v) => msg.includes(v));
};

function createMediaDownloader({ logger, downloadTimeoutMs }) {
  return (msg) =>
    retry(
      async () => {
        let media;
        try {
          media = await withTimeout(
            msg.downloadMedia(),
            downloadTimeoutMs,
            'unduhan melewati batas waktu'
          );
        } catch (err) {
          logger.warn(`downloadMedia default gagal (${err.message}), mencoba fallback ekstraksi...`);
          media = await downloadWwebjsMediaFallback(msg);
        }

        if (!media) media = await downloadWwebjsMediaFallback(msg);
        if (!media) throw new Error('media tidak tersedia (kedaluwarsa atau belum tersinkron)');
        return media;
      },
      {
        onRetry: (error, n) => {
          if (!shouldRetryDownload(error)) throw error;
          logger.warn(`Unduh gagal (percobaan ${n}) untuk ${msg.id?.id}: ${error.stack ?? error.message}`);
        },
      }
    );
}

export function createWwebjsMessageMapper({ logger, inspectAttachment, downloadTimeoutMs = 60_000 }) {
  const download = createMediaDownloader({ logger, downloadTimeoutMs });

  return async function mapMessage(msg) {
    // Defense in depth: group traffic and stickers must never be downloaded
    // or emitted if this mapper is called outside the normal adapter path.
    if (msg?.from?.endsWith('@g.us') || msg?.author || msg?.type === 'sticker') return null;

    let attachment = null;
    let attachmentFailed = false;
    let attachmentRejected = false;
    let attachmentError = null;
    let attachmentWarnings = [];
    let attachmentHash = null;

    if (msg.hasMedia || WWEBJS_MEDIA_TYPES.includes(msg.type)) {
      try {
        const media = await download(msg);
        const data = Buffer.from(media.data, 'base64');
        const verdict = await inspectAttachment({ mimeType: media.mimetype, size: data.length, data });

        attachmentHash = verdict.sha256;
        attachmentWarnings = verdict.warnings;

        if (verdict.ok) {
          attachment = createAttachment({
            fileName: `${msg.id?.id || Date.now()}.${verdict.type.extensions[0]}`,
            originalName: safeName(media.filename),
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
      id: msg.id?._serialized || msg.id?.$1 || msg.id?.id,
      from: msg.from,
      author: msg.author ?? null,
      isGroup: msg.from.endsWith('@g.us') || Boolean(msg.author),
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
