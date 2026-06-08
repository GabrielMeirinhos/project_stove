import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { request as httpRequest } from 'node:http';

const PORT = Number(process.env.PORT ?? 4173);
const ROOT = process.cwd();
const LANDING_FILE = path.join(ROOT, 'stove_landing_final.html');

const contentTypeByExt = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.mjs': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
};

const APP_PROXY_TARGET = Number(process.env.APP_PORT ?? 3000);

function proxyToApp(req, res) {
  const proxyReq = httpRequest(
    {
      hostname: '127.0.0.1',
      port: APP_PROXY_TARGET,
      path: req.url,
      method: req.method,
      headers: req.headers,
    },
    (proxyRes) => {
      res.writeHead(proxyRes.statusCode ?? 502, proxyRes.headers);
      proxyRes.pipe(res);
    },
  );

  proxyReq.on('error', () => {
    res.writeHead(503, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>App indisponível</title></head><body><h1>App indisponível</h1><p>Inicie o frontend com <strong>npm run dev</strong> dentro de <code>frontend/</code>.</p></body></html>');
  });

  req.pipe(proxyReq);
}

const server = http.createServer((req, res) => {
  const requestUrl = new URL(req.url ?? '/', `http://${req.headers.host ?? 'localhost'}`);
  const pathname = decodeURIComponent(requestUrl.pathname);

  if (pathname === '/' || pathname === '/stove_landing_final.html') {
    const html = fs.readFileSync(LANDING_FILE, 'utf8');
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(html);
    return;
  }

  if (pathname === '/app' || pathname.startsWith('/app/')) {
    const upstreamPath = pathname === '/app' ? '/' : pathname.slice('/app'.length) || '/';
    req.url = upstreamPath + requestUrl.search;
    proxyToApp(req, res);
    return;
  }

  if (pathname === '/src' || pathname.startsWith('/src/') || pathname === '/@vite' || pathname.startsWith('/@vite/') || pathname === '/node_modules' || pathname.startsWith('/node_modules/') || pathname === '/assets' || pathname.startsWith('/assets/') || pathname === '/api' || pathname.startsWith('/api/')) {
    proxyToApp(req, res);
    return;
  }

  const assetPath = path.join(ROOT, pathname.replace(/^\//, ''));
  if (!assetPath.startsWith(ROOT) || !fs.existsSync(assetPath) || fs.statSync(assetPath).isDirectory()) {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Not found');
    return;
  }

  const ext = path.extname(assetPath).toLowerCase();
  const contentType = contentTypeByExt[ext] ?? 'application/octet-stream';
  res.writeHead(200, { 'Content-Type': contentType });
  fs.createReadStream(assetPath).pipe(res);
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`Landing page running at http://localhost:${PORT}`);
});