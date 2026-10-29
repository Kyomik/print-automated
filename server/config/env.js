import 'dotenv/config';

const required = (name) => {
  const value = process.env[name];
  if (!value) throw new Error(`Environment variable ${name} wajib diisi`);
  return value;
};

export const env = Object.freeze({
  port: Number(process.env.PORT ?? 3000),
  apiToken: required('API_TOKEN'),
  maxPayloadBytes: Number(process.env.MAX_PAYLOAD_MB ?? 50) * 1024 * 1024,
  clamav: {
    enabled: process.env.ENABLE_CLAMAV === 'true',
    host: process.env.CLAMAV_HOST ?? '127.0.0.1',
    port: Number(process.env.CLAMAV_PORT ?? 3310),
    timeoutMs: 30_000,
    failClosed: process.env.CLAMAV_FAIL_CLOSED === 'true',
  },
});
