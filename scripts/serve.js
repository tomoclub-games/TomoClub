// Node port of scripts/serve.py for StackBlitz (WebContainers have no Python).
// Clean URLs: /about serves about/index.html.
// Rewrite: /podcast-<id> serves podcast/episodes/<id>/index.html.
//
// Usage: node scripts/serve.js [port]   (default 8000)
const http = require("http");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const PODCAST = /^\/podcast-([A-Za-z0-9_-]+)\/?$/;
const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".xml": "application/xml; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
  ".webmanifest": "application/manifest+json",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".webp": "image/webp",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".pdf": "application/pdf",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".ttf": "font/ttf",
};

const isFile = (p) => fs.existsSync(p) && fs.statSync(p).isFile();

function resolve(urlPath) {
  const clean = decodeURIComponent(urlPath.split("?")[0].split("#")[0]);
  const m = PODCAST.exec(clean);
  const rel = m ? `/podcast/episodes/${m[1]}/index.html` : clean;
  const fs_ = path.join(ROOT, path.normalize(rel));
  if (!fs_.startsWith(ROOT)) return null;
  if (isFile(fs_)) return fs_;
  if (isFile(path.join(fs_, "index.html"))) return path.join(fs_, "index.html");
  if (isFile(fs_ + ".html")) return fs_ + ".html";
  return null;
}

const port = Number(process.env.PORT || process.argv[2]) || 8000;
http
  .createServer((req, res) => {
    const file = resolve(req.url);
    if (!file) {
      res.writeHead(404, { "Content-Type": "text/plain" });
      return res.end("Not found");
    }
    res.writeHead(200, {
      "Content-Type": TYPES[path.extname(file)] || "application/octet-stream",
    });
    fs.createReadStream(file).pipe(res);
  })
  .listen(port, () => console.log(`Serving ${ROOT} at http://localhost:${port}`));
