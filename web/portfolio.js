/*
 * portfolio.js — coquille web du client Cube 2 « visite du portfolio ».
 *
 *  - lit ?name=<pseudo> (assaini) pour nommer le joueur, sinon un nom invité ;
 *  - configure le WebSocket du jeu sur <même origine>/<préfixe>/ws (ws ou wss) :
 *    les sockets UDP d'ENet sont émulées par Emscripten au-dessus de ce WebSocket,
 *    le serveur fait le pont vers le serveur dédié Cube 2 (UDP) ;
 *  - gère le chargement, le redimensionnement, le plein écran et le focus
 *    (le client est prévu pour être intégré dans une iframe).
 */
(function () {
  'use strict';

  var canvas = document.getElementById('canvas');
  var overlay = document.getElementById('overlay');
  var statusEl = document.getElementById('status');
  var progressEl = document.getElementById('progress');
  var netEl = document.getElementById('net');
  var clickHint = document.getElementById('clickhint');

  // --- Nom du joueur -------------------------------------------------------
  function sanitizeName(raw) {
    if (!raw) return '';
    var s = String(raw).normalize('NFD').replace(/[̀-ͯ]/g, ''); // retire les accents
    s = s.replace(/[^A-Za-z0-9_.\-]/g, '');                              // caractères sûrs
    return s.slice(0, 15);
  }
  var params = new URLSearchParams(location.search);
  var playerName = sanitizeName(params.get('name'));
  if (!playerName) playerName = 'invite' + Math.floor(100 + Math.random() * 900);

  // --- URL du WebSocket : même origine, préfixe de la page + "ws" ----------
  var basePath = location.pathname.replace(/[^\/]*$/, ''); // ex. "/cube2/"
  var wsUrl = (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + basePath + 'ws';
  var offline = params.get('offline') === '1';

  function setStatus(text) { statusEl.textContent = text; }
  function setNet(on, text) {
    netEl.className = 'badge ' + (on ? 'on' : 'off');
    netEl.textContent = text;
  }

  var ready = false;
  function exec(script) {
    if (!ready) return;
    try { Module.ccall('pf_execute', null, ['string'], [script]); } catch (e) { console.error(e); }
  }

  function viewport() {
    var r = canvas.getBoundingClientRect();
    return { w: Math.max(320, Math.round(r.width)), h: Math.max(240, Math.round(r.height)) };
  }

  var connectTried = false;
  function connectToServer() {
    if (offline) return;
    connectTried = true;
    setNet(false, 'connexion…');
    exec('pfconnect');
  }

  var noop = function () {};
  var Module = window.Module = {
    canvas: canvas,
    // Le moteur lit ces deux valeurs à la création de la fenêtre SDL.
    desiredWidth: viewport().w,
    desiredHeight: viewport().h,
    websocket: { url: wsUrl, subprotocol: 'binary' },
    print: function (text) {
      console.log(text);
      if (/^joined server|connected to server/i.test(text)) setNet(true, 'en ligne');
      else if (/could not connect|server network error|disconnected/i.test(text)) setNet(false, 'hors ligne');
    },
    printErr: function (text) { console.warn(text); },
    setStatus: function (text) {
      if (!text) return;
      var m = text.match(/\((\d+(?:\.\d+)?)\/(\d+)\)/);
      if (m) progressEl.style.width = Math.round(100 * m[1] / m[2]) + '%';
      setStatus(text.replace(/\(\d.*\)/, '').replace('Downloading data...', 'Téléchargement des données…'));
    },
    monitorRunDependencies: function (left) {
      if (!left) setStatus('Initialisation du moteur…');
    },

    // --- Crochets appelés par le moteur (hérités de BananaBread / Sour) ----
    autoexec: function () {
      ready = true;
      exec('name "' + playerName + '"');
      exec('pfconnect = [connect cube2 28785]');
    },
    setPlayerModels: noop,
    loadDefaultMap: function () {
      // On affiche tout de suite la carte en solo, puis on rejoint le serveur :
      // si le serveur est injoignable, la visite reste jouable hors ligne.
      exec('mode 0; map portfolio');
      setTimeout(connectToServer, 800);
    },
    onGameReady: function () {
      progressEl.style.width = '100%';
      overlay.classList.add('done');
      clickHint.hidden = false;
      resize();
    },
    onConnect: noop,
    onDisconnect: function () { setNet(false, 'hors ligne'); },
    onLocalDisconnect: noop,
    postLoadWorld: noop,
    interop: function () { return 0; },
    assets: { missingTexture: noop, missingModel: noop, missingSound: noop, onConnect: noop,
              loadWorld: noop, receiveMap: noop, loadRandomMap: noop },
    cluster: { receive: function () { return 0; }, send: noop, connect: noop, disconnect: noop, createGame: noop },
    gameState: { playerState: noop },
    discord: { login: noop }
  };

  setNet(false, offline ? 'hors ligne (forcé)' : 'hors ligne');

  // --- Redimensionnement ---------------------------------------------------
  var lastW = 0, lastH = 0;
  function resize() {
    var v = viewport();
    Module.desiredWidth = v.w; Module.desiredHeight = v.h;
    if (!ready || (v.w === lastW && v.h === lastH)) return;
    lastW = v.w; lastH = v.h;
    try { Module.ccall('pf_resize', null, ['number', 'number'], [v.w, v.h]); } catch (e) { console.error(e); }
  }
  window.addEventListener('resize', resize);
  document.addEventListener('fullscreenchange', function () { setTimeout(resize, 50); });

  // --- Focus clavier + capture de la souris (iframe) ------------------------
  canvas.addEventListener('mousedown', function () {
    canvas.focus();
    try { window.focus(); } catch (e) {}
    clickHint.hidden = true;
  });
  document.addEventListener('pointerlockchange', function () {
    if (ready && !document.pointerLockElement) clickHint.hidden = false;
    else clickHint.hidden = true;
  });
  // Évite que les flèches / Tab fassent défiler la page ou sortir le focus de l'iframe
  // (on ne bloque pas les touches qui produisent du texte : le chat en a besoin).
  window.addEventListener('keydown', function (e) {
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Tab'].indexOf(e.code) >= 0) e.preventDefault();
  });

  // --- Plein écran ---------------------------------------------------------
  document.getElementById('fullscreen').addEventListener('click', function () {
    var el = document.getElementById('stage');
    if (document.fullscreenElement) document.exitFullscreen();
    else if (el.requestFullscreen) el.requestFullscreen().catch(function () {});
    canvas.focus();
  });

  window.addEventListener('error', function (e) {
    if (!ready) setStatus('Erreur : ' + (e.message || e));
  });
})();
