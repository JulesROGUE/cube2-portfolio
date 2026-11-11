/*
 * portfolio.js — coquille web minimale du client Cube 2 « visite du portfolio ».
 * Toute l'interface est celle du jeu d'origine ; ce script ne fait que :
 *  - lire ?name=<pseudo> (assaini) pour nommer le joueur, sinon un nom invité ;
 *  - configurer le WebSocket du jeu sur <même origine>/<préfixe>/ws (ws ou wss) :
 *    les sockets UDP d'ENet sont émulées par Emscripten au-dessus de ce WebSocket ;
 *  - ne capturer la souris QUE sur un clic dans le canvas (jamais sur un simple
 *    focus de l'iframe) et la relâcher quand le pointer lock est perdu (Échap) ;
 *  - adapter la résolution à la taille de l'iframe et réveiller l'audio.
 */
(function () {
  'use strict';

  var canvas = document.getElementById('canvas');
  var loading = document.getElementById('loading');
  var statusEl = document.getElementById('status');

  function sanitizeName(raw) {
    if (!raw) return '';
    var s = String(raw).normalize('NFD').replace(/[̀-ͯ]/g, '');
    return s.replace(/[^A-Za-z0-9_.\-]/g, '').slice(0, 15);
  }
  var params = new URLSearchParams(location.search);
  var playerName = sanitizeName(params.get('name')) || 'invite' + Math.floor(100 + Math.random() * 900);
  var offline = params.get('offline') === '1';

  var basePath = location.pathname.replace(/[^\/]*$/, '');
  var wsUrl = (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + basePath + 'ws';

  var ready = false;
  function call(fn, types, args) {
    if (!ready) return;
    try { Module.ccall(fn, null, types, args); } catch (e) { console.error(e); }
  }
  function exec(script) { call('pf_execute', ['string'], [script]); }

  function viewport() {
    return { w: Math.max(320, canvas.clientWidth || innerWidth), h: Math.max(240, canvas.clientHeight || innerHeight) };
  }

  var noop = function () {};
  window.Module = {
    canvas: canvas,
    desiredWidth: viewport().w,
    desiredHeight: viewport().h,
    websocket: { url: wsUrl, subprotocol: 'binary' },
    print: function (t) { console.log(t); },
    printErr: function (t) { console.warn(t); },
    setStatus: function (t) { statusEl.textContent = t || ''; },
    // Crochets appelés par le moteur (hérités de BananaBread / Sour)
    autoexec: function () {
      ready = true;
      exec('exec "data/portfolio.cfg"');
      exec('name "' + playerName + '"');
      exec('pfconnect = [connect cube2 28785]');
    },
    setPlayerModels: noop,
    loadDefaultMap: function () {
      // Carte affichée tout de suite en solo, puis connexion au serveur multijoueur.
      exec('mode 0; map portfolio');
      if (!offline) setTimeout(function () { exec('pfconnect'); }, 800);
    },
    onGameReady: function () { loading.className = 'done'; resize(); },
    onConnect: noop, onDisconnect: noop, onLocalDisconnect: noop, postLoadWorld: noop,
    // `js "..."` côté cubescript : seul l'enchaînement des musiques est autorisé.
    interop: function (cmd) { if (cmd === 'nextmusic') nextMusic(); return 0; },
    // Fichiers introuvables : seuls les échecs signalés par le moteur (msg != 0) comptent,
    // les essais silencieux de variantes (.jpg puis .png, masques facultatifs...) sont ignorés.
    assets: { missingTexture: function (n, msg) { if (msg) console.warn('texture manquante : ' + n); },
              missingModel: function (n, msg) { if (msg) console.warn('modèle manquant : ' + n); },
              missingSound: function (n, msg) { if (msg) console.warn('son manquant : ' + n); }, onConnect: noop,
              loadWorld: noop, receiveMap: noop, loadRandomMap: noop },
    cluster: { receive: function () { return 0; }, send: noop, connect: noop, disconnect: noop, createGame: noop },
    gameState: { playerState: noop },
    discord: { login: noop }
  };

  var lastW = 0, lastH = 0;
  function resize() {
    var v = viewport();
    Module.desiredWidth = v.w; Module.desiredHeight = v.h;
    if (!ready || (v.w === lastW && v.h === lastH)) return;
    lastW = v.w; lastH = v.h;
    call('pf_resize', ['number', 'number'], [v.w, v.h]);
  }
  window.addEventListener('resize', resize);
  document.addEventListener('fullscreenchange', function () { setTimeout(resize, 50); });

  // Onglet masqué : requestAnimationFrame s'arrête, ce qui gèlerait les monstres simulés
  // par ce client pour tout le serveur. On bascule alors la boucle principale sur setTimeout.
  document.addEventListener('visibilitychange', function () {
    var setTiming = window._emscripten_set_main_loop_timing;
    if (!ready || typeof setTiming !== 'function') return;
    if (document.hidden) setTiming(0, 16);   // EM_TIMING_SETTIMEOUT, ~60 Hz
    else setTiming(1, 1);                   // EM_TIMING_RAF
  });

  // Musiques libres de droit (CC0, voir CREDITS.md) : téléchargées seulement au
  // premier geste de l'utilisateur, puis jouées en boucle via la commande `music` du jeu.
  var MUSIC = ['stage1.ogg', 'stage2.ogg', 'stageselect.ogg'];
  var musicIndex = -1, musicStarted = false;
  function nextMusic() {
    if (!ready) return;
    musicIndex = (musicIndex + 1) % MUSIC.length;
    var name = MUSIC[musicIndex];
    var target = '/packages/music/' + name;
    var play = function () { exec('music "music/' + name + '" [js nextmusic]'); };
    try { if (Module.FS.analyzePath(target).exists) return play(); } catch (e) {}
    fetch(basePath + 'music/' + name).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.arrayBuffer();
    }).then(function (buf) {
      Module.FS.mkdirTree('/packages/music');
      Module.FS.writeFile(target, new Uint8Array(buf));
      console.log('musique chargée : ' + name + ' (' + buf.byteLength + ' octets)');
      play();
    }).catch(function (e) { console.warn('musique indisponible : ' + name + ' ' + e); });
  }
  function startMusic() {
    if (musicStarted || !ready) return;
    musicStarted = true;
    nextMusic();
  }

  function resumeAudio() {
    var ctx = Module.SDL2 && Module.SDL2.audioContext;
    if (ctx && ctx.state === 'suspended') ctx.resume();
    startMusic();
  }

  // Capture de la souris : uniquement sur un clic dans le canvas. Le jeu ne passe en
  // mode « souris capturée » qu'une fois le pointer lock réellement obtenu (sinon la
  // vue dériverait en suivant le curseur), et le relâche dès qu'il est perdu (Échap).
  canvas.addEventListener('mousedown', function () {
    canvas.focus();
    resumeAudio();
    if (!ready || document.pointerLockElement === canvas) return;
    // Mouvement « ajusté » par le système (même vitesse que le curseur) : le mode brut
    // (unadjustedMovement) envoie des comptes de capteur, énormes sur une souris haute
    // résolution, d'où des à-coups de la vue et du curseur des menus.
    if (canvas.requestPointerLock) { try { canvas.requestPointerLock(); } catch (e) {} }
  });
  document.addEventListener('keydown', resumeAudio);
  document.addEventListener('pointerlockchange', function () {
    call('pf_grab', ['number'], [document.pointerLockElement === canvas ? 1 : 0]);
  });
  // Vue et curseur des menus : chaque mouvement (y compris les événements regroupés
  // par le navigateur) est transmis au jeu, qui les cumule et les applique une fois
  // par image. Plus fiable que la voie SDL, qui pouvait en perdre en pointer lock.
  document.addEventListener('pointermove', function (e) {
    if (!ready || document.pointerLockElement !== canvas) return;
    var dx = 0, dy = 0, list = e.getCoalescedEvents ? e.getCoalescedEvents() : [];
    if (list && list.length > 1) { for (var i = 0; i < list.length; i++) { dx += list[i].movementX; dy += list[i].movementY; } }
    else { dx = e.movementX; dy = e.movementY; }
    if (dx || dy) Module._pf_mousemove(dx | 0, dy | 0);
  });
  document.addEventListener('pointerlockerror', function () {
    console.warn('pointer lock refusé (iframe sans allow="pointer-lock" ?)');
  });
  window.addEventListener('blur', function () { call('pf_grab', ['number'], [0]); });
  // Flèches / Tab ne doivent pas faire défiler la page ni sortir de l'iframe.
  window.addEventListener('keydown', function (e) {
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Tab'].indexOf(e.code) >= 0) e.preventDefault();
  });
})();
