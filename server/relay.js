/*
 * relay.js — conteneur web du Cube 2 portfolio.
 *
 *  1. Sert le client (HTML/JS/WASM/données) sous le préfixe /cube2/ avec les bons
 *     types MIME (application/wasm...) et la compression gzip pré-calculée.
 *  2. Fait le pont WebSocket <-> UDP sur /cube2/ws : chaque connexion WebSocket
 *     (sockets UDP d'ENet émulées par Emscripten dans le navigateur) obtient sa
 *     propre socket UDP vers le serveur dédié Cube 2. Les datagrammes sont
 *     relayés tels quels, dans les deux sens.
 *
 * Variables d'environnement :
 *   PORT (8080), PREFIX (/cube2), PUBLIC_DIR (./public),
 *   CUBE2_SERVER_HOST (cube2-server), CUBE2_SERVER_PORT (28785), MAX_CLIENTS (64)
 */
'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');
const dgram = require('dgram');
const { WebSocketServer } = require('ws');

const PORT = parseInt(process.env.PORT || '8080', 10);
const PREFIX = (process.env.PREFIX || '/cube2').replace(/\/+$/, '');
const PUBLIC_DIR = path.resolve(process.env.PUBLIC_DIR || path.join(__dirname, 'public'));
const GAME_HOST = process.env.CUBE2_SERVER_HOST || 'cube2-server';
const GAME_PORT = parseInt(process.env.CUBE2_SERVER_PORT || '28785', 10);
const MAX_CLIENTS = parseInt(process.env.MAX_CLIENTS || '64', 10);
const MAX_DATAGRAM = 4096;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.wasm': 'application/wasm',
  '.data': 'application/octet-stream',
  '.json': 'application/json',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
  '.txt': 'text/plain; charset=utf-8',
};

function log(...args) { console.log(new Date().toISOString(), ...args); }

// --- Fichiers statiques -----------------------------------------------------
function serveStatic(req, res, rel) {
  if (rel === '' || rel.endsWith('/')) rel += 'index.html';
  const file = path.normalize(path.join(PUBLIC_DIR, rel));
  if (!file.startsWith(PUBLIC_DIR + path.sep)) { res.writeHead(403); return res.end(); }
  fs.stat(file, (err, st) => {
    if (err || !st.isFile()) { res.writeHead(404, { 'Content-Type': 'text/plain' }); return res.end('404'); }
    const ext = path.extname(file);
    const headers = {
      'Content-Type': MIME[ext] || 'application/octet-stream',
      'X-Content-Type-Options': 'nosniff',
      // index.html et la coquille changent à chaque build ; le reste peut être mis en cache brièvement.
      'Cache-Control': ext === '.html' ? 'no-cache' : 'public, max-age=3600',
      'Vary': 'Accept-Encoding',
    };
    let target = file, size = st.size;
    const gz = file + '.gz';
    if (/\bgzip\b/.test(req.headers['accept-encoding'] || '') && fs.existsSync(gz)) {
      target = gz; size = fs.statSync(gz).size; headers['Content-Encoding'] = 'gzip';
    }
    headers['Content-Length'] = size;
    res.writeHead(200, headers);
    if (req.method === 'HEAD') return res.end();
    fs.createReadStream(target).pipe(res);
  });
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');
  const p = decodeURIComponent(url.pathname);
  if (req.method !== 'GET' && req.method !== 'HEAD') { res.writeHead(405); return res.end(); }
  if (p === PREFIX + '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ ok: true, clients: wss.clients.size }));
  }
  if (p === '/' || p === PREFIX) { res.writeHead(301, { Location: PREFIX + '/' + url.search }); return res.end(); }
  if (!p.startsWith(PREFIX + '/')) { res.writeHead(404); return res.end('404'); }
  serveStatic(req, res, p.slice(PREFIX.length + 1));
});

// --- Pont WebSocket <-> UDP ---------------------------------------------------
const wss = new WebSocketServer({
  noServer: true,
  maxPayload: MAX_DATAGRAM,
  perMessageDeflate: false,
  // Emscripten ouvre ses sockets avec le sous-protocole « binary » : il faut le renvoyer.
  handleProtocols: (protocols) => (protocols.has('binary') ? 'binary' : false),
});

server.on('upgrade', (req, socket, head) => {
  const p = new URL(req.url, 'http://localhost').pathname;
  if (p !== PREFIX + '/ws' && p !== PREFIX + '/ws/') { socket.destroy(); return; }
  if (wss.clients.size >= MAX_CLIENTS) {
    socket.write('HTTP/1.1 503 Service Unavailable\r\n\r\n');
    socket.destroy();
    return;
  }
  wss.handleUpgrade(req, socket, head, (ws) => wss.emit('connection', ws, req));
});

// Message spécial envoyé par Emscripten à l'ouverture d'une socket UDP émulée :
// 0xFFFFFFFF "port" <port 16 bits>. Il ne doit pas être transmis au serveur.
function isPortMessage(buf) {
  return buf.length === 10 && buf[0] === 0xff && buf[1] === 0xff && buf[2] === 0xff && buf[3] === 0xff &&
    buf.toString('latin1', 4, 8) === 'port';
}

let nextId = 1;
wss.on('connection', (ws, req) => {
  const id = nextId++;
  const who = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
  const udp = dgram.createSocket('udp4');
  let closed = false, connected = false;
  const pending = []; // datagrammes reçus avant la résolution DNS / connexion UDP
  log(`[ws#${id}] connexion de ${who} (${wss.clients.size} client(s))`);

  const close = () => {
    if (closed) return;
    closed = true;
    try { udp.close(); } catch (e) { /* déjà fermée */ }
    try { ws.close(); } catch (e) { /* déjà fermée */ }
    log(`[ws#${id}] fermeture`);
  };

  udp.on('message', (msg) => { if (ws.readyState === ws.OPEN) ws.send(msg, { binary: true }); });
  udp.on('error', (err) => { log(`[ws#${id}] erreur UDP: ${err.message}`); close(); });
  udp.connect(GAME_PORT, GAME_HOST, (err) => {
    if (err) { log(`[ws#${id}] serveur injoignable: ${err.message}`); return close(); }
    connected = true;
    while (pending.length) udp.send(pending.shift());
  });

  ws.on('message', (data, isBinary) => {
    if (!isBinary || closed) return;
    const buf = Buffer.isBuffer(data) ? data : Buffer.from(data);
    if (isPortMessage(buf)) return;
    if (!connected) { if (pending.length < 32) pending.push(buf); return; }
    udp.send(buf);
  });
  ws.on('close', close);
  ws.on('error', close);
});

server.listen(PORT, () => {
  log(`cube2-portfolio : http://0.0.0.0:${PORT}${PREFIX}/  (WebSocket ${PREFIX}/ws -> udp://${GAME_HOST}:${GAME_PORT})`);
});

for (const sig of ['SIGINT', 'SIGTERM']) process.on(sig, () => { log('arrêt'); process.exit(0); });
