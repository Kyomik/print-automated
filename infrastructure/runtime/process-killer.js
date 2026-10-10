import { execFile } from 'node:child_process';

const isWindows = process.platform === 'win32';

// Marker dikirim lewat environment variable, bukan disisipkan ke script (aman dari injeksi)
const WINDOWS_SCRIPT = `
  Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" |
  Where-Object { $_.CommandLine -and $_.CommandLine.Contains($env:KILL_MARKER) } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
`;

export class ProcessKiller {
  /** Mematikan proses Chrome yang command line-nya memuat marker (Chrome pribadi aman). */
  killByCommandLine(marker) {
    return new Promise((resolve) => {
      if (!marker) return resolve();

      if (isWindows) {
        execFile(
          'powershell',
          ['-NoProfile', '-NonInteractive', '-Command', WINDOWS_SCRIPT],
          { windowsHide: true, env: { ...process.env, KILL_MARKER: marker } },
          () => resolve()
        );
      } else {
        execFile('pkill', ['-f', '--', marker], () => resolve());
      }
    });
  }
}