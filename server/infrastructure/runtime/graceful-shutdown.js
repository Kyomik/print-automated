/** @param {Array<{ name: string, stop: () => Promise<void> | void }>} services  dijalankan berurutan */
export function registerGracefulShutdown(services, { logger }) {
  let running = false;

  const run = async (signal) => {
    if (running) return;
    running = true;
    logger.info(`${signal} diterima, mematikan layanan...`);

    await Promise.allSettled(
      services.map(async ({ name, stop }) => {
        try {
          await stop();
          logger.info(`${name} dimatikan.`);
        } catch (error) {
          logger.error(`${name} gagal dimatikan:`, error?.message ?? error);
        }
      })
    );

    process.exit(0);
  };

  for (const signal of ['SIGINT', 'SIGTERM']) {
    process.on(signal, () => run(signal));
  }
}