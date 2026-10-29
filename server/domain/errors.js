export class DomainError extends Error {
  constructor(message, options) {
    super(message, options);
    this.name = new.target.name;
  }
}

export class ValidationError extends DomainError {}

export class NotConnectedError extends DomainError {
  constructor() {
    super('WhatsApp belum terhubung');
  }
}

export class DeliveryError extends DomainError {
  constructor(options) {
    super('Gagal mengirim pesan', options);
  }
}