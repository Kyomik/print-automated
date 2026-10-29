import { sleep } from './sleep.js';

export async function retry(fn, { attempts = 3, delaysMs = [1000, 4000], onRetry } = {}) {
  let lastError;
  for (let i = 0; i < attempts; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      if (i === attempts - 1) break;
      onRetry?.(error, i + 1);
      await sleep(delaysMs[i] ?? delaysMs.at(-1));
    }
  }
  throw lastError;
}

export function withTimeout(promise, ms, message = 'timeout') {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(message)), ms);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}