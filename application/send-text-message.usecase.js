import { ValidationError } from '../domain/errors.js';

export class SendTextMessage {
  #messaging;

  constructor({ messaging }) {
    this.#messaging = messaging;
  }

  async execute({ recipient, text }) {
    if (typeof recipient !== 'string' || !recipient.trim()) {
      throw new ValidationError('Nomor tujuan wajib diisi');
    }
    if (typeof text !== 'string' || !text.trim()) {
      throw new ValidationError('Isi pesan wajib diisi');
    }
    return this.#messaging.sendText(recipient.trim(), text);
  }
}