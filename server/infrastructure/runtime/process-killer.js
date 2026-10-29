import path from 'node:path';
import { execFile } from 'node:child_process';

const isWindows = process.platform === 'win32';

// Marker dikirim lewat environment variable, bukan disisipkan ke script (aman dari injeksi)
const WINDOWS_SCRIPT = `
  $marker = $env:KILL_MARKER
  $session = $env:KILL_SESSION
  Get-CimInstance Win32_Process |
  Where-Object {
    ($_.Name -match '^(chrome|chromium|msedge)\\.exe$') -and
    $_.CommandLine -and
    (
      ($session -and $_.CommandLine -like "*$session*") -or
      ($marker -and (
        $_.CommandLine -like "*$marker*" -or
        $_.CommandLine -like "*$($marker.Replace('\\', '/'))*"
      ))
    )
  } |
  ForEach-Object {
    & taskkill.exe /F /T /PID $_.ProcessId 2>$null
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
  }
`;

export class ProcessKiller {
  /** Mematikan proses Chrome/Chromium yang command line-nya memuat marker (Chrome pribadi aman). */
  killByCommandLine(marker) {
    return new Promise((resolve) => {
      if (!marker) return resolve();

      if (isWindows) {
        const session = path.basename(marker);
        execFile(
          'powershell',
          ['-NoProfile', '-NonInteractive', '-Command', WINDOWS_SCRIPT],
          {
            windowsHide: true,
            env: { ...process.env, KILL_MARKER: marker, KILL_SESSION: session },
          },
          () => resolve()
        );
      } else {
        execFile('pkill', ['-f', '--', marker], () => resolve());
      }
    });
  }
}