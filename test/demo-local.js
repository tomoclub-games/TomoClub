// TEST ONLY: runs the fixture districts, the API stub and the app together
// so the interface can be clicked through locally without an API key.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { startStub } from './anthropic-stub.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const FIX = path.join(here, 'fixtures');
function site(dir, port) {
  http
    .createServer((req, res) => {
      const origin = `http://127.0.0.1:${port}`;
      const p = decodeURIComponent(new URL(req.url, origin).pathname);
      let file = path.join(FIX, dir, p);
      if (p.endsWith('/')) file = path.join(file, 'index.html');
      if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) {
        res.writeHead(404);
        return res.end('Not found');
      }
      const ext = path.extname(file);
      let body = fs.readFileSync(file);
      if (ext === '.xml') body = Buffer.from(body.toString().replaceAll('__ORIGIN__', origin));
      res.writeHead(200, { 'content-type': { '.html': 'text/html', '.pdf': 'application/pdf', '.xml': 'application/xml', '.txt': 'text/plain' }[ext] });
      res.end(body);
    })
    .listen(port, '127.0.0.1');
}
site('riverbend', 4599);
site('lakeside', 4598);
await startStub(4650);
const child = spawn(process.execPath, ['--disable-warning=ExperimentalWarning', 'src/server.js'], {
  cwd: path.join(here, '..'),
  env: {
    ...process.env,
    PORT: '4800',
    DATA_DIR: fs.mkdtempSync(path.join(os.tmpdir(), 'demo-')),
    ALLOW_PRIVATE_HOSTS: 'true',
    ANTHROPIC_API_KEY: 'test-key',
    ANTHROPIC_API_URL: 'http://127.0.0.1:4650',
    ADMIN_PASSWORD: 'demo-pass',
    CRAWL_DELAY_MS: '150',
  },
  stdio: 'inherit',
});
process.on('SIGTERM', () => {
  child.kill();
  process.exit(0);
});
