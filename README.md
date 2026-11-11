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
- **Des salles thématisées**, chacune avec ses textures, ses décors 3D, sa couleur de
  lumière et son ambiance sonore :

  | Salle | Thème | Décors | Ambiance sonore |
  |---|---|---|---|
  | Hall | marbre | accueil, plantes, bancs | souffle + carillon |
  | Profil | bibliothèque / bureau | étagères, bureau + écran, lampe, raquette de badminton | tic-tac, nappe chaude |
  | Compétences | salle serveur / labo | baies serveurs à LED, paillasse, câbles | ventilateurs + bips |
  | Leboncoin | garage auto | voiture, pneus, servante, panneau « À vendre » | moteur au ralenti |
  | Magic Shape Generator | salle rythmique néon | planètes feu/glace (ADOFAI), anneau néon, dalles | boucle de batterie 120 bpm |
  | Mineport | monde en voxels | arbre et blocs voxel, minerai | vent + oiseaux |
  | Cube 2 Portfolio | arène | piliers, cible, caisses | bourdon d'arène |
  | Portfolio OS | bureau Ubuntu géant | moniteur géant (bureau julesrogue.fr), clavier | nappe « démarrage » + clavier |
  | Certificats | salle des trophées | trophées, diplôme Cisco, médaille | accord solennel |
  | Tux World | banquise | manchots, igloo, bonhomme de neige, neige qui tombe | vent arctique + cris de manchots |
  | Contact | bureau de poste | guichet, boîtes aux lettres, colis, téléphone | sonnerie + tampon |

- **Des monstres** : des « bugs » (Virus, Bug, Glitch, Malware, Spam…) gardent les salles
  et attaquent les visiteurs, avec leurs propres modèles et cris.
- **Des armes** (pistolet, fusil à pompe, mitrailleuse, lance-roquettes, fusil de
  précision, lance-grenades, scie) avec munitions, santé et armure à ramasser dans les
  salles. Le PvP entre visiteurs est **désactivé par défaut** (variable serveur `pfpvp`).
- **Des sons** : tirs, explosions, impacts, pas, saut, ramassages, douleur, cris des
  monstres et une ambiance par salle — **tous synthétisés** par `tools/gen_sounds.py`.
- **Une histoire** : le serveur du portfolio a « planté », 10 fragments se sont éparpillés
  et des bugs rôdent. L'intro, la restauration de chaque fragment (`[3/10] ...`) et la fin
  s'affichent en **messages courts dans la console d'origine** ; le détail de chaque sujet
  est écrit sur les **panneaux muraux** des salles. Aucune surcouche d'interface n'est
  ajoutée : HUD, console, tableau des scores et menus sont ceux de Cube 2.
- **Le multijoueur** : tous les visiteurs et les monstres sont partagés sur le même
  serveur ; chat avec `T`.
- **Le pseudo** est repris du compte du portfolio via `?name=<pseudo>`.

Commandes : `ZQSD`/`WASD`/flèches, souris (clic = tir, clic droit = saut), `1`–`6` /
molette (armes), `Espace` (saut), `T`/`Entrée` (chat), `Tab` (scores),
`C` (3ᵉ personne), `Échap` (menu, relâche la souris).

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
  └─ serveur dédié Cube 2 natif (même code source, carte forcée, monstres maintenus)
