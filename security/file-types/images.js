import { defineFileType, startsWith, asciiAt } from '../file-type.js';

const MB = 1024 * 1024;

export const jpeg = defineFileType({
  name: 'jpeg', extensions: ['jpg'], mimes: ['image/jpeg'], maxBytes: 15 * MB,
  matches: startsWith(0xff, 0xd8, 0xff),
});

export const png = defineFileType({
  name: 'png', extensions: ['png'], mimes: ['image/png'], maxBytes: 15 * MB,
  matches: startsWith(0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a),
});

export const webp = defineFileType({
  name: 'webp', extensions: ['webp'], mimes: ['image/webp'], maxBytes: 15 * MB,
  matches: (buf) => asciiAt(buf, 0, 'RIFF') && asciiAt(buf, 8, 'WEBP'),
});