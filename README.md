# Cube 2 Portfolio — la visite 3D du portfolio de Jules ROGUE

Une version **minimale et modifiée de Cube 2: Sauerbraten**, compilée en **WebAssembly**
(Emscripten + WebGL 2), jouable dans le navigateur et **multijoueur**. Elle sert de
« visite » interactive du portfolio [julesrogue.fr](https://julesrogue.fr) : chaque salle
de la carte présente une partie du parcours de Jules (profil, compétences BTS SIO SLAM,
projets, certificats, Tux World, contact), avec une petite histoire à suivre.

> Projet réalisé dans le cadre du BTS SIO option SLAM.

## Ce que contient la visite

- **Une carte dédiée** (`portfolio.ogz`) **générée par script** (`tools/gen_map.py`) :
  Hall d'accueil, salles Profil, Compétences, Certificats, Tux World, Contact et une
  Galerie des projets à cinq stands (Leboncoin, Magic Shape Generator, Mineport,
  Cube 2 Portfolio, Portfolio OS).
- **Des panneaux muraux** (textures générées avec le texte du portfolio) et **des textes
  HUD** déclenchés par zone : en entrant dans une salle, sa présentation s'affiche.
- **Une histoire** : le serveur du portfolio a « planté » et son contenu s'est éparpillé
  en 10 fragments. L'intro l'explique à l'arrivée, l'objectif en haut à droite suit la
  progression (x/10), chaque salle découverte affiche une notification, et une fin
  s'affiche quand les 10 fragments sont restaurés.
- **Le multijoueur** : tous les visiteurs se retrouvent sur le même serveur, se voient
  (avatar + pseudo au-dessus de la tête) et peuvent discuter (touche `T`).
  La visite est **pacifique** : pas de tir, pas de dégâts.
- **Le pseudo** est repris du compte du portfolio via `?name=<pseudo>`.

Commandes : `ZQSD`/`WASD`/flèches, souris, `Espace` (saut), `T`/`Entrée` (chat),
`Tab` (joueurs), `C` (3ᵉ personne), `H`/`F1` (aide), `Échap` (menu).

## Architecture

```
navigateur (iframe /cube2/?name=X)
  └─ cube2.wasm : moteur Cube 2 + ENet ; les sockets UDP sont émulées par
     Emscripten au-dessus d'un WebSocket  ──►  wss://<hôte>/cube2/ws
                                                   │
conteneur « cube2-portfolio » (Node.js, 127.0.0.1:8083)
  ├─ sert /cube2/ (HTML, JS, .wasm en application/wasm, .data, gzip)
  └─ pont WebSocket ⇄ UDP : 1 socket UDP par visiteur ──►  cube2-server:28785/udp
                                                   │
conteneur « cube2-portfolio-server » (réseau interne Docker uniquement)
  └─ serveur dédié Cube 2 natif (même code source, mode ffa pacifique, carte forcée)
```

Le client démarre d'abord la carte **en solo** (affichage immédiat), puis rejoint le
serveur. Si le serveur est injoignable, la visite reste jouable hors ligne
(`?offline=1` force ce mode).

### Arborescence

| Chemin | Rôle |
|---|---|
| `engine/` | Sous-ensemble **vendorisé et modifié** du moteur (C++) : `engine/`, `fpsgame/`, `shared/`, `enet/` |
| `engine/fpsgame/portfolio.cpp` | Module de visite : zones (`pfzone`), progression, panneaux HUD, histoire |
| `engine/engine/pfweb.cpp` | Aides web (exécution de cubescript depuis JS, redimensionnement, rectangles HUD) |
| `engine/engine/nosound.cpp`, `webstubs.cpp` | Son et enregistreur vidéo retirés ; fonctions GL desktop neutralisées |
| `engine/Makefile` | `make web` (Emscripten) et `make server` (serveur natif) |
| `game/data/` | Scripts cubescript (menus, touches, config) — `glsl.cfg`, `stdlib.cfg`, `keymap.cfg` d'origine |
| `game/packages/fonts/` | Police DejaVu Sans (format Cube 2) |
| `tools/content.py` | **Contenu de la visite** (textes des zones, panneaux, histoire) |
| `tools/gen_map.py` | Génère `portfolio.ogz` (octree OCTA v33) + `portfolio.cfg` (textures, zones) |
| `tools/gen_assets.py` | Génère toutes les images (UI, textures, panneaux à texte, avatar OBJ) |
| `web/` | Coquille HTML/JS (pseudo, URL du WebSocket, plein écran, focus, iframe) |
| `server/relay.js` | Serveur web + pont WebSocket ⇄ UDP |
| `docker/`, `docker-compose.yml` | Images web (build WASM inclus) et serveur dédié |
| `scripts/build-web.sh` | Build local du client dans `dist/cube2/` |

## Allègements par rapport à Sauerbraten

- **Aucune carte officielle**, aucun modèle, son ou texture d'origine : seule la carte
  générée est embarquée, avec des textures et un avatar générés par script.
- **Son retiré** (SDL_mixer non lié) et **enregistreur vidéo retiré**.
- **Éditeur désactivé** (`allowedittoggle` → 0, aucune touche d'édition, cfg d'édition vides).
- **Armes/dégâts désactivés** côté client (pas de tir) et côté serveur (aucun dégât),
  HUD santé/munitions masqué, pas de bots, une seule carte et un seul mode (ffa),
  limite de temps portée à 24 h, votes de carte forcés sur la visite.
- Menus réduits au strict nécessaire (pseudo, aide, options, recommencer l'histoire).

Poids du client (build `-Oz`) : `cube2.wasm` 1,9 Mo (**765 Ko** gzip), `cube2.data`
0,88 Mo (**707 Ko** gzip), `cube2.js` 233 Ko (**55 Ko** gzip) : **≈ 1,5 Mo transférés**.

## Construire et lancer

### Avec Docker (recommandé)

```bash
docker compose up -d --build
# client :    http://127.0.0.1:8083/cube2/?name=MonPseudo
# websocket : ws://127.0.0.1:8083/cube2/ws
# santé :     http://127.0.0.1:8083/cube2/health
```

Le build de l'image web compile le moteur avec l'image officielle
`emscripten/emsdk:6.0.6` (aucune source tierce à télécharger à part les ports
Emscripten SDL2/zlib/libpng/libjpeg récupérés automatiquement par `emcc`).

### En local (développement)

```bash
source ~/emsdk/emsdk_env.sh        # Emscripten 6.x
./scripts/build-web.sh             # -> dist/cube2/
python3 -m http.server -d dist 8099   # puis http://127.0.0.1:8099/cube2/?offline=1
make -C engine server              # serveur natif (nécessite zlib1g-dev)
```

### Modifier le contenu

Tout le texte est dans `tools/content.py` ; le plan de la carte (salles, portes,
panneaux) est en tête de `tools/gen_map.py`. Relancer `./scripts/build-web.sh`
(ou `docker compose up -d --build`).

## Intégration dans le portfolio

- Le conteneur web écoute sur `127.0.0.1:8083` et sert tout sous le préfixe `/cube2/`.
- Le client construit l'URL du WebSocket à partir de `location` :
  `ws(s)://<hôte><chemin-de-la-page>ws`, soit `wss://julesrogue.fr/cube2/ws` en prod.
- Le pseudo est lu depuis `?name=` : accents retirés, seuls `A-Z a-z 0-9 _ . -` sont
  gardés, 15 caractères max ; sinon un nom `inviteNNN`.
- Iframe : `<iframe src="/cube2/?name=..." allow="fullscreen; pointer-lock" allowfullscreen></iframe>`
  (si l'iframe est `sandbox`, ajouter `allow-scripts allow-same-origin allow-pointer-lock`).
  Un clic dans le jeu donne le focus clavier et capture la souris ; bouton plein écran en bas à gauche.

Bloc nginx (hôte) :

```nginx
location /cube2/ {
    proxy_pass http://127.0.0.1:8083;          # sans / final : le préfixe /cube2/ est conservé
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
location = /cube2/ws {
    proxy_pass http://127.0.0.1:8083;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
}
```

## Crédits et licences

- **Moteur Cube 2: Sauerbraten** — © Wouter van Oortmerssen, Lee Salzman, Mike Dysart,
  Robert Pointon, Quinton Reeves et contributeurs — **licence zlib**
  (voir `engine/readme_source.txt`). <http://sauerbraten.org>
- **Portage Emscripten** — le code de `engine/` est dérivé de
  [cfoust/sour](https://github.com/cfoust/sour) (licence MIT, © Caleb Foust), lui-même
  issu de [kripken/BananaBread](https://github.com/kripken/BananaBread) (zlib).
  Les modifications « portfolio » sont signalées par des commentaires `PORTFOLIO`.
- **ENet** — © Lee Salzman — licence MIT (`engine/enet/LICENSE`).
- **Scripts de données** `game/data/glsl.cfg`, `stdlib.cfg`, `keymap.cfg` — Sauerbraten
  (zlib). Les fichiers d'interface sous licence CC BY-NC-SA de Sauerbraten
  (`guiskin`, `guioverlay`, `guislider`) **ne sont pas** utilisés : ils sont remplacés
  par des images générées.
- **Police** `game/packages/fonts/` — DejaVu Sans (licence Bitstream Vera / domaine
  public, voir `game/packages/fonts/default.txt`), au format de police Cube 2.
- **Textures, panneaux, avatar, carte** — générés par les scripts de `tools/`
  (aucun asset tiers), sous la même licence que le projet.
- Code propre au projet (module portfolio, scripts, coquille web, relais) : licence zlib.

Contenu du portfolio : © Jules ROGUE.
