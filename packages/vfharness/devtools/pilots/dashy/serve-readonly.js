'use strict';
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, 'app', 'dist');
const host = '127.0.0.1';
const port = 4000;
const types = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.webmanifest': 'application/manifest+json; charset=utf-8',
  '.yml': 'text/yaml; charset=utf-8',
  '.yaml': 'text/yaml; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.eot': 'application/vnd.ms-fontobject',
  '.txt': 'text/plain; charset=utf-8',
};
function send(res, status, body, headers = {}) {
  res.writeHead(status, Object.assign({
    'Content-Type': 'text/plain; charset=utf-8',
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'no-referrer',
  }, headers));
  res.end(body);
}
const server = http.createServer((req, res) => {
  if (!['GET', 'HEAD'].includes(req.method)) return send(res, 405, 'Read-only launchpad', {'Allow':'GET, HEAD'});
  const authority = (req.headers.host || '').toLowerCase();
  if (!['localhost:4000', '127.0.0.1:4000'].includes(authority)) return send(res, 403, 'Local access only');
  let route;
  try { route = decodeURIComponent(new URL(req.url, 'http://localhost:4000').pathname).replace(/\\/g, '/'); }
  catch { return send(res, 400, 'Invalid URL'); }
  if (route.includes('\0') || route.split('/').includes('..')) return send(res, 403, 'Invalid path');
  if (/^\/(api|auth|login|save-config|proxy)(\/|$)/i.test(route)) return send(res, 404, 'No control APIs');
  const name = route === '/' ? '/index.html' : route;
  const candidate = path.resolve(root, '.' + name);
  const rel = path.relative(root, candidate);
  if (rel.startsWith('..') || path.isAbsolute(rel)) return send(res, 403, 'Invalid path');
  fs.stat(candidate, (err, st) => {
    if (err || !st.isFile()) return send(res, 404, 'Not found');
    const ext = path.extname(candidate).toLowerCase();
    const responseHeaders = {
      'Content-Type': types[ext] || 'application/octet-stream',
      'Cache-Control': 'no-store',
      'Content-Length': st.size,
      'X-Content-Type-Options': 'nosniff',
      'X-Frame-Options': 'DENY',
      'Referrer-Policy': 'no-referrer',
    };
    res.writeHead(200, responseHeaders);
    if (req.method === 'HEAD') return res.end();
    fs.createReadStream(candidate).on('error', () => res.destroy()).pipe(res);
  });
});
server.listen(port, host, () => console.log('DASHY_STATIC_LISTEN http://' + host + ':' + port));
