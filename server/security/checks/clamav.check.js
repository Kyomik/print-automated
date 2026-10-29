import net from 'node:net';
import { block } from '../verdict.js';

/**
 * Memindai buffer menggunakan protokol INSTREAM ClamAV daemon (clamd) via TCP
 */
function scanBuffer(data, options) {
  return new Promise((resolve, reject) => {
    const socket = new net.Socket();
    let response = '';

    socket.setTimeout(options.timeoutMs ?? 30000);

    socket.connect(options.port, options.host, () => {
      // Perintah INSTREAM: kirim "zINSTREAM\0"
      socket.write('zINSTREAM\0');

      const chunkSize = 2048;
      for (let i = 0; i < data.length; i += chunkSize) {
        const chunk = data.subarray(i, i + chunkSize);
        const sizeBuf = Buffer.alloc(4);
        sizeBuf.writeUInt32BE(chunk.length, 0);
        socket.write(sizeBuf);
        socket.write(chunk);
      }

      // Chunk ukuran 0 menandakan akhir stream
      const zeroBuf = Buffer.alloc(4);
      zeroBuf.writeUInt32BE(0, 0);
      socket.write(zeroBuf);
    });

    socket.on('data', (chunk) => {
      response += chunk.toString('utf8');
    });

    socket.on('end', () => {
      const trimmed = response.trim();
      if (trimmed.includes('FOUND')) {
        const match = trimmed.match(/stream:\s*(.+?)\s*FOUND/i);
        resolve({ infected: true, signature: match?.[1] ?? 'Infected' });
      } else {
        resolve({ infected: false });
      }
    });

    socket.on('error', reject);
    socket.on('timeout', () => {
      socket.destroy();
      reject(new Error('ClamAV scan timeout'));
    });
  });
}

export function createClamavCheck(options) {
  return async ({ file }) => {
    try {
      const result = await scanBuffer(file.data, options);
      if (result.infected) return block(`virus terdeteksi (${result.signature})`);
    } catch {
      // fail closed: pemindai mati -> file ditolak, bukan diloloskan
      if (options.failClosed) return block('pemindai antivirus tidak tersedia');
    }
  };
}