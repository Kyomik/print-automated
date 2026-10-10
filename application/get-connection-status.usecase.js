export class GetConnectionStatus {
  #messaging;

  constructor({ messaging }) {
    this.#messaging = messaging;
  }

  execute() {
    return { status: this.#messaging.getStatus() };
  }
}