```

### Les monstres en multijoueur

Les monstres sont les **bots de Cube 2** (`fpsgame/aiman.h`, `ai.cpp`), et non les monstres
du mode solo (`monster.cpp`, purement locaux). C'est le mécanisme multijoueur d'origine du
moteur : le **serveur fait autorité** sur leur existence, leur santé, les dégâts, les morts
et la réapparition ; il confie la simulation de chaque monstre (déplacement, visée) à un
client « propriétaire », qui diffuse ses positions à tout le monde. Tous les joueurs voient
donc les mêmes monstres au même endroit ; si le propriétaire part, le serveur réassigne ses
monstres à un autre visiteur. Adaptations :

- le serveur maintient `pfmonsters` monstres (5 par défaut, habileté `pfmonsterskill` = 20)
  tant qu'au moins un visiteur est connecté ;
- les monstres ne ciblent que les humains et ne se blessent pas entre eux ;
- ils apparaissent dans les salles (départs dédiés), naviguent grâce à un graphe de points
  de passage généré avec la carte (`portfolio.wpt`) et réapparaissent après leur mort ;
- modèle (virus, bug, glitch) et cris dépendent du type de monstre ;
- un onglet masqué continue de faire tourner la simulation (boucle `setTimeout` au lieu de
  `requestAnimationFrame`), pour ne pas geler les monstres qu'il pilote.

Le joueur qui meurt réapparaît au Hall (clic ou attente, comme dans Cube 2).

Le client démarre d'abord la carte **en solo** (affichage immédiat), puis rejoint le
serveur. Si le serveur est injoignable, la visite reste jouable hors ligne
(`?offline=1` force ce mode).

### Arborescence

| Chemin | Rôle |
|---|---|
| `engine/` | Sous-ensemble **vendorisé et modifié** du moteur (C++) : `engine/`, `fpsgame/`, `shared/`, `enet/` |
| `engine/fpsgame/portfolio.cpp` | Module de visite : zones (`pfzone`), progression de l'histoire (console), pas, éclairage auto |
| `engine/fpsgame/aiman.h`, `ai.cpp`, `server.cpp` | Monstres (bots) maintenus par le serveur, PvP désactivable |
| `engine/engine/pfweb.cpp` | Aides web (cubescript depuis JS, redimensionnement, capture de la souris) |
| `engine/engine/webstubs.cpp` | Enregistreur vidéo retiré, fonctions GL desktop neutralisées |
| `engine/Makefile` | `make web` (Emscripten) et `make server` (serveur natif) |
| `game/data/` | Scripts cubescript (menus, touches, config) — `glsl.cfg`, `stdlib.cfg`, `keymap.cfg` d'origine |
| `game/packages/fonts/` | Police DejaVu Sans (format Cube 2) |
| `tools/content.py` | **Contenu de la visite** (textes des zones, panneaux, histoire) |
| `tools/gen_map.py` | Génère `portfolio.ogz` (octree OCTA v33), `portfolio.cfg` (textures, décors, ambiances, zones) et `portfolio.wpt` (navigation des monstres) |
| `tools/gen_assets.py` | Génère les images (UI, icônes du HUD, textures thématiques, panneaux à texte, particules) |
| `tools/gen_models.py`, `tools/objmodel.py` | Génère tous les modèles 3D (avatar, armes, monstres, objets, décors) au format OBJ |
| `tools/gen_sounds.py` | Synthétise tous les sons (effets + ambiances de salle) en WAV |
| `web/` | Coquille HTML/JS minimale (pseudo, URL du WebSocket, capture de la souris au clic, iframe) |
| `server/relay.js` | Serveur web + pont WebSocket ⇄ UDP |
| `docker/`, `docker-compose.yml` | Images web (build WASM inclus) et serveur dédié |
| `scripts/build-web.sh` | Build local du client dans `dist/cube2/` |

## Allègements par rapport à Sauerbraten

- **Aucune carte, aucun modèle, son ou texture d'origine** : tout est généré par les
  scripts de `tools/` (images, modèles OBJ low poly, sons WAV synthétisés).
- **Une seule carte et un seul mode** (« visite », dérivé du ffa), limite de temps à 24 h,
  votes de carte forcés sur la visite ; **éditeur désactivé** ; enregistreur vidéo retiré.
- Son via SDL_mixer **sans décodeur** (WAV uniquement, pas d'Ogg/MP3 embarqué).
- Pas de lightmaps dans la carte : l'éclairage coloré est calculé par le client au
  chargement (`calclight -1`, ≈ 1 s).
- Menus d'origine réduits au strict nécessaire (pseudo, options, recommencer l'histoire).

Poids du client (build `-Oz`) : `cube2.wasm` 2,2 Mo (**0,95 Mo** gzip), `cube2.data`
4,6 Mo (**3,4 Mo** gzip, dont 2,4 Mo de sons), `cube2.js` 233 Ko (**55 Ko** gzip) :
**≈ 4,4 Mo transférés**.

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
Emscripten SDL2/SDL2_mixer/zlib/libpng/libjpeg récupérés automatiquement par `emcc`).

### En local (développement)

```bash
source ~/emsdk/emsdk_env.sh        # Emscripten 6.x
./scripts/build-web.sh             # -> dist/cube2/
python3 -m http.server -d dist 8099   # puis http://127.0.0.1:8099/cube2/?offline=1
make -C engine server              # serveur natif (nécessite zlib1g-dev)
```

### Modifier le contenu

Tout le texte est dans `tools/content.py` ; le plan de la carte (salles, portes,
panneaux, décors, objets, monstres, lumières, ambiances) est dans `tools/gen_map.py`. Relancer `./scripts/build-web.sh`
(ou `docker compose up -d --build`).

## Intégration dans le portfolio

- Le conteneur web écoute sur `127.0.0.1:8083` et sert tout sous le préfixe `/cube2/`.
- Le client construit l'URL du WebSocket à partir de `location` :
  `ws(s)://<hôte><chemin-de-la-page>ws`, soit `wss://julesrogue.fr/cube2/ws` en prod.
- Le pseudo est lu depuis `?name=` : accents retirés, seuls `A-Z a-z 0-9 _ . -` sont
  gardés, 15 caractères max ; sinon un nom `inviteNNN`.
- Iframe : `<iframe src="/cube2/?name=..." allow="fullscreen; pointer-lock" allowfullscreen></iframe>`
  (si l'iframe est `sandbox`, ajouter `allow-scripts allow-same-origin allow-pointer-lock`).
  La souris n'est capturée **que sur un clic dans le canvas** (jamais sur un simple focus
  de l'iframe) ; `Échap` la relâche, et la barre du portfolio reste cliquable.

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
- **Tous les assets du jeu** — textures, panneaux, icônes, particules, modèles 3D
  (avatar, armes, monstres, objets, décors), sons et ambiances, carte et points de
  passage — sont des **créations originales générées par les scripts de `tools/`**
  (`gen_assets.py`, `gen_models.py`, `gen_sounds.py`, `gen_map.py`), sans aucun fichier
  tiers : même licence que le projet (zlib). Aucun asset de Sauerbraten (modèles, sons,
  textures, sous licences diverses dont CC BY-NC) n'est embarqué.
- Code propre au projet (module portfolio, scripts, coquille web, relais) : licence zlib.

Contenu du portfolio : © Jules ROGUE.
