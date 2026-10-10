import { createHash, timingSafeEqual } from 'node:crypto';

const digest = (value) => createHash('sha256').update(value).digest();

export class TokenAuthenticator {
  #expected;

  constructor(expectedToken) {
    this.#expected = digest(expectedToken);
  }

  authenticate(token) {
    if (typeof token !== 'string') return false;
    return timingSafeEqual(digest(token), this.#expected); // aman dari timing attack
  }
}