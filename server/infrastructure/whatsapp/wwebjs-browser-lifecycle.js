import fs from 'node:fs/promises';
import path from 'node:path';
import { sleep } from '../../shared/sleep.js';

/** Menangani penutupan Chromium dan pembersihan profil WhatsApp Web. */
export function createWwebjsBrowserLifecycle({ sessionDir, processKiller, config }) {
  async function killOrphanBrowsers() {
    await processKiller.killByCommandLine(sessionDir);
    // Hapus file lock sisa agar Chrome tidak menganggap profil masih terkunci.
    for (const lockFile of ['SingletonLock', 'SingletonCookie', 'SingletonSocket']) {
      await fs.unlink(path.join(sessionDir, lockFile)).catch(() => {});
    }
  }

  async function waitForBrowserClose(browser) {
    if (!browser?.isConnected?.()) return;

    await new Promise((resolve) => {
      let timer;
      const finish = () => {
        clearTimeout(timer);
        browser.off('disconnected', finish);
        resolve();
      };

      browser.once('disconnected', finish);
      if (!browser.isConnected()) finish();
      else timer = setTimeout(finish, config.browserCloseTimeoutMs ?? 10_000);
    });
  }

  async function teardown(client, { browserAlreadyClosing = false } = {}) {
    if (!client) return;

    client.removeAllListeners();

    if (browserAlreadyClosing) {
      await waitForBrowserClose(client.pupBrowser);
    } else {
      await Promise.race([
        client.destroy().catch(() => {}),
        sleep(config.shutdownTimeoutMs),
      ]);
    }

    // Never touch the profile until Chromium has closed or been terminated.
    await killOrphanBrowsers();
    await sleep(500);
  }

  return { killOrphanBrowsers, teardown };
}
