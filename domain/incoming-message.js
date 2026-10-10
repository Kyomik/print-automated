export function createAttachment({ fileName, originalName = null, mimeType, data }) {
  return Object.freeze({ fileName, originalName, mimeType, size: data.length, data });
}

export function createIncomingMessage({
  id, from, author = null, isGroup = false, timestamp, type, body = '',
  attachment = null,
  attachmentFailed = false,
  attachmentRejected = false,
  attachmentError = null,
  attachmentWarnings = [],
  attachmentHash = null,
}) {
  return Object.freeze({
    id, from, author, isGroup, timestamp, type, body,
    attachment, attachmentFailed, attachmentRejected,
    attachmentError, attachmentWarnings, attachmentHash,
  });
}