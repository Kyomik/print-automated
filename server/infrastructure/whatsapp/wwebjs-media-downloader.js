/**
 * Fallback unduhan untuk WhatsApp Web versi yang gagal dilayani oleh
 * Message.downloadMedia() dari whatsapp-web.js.
 */
export async function downloadWwebjsMediaFallback(msg) {
  const page = msg.client?.pupPage;
  if (!page) throw new Error('Puppeteer page tidak tersedia');

  const serializedId = msg.id?._serialized || msg.id?.$1;
  const rawId = msg.id?.id;

  const result = await page.evaluate(
    async ({ serializedId, rawId }) => {
      const Collections = window.require('WAWebCollections');
      const MsgCollection = Collections?.Msg;
      if (!MsgCollection) throw new Error('WAWebCollections.Msg tidak ditemukan');

      let msgModel = null;
      if (serializedId) {
        try { msgModel = MsgCollection.get(serializedId); } catch {}
      }
      if (!msgModel && rawId) {
        const all = typeof MsgCollection.getModelsArray === 'function' ? MsgCollection.getModelsArray() : [];
        msgModel = all.find(
          (x) => x?.id?.id === rawId || x?.id?._serialized === serializedId || x?.id?.$1 === serializedId
        );
      }
      if (!msgModel && serializedId && typeof MsgCollection.getMessagesById === 'function') {
        try {
          const res = await MsgCollection.getMessagesById([serializedId]);
          msgModel = res?.messages?.[0];
        } catch {}
      }

      if (!msgModel) {
        throw new Error(`Pesan ${rawId || serializedId} tidak ditemukan di memori WA`);
      }

      // The current WhatsApp Web bundle may expose this ID as `$1`; its
      // internal media downloader still expects `_serialized`.
      if (msgModel.id && msgModel.id._serialized == null && typeof msgModel.id.$1 === 'string') {
        msgModel.id._serialized = msgModel.id.$1;
      }

      if (msgModel.mediaData && msgModel.mediaData.mediaStage !== 'RESOLVED') {
        try {
          if (typeof msgModel.downloadMedia === 'function') {
            await msgModel.downloadMedia({ downloadEvenIfExpensive: true, rmrReason: 1 });
          }
        } catch {}
      }

      if (msgModel.mediaData?.renderableUrl) {
        try {
          const res = await fetch(msgModel.mediaData.renderableUrl);
          if (res.ok) {
            const blob = await res.blob();
            const buffer = await blob.arrayBuffer();
            const base64Data = await window.WWebJS.arrayBufferToBase64Async(buffer);
            return {
              data: base64Data,
              mimetype: msgModel.mimetype || msgModel.mediaData?.mimetype || 'application/octet-stream',
              filename: msgModel.filename || msgModel.mediaData?.filename,
              filesize: msgModel.size || msgModel.mediaData?.size || buffer.byteLength,
            };
          }
        } catch {}
      }

      const downloadManagerModule = window.require('WAWebDownloadManager');
      const downloadManager = downloadManagerModule?.downloadManager;
      if (!downloadManager || typeof downloadManager.downloadAndMaybeDecrypt !== 'function') {
        throw new Error('WAWebDownloadManager tidak ditemukan');
      }

      const directPath = msgModel.directPath || msgModel.mediaData?.directPath;
      const encFilehash = msgModel.encFilehash || msgModel.mediaData?.encFilehash;
      const filehash = msgModel.filehash || msgModel.mediaData?.filehash;
      const mediaKey = msgModel.mediaKey || msgModel.mediaData?.mediaKey;
      const mediaKeyTimestamp = msgModel.mediaKeyTimestamp || msgModel.mediaData?.mediaKeyTimestamp;
      const type = msgModel.type || msgModel.mediaData?.type;

      if (!directPath || !mediaKey) {
        throw new Error('Informasi directPath/mediaKey tidak lengkap pada pesan');
      }

      const mockQpl = {
        addAnnotations: function () { return this; },
        addPoint: function () { return this; },
      };

      const decryptedMedia = await downloadManager.downloadAndMaybeDecrypt({
        directPath,
        encFilehash,
        filehash,
        mediaKey,
        mediaKeyTimestamp,
        type,
        // whatsapp-web.js 1.34.7 omits this field. Recent WhatsApp Web
        // builds require it to validate uncached media; otherwise the
        // downloader sees application/octet-stream and throws `t: t`.
        mimetype: msgModel.mimetype || msgModel.mediaData?.mimetype,
        signal: new AbortController().signal,
        downloadQpl: mockQpl,
      });

      const data = await window.WWebJS.arrayBufferToBase64Async(decryptedMedia);

      return {
        data,
        mimetype: msgModel.mimetype || msgModel.mediaData?.mimetype || 'application/octet-stream',
        filename: msgModel.filename || msgModel.mediaData?.filename,
        filesize: msgModel.size || msgModel.mediaData?.size,
      };
    },
    { serializedId, rawId }
  );

  if (!result || !result.data) {
    throw new Error('Gagal mengekstrak media');
  }

  return result;
}
