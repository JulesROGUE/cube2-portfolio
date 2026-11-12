/*
 * portfolio.js — coquille web minimale du client Cube 2 « visite du portfolio ».
 * Toute l'interface est celle du jeu d'origine ; ce script ne fait que :
 *  - lire ?name=<pseudo> (assaini) pour nommer le joueur, sinon un nom invité ;
 *  - configurer le WebSocket du jeu sur <même origine>/<préfixe>/ws (ws ou wss) :
 *    les sockets UDP d'ENet sont émulées par Emscripten au-dessus de ce WebSocket ;
 *  - gérer la souris : capturée (pointer lock) en jeu, libre avec le curseur natif
 *    dans les menus ; un seul Échap ouvre le menu ; plein écran ; quitter le jeu ;
 *  - mémoriser l'apparence choisie (localStorage) ;
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
  var reconnectDelay = 3000, reconnectTimer = 0;
  // Connexion perdue (serveur redémarré, réseau coupé…) : le moteur se retrouve sans
  // carte ni mode. On recharge la carte en solo puis on retente la connexion, avec un
  // délai croissant, jusqu'à ce qu'elle réussisse (un échec de connexion relance un essai).
  function scheduleReconnect(reloadMap) {
    if (quitting || offline) return;
    console.warn('connexion au serveur perdue : nouvelle tentative dans ' + (reconnectDelay / 1000) + ' s');
    clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(function () {
      if (quitting) return;
      if (reloadMap) exec('if (! (isconnected 0 0)) [mode 0; map portfolio]');
      setTimeout(function () {
        exec('if (! (isconnected 0 0)) [pfconnect]');
        // pas connecté 15 s plus tard (échec de connexion) : nouvel essai
        reconnectTimer = setTimeout(function () { exec('if (! (isconnected 0 0)) [js reconnect]'); }, 15000);
      }, reloadMap ? 800 : 0);
    }, reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * 2, 30000);
  }
  function call(fn, types, args) {
    if (!ready) return;
    try { Module.ccall(fn, null, types, args); } catch (e) { console.error(e); }
  }
  function exec(script) { call('pf_execute', ['string'], [script]); }

  function viewport() {
    return { w: Math.max(320, canvas.clientWidth || innerWidth), h: Math.max(240, canvas.clientHeight || innerHeight) };
  }

  // --- Version du build et progression du chargement -------------------------
  // Toutes les ressources sont demandées avec ?v=<build> : un cache (navigateur ou
  // Cloudflare) ne peut plus mélanger l'ancien chargeur avec les nouvelles données,
  // ce qui bloquait le jeu sur « Chargement ».
  var buildMeta = document.querySelector('meta[name="build"]');
  var BUILD = buildMeta && buildMeta.content !== '__BUILD__' ? buildMeta.content : '';
  function versioned(path) { return BUILD ? path + '?v=' + BUILD : path; }

  // Écran de chargement minimal : « Chargement.. » puis « <étape> <n>/3 ».
  var stepEl = document.getElementById('ld-step');
  var dl = { wasm: [0, 0], data: [0, 0] };   // [chargé, total] en octets
  // moteur et données se téléchargent en parallèle : l'étape affichée ne recule jamais
  var wasmDone = false, dataDone = false, failed = false, shown = 0;
  var STEPS = ['Moteur du jeu', 'Données du jeu', 'Préparation de la carte'];
  function showStep(i) {
    if (failed || i < shown) return;
    shown = i;
    stepEl.textContent = STEPS[i] + ' ' + (i + 1) + '/' + STEPS.length;
  }
  function renderProgress() {
    if (dl.data[1] && dl.data[0] >= dl.data[1]) dataDone = true;
    if (!wasmDone) showStep(0);
    else if (!dataDone) showStep(1);
    else showStep(2);
  }
  function setPhase() { dataDone = true; renderProgress(); }
  function loadError() {
    failed = true;
    stepEl.className = 'ld-step ld-error';
    stepEl.textContent = 'Échec du chargement : actualisez la page';
  }
  var dataRaw = 0;
  fetch(versioned('cube2.data'), { method: 'HEAD' }).then(function (r) {
    dataRaw = +r.headers.get('X-Raw-Length') || 0;
    if (dataRaw && dl.data[1] < dataRaw) { dl.data[1] = dataRaw; }
  }).catch(function () {});

  var noop = function () {};
  window.Module = {
    locateFile: function (path) { return versioned(path); },
    // Téléchargement du moteur (.wasm) en suivant sa progression
    instantiateWasm: function (imports, receive) {
      fetch(versioned('cube2.wasm')).then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        dl.wasm[1] = +r.headers.get('X-Raw-Length') || +r.headers.get('Content-Length') || 0;
        renderProgress();
        if (!r.body || !r.body.getReader) return r.arrayBuffer();
        var reader = r.body.getReader();
        var chunks = [];
        var got = 0;
        var pump = function () {
          return reader.read().then(function (res) {
            if (res.done) return;
            chunks.push(res.value);
            got += res.value.length;
            dl.wasm[0] = got;
            if (got > dl.wasm[1]) dl.wasm[1] = got;
            renderProgress();
            return pump();
          });
        };
        return pump().then(function () {
          var buf = new Uint8Array(got);
          var off = 0;
          chunks.forEach(function (c) { buf.set(c, off); off += c.length; });
          wasmDone = true;
          renderProgress();
          return buf.buffer;
        });
      }).then(function (bytes) {
        return WebAssembly.instantiate(bytes, imports);
      }).then(function (out) {
        receive(out.instance, out.module);
      }).catch(loadError);
      return {};
    },
    canvas: canvas,
    desiredWidth: viewport().w,
    desiredHeight: viewport().h,
    websocket: { url: wsUrl, subprotocol: 'binary' },
    print: function (t) { console.log(t); },
    printErr: function (t) { console.warn(t); },
    // Messages d'Emscripten : « Downloading data... (x/y) », « Preparing... (n/m) », « Running... »
    setStatus: function (t) {
      t = t || '';
      var m = /Downloading data\.\.\. \((\d+)\/(\d+)\)/.exec(t);
      if (m) {
        dl.data = [+m[1], Math.max(dataRaw, +m[2], +m[1])];
        renderProgress();
        statusEl.textContent = '';
        return;
      }
      if (/Preparing|Running/.test(t) || (t === '' && dl.data[1] && dl.data[0] >= dl.data[1])) {
        setPhase();
      }
      statusEl.textContent = t.replace('Preparing...', 'Préparation…').replace('Running...', 'Démarrage…');
    },
    // Crochets appelés par le moteur (hérités de BananaBread / Sour)
    autoexec: function () {
      ready = true;
      exec('exec "data/portfolio.cfg"');
      exec('pfsetname "' + playerName + '"');   // pseudo de la session, non modifiable ensuite
      var skin = null;
      try { skin = localStorage.getItem('cube2.skin'); } catch (e) {}
      if (skin !== null && /^[0-3]$/.test(skin)) exec('playermodel ' + skin);
      exec('pfconnect = [connect cube2 28785]');
    },
    setPlayerModels: noop,
    loadDefaultMap: function () {
      // Carte affichée tout de suite en solo, puis connexion au serveur multijoueur.
      exec('mode 0; map portfolio');
      if (!offline) setTimeout(function () { exec('pfconnect'); }, 800);
    },
    onGameReady: function () { loading.className = 'done'; resize(); },
    onConnect: function () { reconnectDelay = 3000; },
    // Connexion perdue (serveur redémarré, réseau coupé…) : le moteur se retrouve sans
    // carte ni mode. On recharge la carte en solo puis on se reconnecte (délai croissant).
    onDisconnect: function () {
      if (quitting || offline) return;
      scheduleReconnect(true);
    },
    onLocalDisconnect: noop, postLoadWorld: noop,
    // `js "..."` côté cubescript : seul l'enchaînement des musiques est autorisé.
    interop: function (cmd) {
      if (cmd === 'nextmusic') nextMusic();
      else if (cmd === 'fullscreen') setTimeout(toggleFullscreen, 0);
      else if (cmd === 'quit') setTimeout(quitGame, 0);
      else if (cmd === 'reconnect') scheduleReconnect(false);
      return 0;
    },
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

  // --- Souris -------------------------------------------------------------------
  // En jeu : pointer lock, mouvements relatifs transmis au jeu (pf_mousemove), cumulés
  // et appliqués une fois par image. Dans les menus : souris libre, curseur NATIF du
  // système et position absolue (pf_mousepos, en fractions du canvas : indépendante
  // de la taille CSS, de la résolution et de devicePixelRatio).
  // Le navigateur réserve le premier Échap à la sortie du pointer lock : une perte de
  // capture non demandée ouvre donc directement le menu principal.
  var rawMouse = params.get('rawmouse') === '1';   // unadjustedMovement (essai)
  var quitting = false, expectUnlockUntil = 0;
  var hint = document.createElement('div');
  hint.id = 'hint';
  hint.textContent = 'Click to resume';
  document.body.appendChild(hint);

  function locked() { return document.pointerLockElement === canvas; }
  function guiOpen() { return ready && Module._pf_guiopen ? Module._pf_guiopen() === 1 : false; }
  function updateUi() {
    var l = locked();
    canvas.style.cursor = l ? 'none' : 'default';
    hint.className = (ready && !l && !quitting && !guiOpen() && loading.className === 'done') ? 'on' : '';
  }
  function requestLock() {
    if (!ready || locked() || quitting || !canvas.requestPointerLock) return;
    var fallback = function () { try { var q = canvas.requestPointerLock(); if (q && q.catch) q.catch(updateUi); } catch (e) { updateUi(); } };
    try {
      var p = rawMouse ? canvas.requestPointerLock({ unadjustedMovement: true }) : canvas.requestPointerLock();
      // repli automatique si le navigateur refuse le mode brut (ou la demande)
      if (p && p.catch) p.catch(function () { if (rawMouse) fallback(); else updateUi(); });
    } catch (e) { if (rawMouse) fallback(); }
  }
  function releaseLock() {
    if (!locked()) return;
    expectUnlockUntil = performance.now() + 1000;
    document.exitPointerLock();
  }
  Module.pfLock = requestLock;          // appelé par le jeu quand tous les menus se ferment
  Module.pfUnlock = releaseLock;        // appelé par le jeu quand un menu s'ouvre en jeu
  Module.pfSkin = function (n) { try { localStorage.setItem('cube2.skin', String(n)); } catch (e) {} };

  function sendPos(e) {
    if (!ready || !Module._pf_mousepos) return;
    var r = canvas.getBoundingClientRect();
    if (!r.width || !r.height) return;
    Module._pf_mousepos((e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height);
  }

  canvas.addEventListener('mousedown', function (e) {
    canvas.focus();
    resumeAudio();
    if (!ready || locked()) return;
    sendPos(e);
    if (guiOpen()) {
      // Le survol du menu est calculé au rendu : on attend deux images pour qu'il tienne
      // compte de la position du clic (le geste reste valable pour reprendre la capture).
      requestAnimationFrame(function () { requestAnimationFrame(function () {
        if (!guiOpen() || (Module._pf_guihover && Module._pf_guihover())) return;   // clic sur le menu
        exec('cleargui');                // clic hors du menu : on le ferme et on reprend la visite
        requestLock();
      }); });
      return;
    }
    requestLock();                       // clic dans le jeu hors menu : reprise de la capture
  });
  document.addEventListener('keydown', resumeAudio);
  document.addEventListener('pointerlockchange', function () {
    var l = locked();
    call('pf_grab', ['number'], [l ? 1 : 0]);
    if (!l && !quitting && performance.now() > expectUnlockUntil && !guiOpen()) {
      // Échap, alt-tab, perte de focus : menu principal tout de suite (un seul Échap)
      exec('showgui main');
    }
    if (l) expectUnlockUntil = 0;
    updateUi();
  });
  document.addEventListener('pointermove', function (e) {
    if (!ready) return;
    if (!locked()) { sendPos(e); return; }
    var dx = 0, dy = 0, list = e.getCoalescedEvents ? e.getCoalescedEvents() : [];
    if (list && list.length > 1) { for (var i = 0; i < list.length; i++) { dx += list[i].movementX; dy += list[i].movementY; } }
    else { dx = e.movementX; dy = e.movementY; }
    if (dx || dy) Module._pf_mousemove(dx | 0, dy | 0);
  });
  document.addEventListener('pointerlockerror', function () {
    console.warn('pointer lock refusé (clic nécessaire, ou iframe sans allow="pointer-lock")');
    updateUi();
  });
  setInterval(updateUi, 250);

  // --- Plein écran (menu principal ou touche F) ----------------------------------
  function toggleFullscreen() {
    if (document.fullscreenElement) { if (document.exitFullscreen) document.exitFullscreen(); return; }
    var el = document.documentElement, wasLocked = locked();
    if (!el.requestFullscreen) return;
    if (wasLocked) expectUnlockUntil = performance.now() + 1500;   // le changement de mode peut libérer la souris
    var p = el.requestFullscreen();
    // la capture a survécu au changement de mode : un Échap ultérieur doit rouvrir le menu
    if (p && p.then) p.then(function () { if (locked()) expectUnlockUntil = 0; else if (wasLocked) requestLock(); })
      .catch(function (e) { console.warn('plein écran refusé : ' + e); });
  }

  // --- Quitter le jeu ------------------------------------------------------------
  function quitGame() {
    quitting = true;
    exec('cleargui; disconnect');
    if (locked()) document.exitPointerLock();
    updateUi();
    setTimeout(function () {
      if (window.parent && window.parent !== window) window.parent.postMessage({ type: 'cube2:quit' }, location.origin);
      else location.href = '/';
    }, 200);
  }

  // Flèches / Tab ne doivent pas faire défiler la page ni sortir de l'iframe.
  window.addEventListener('keydown', function (e) {
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Tab'].indexOf(e.code) >= 0) e.preventDefault();
  });
})();
