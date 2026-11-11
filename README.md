# Cube 2 Portfolio — le portfolio de Jules ROGUE dans Cube 2: Sauerbraten

**Cube 2: Sauerbraten** compilé en **WebAssembly** (Emscripten + WebGL 2), jouable dans
le navigateur et **multijoueur**. Il sert de visite interactive du portfolio
[julesrogue.fr](https://julesrogue.fr) : une carte **en extérieur**, sous la skybox du
jeu, où chaque bâtiment présente une partie du parcours de Jules (profil, compétences
BTS SIO SLAM, projets, certificats, Tux World, contact). Le jeu reste fidèle à l'original :
mêmes armes, sons, modèles, HUD, menus et règles (PvP compris), avec des monstres, des
phases de parkour, des combats d'arène et un boss final.

> Projet réalisé dans le cadre du BTS SIO option SLAM.

## Le jeu

- **Lancement direct dans la carte**, sans menu principal ; un clic dans le jeu capture la
  souris, et `Échap` la relâche et ouvre le menu d'origine. L'intro narrative est racontée
  par le portfolio avant l'affichage du jeu ; en jeu, seuls de courts messages s'affichent
  dans la console d'origine.
- **Carte extérieure** générée par script (`tools/gen_map.py`), éclairée par le soleil et
  la lumière du ciel (`sunlight`, `skylight`, skybox `remus/sky01`). Une place d'accueil
  est entourée de bâtiments reliés par des chemins :

  | Lieu | Thème | Éléments |
  |---|---|---|
  | Place d'accueil | pavés, réverbères | panneau d'accueil, départs des joueurs |
  | Profil | bureau / bibliothèque | papier peint, parquet, table, chaise, lampe ; ambiance feu de cheminée |
  | Compétences | salle serveur | panneaux informatiques, consoles, biotanks ; bourdonnement |
  | Galerie des projets | 5 stands | garage Leboncoin, néons Magic Shape (planète et lune), voxels Mineport à ciel ouvert, arène Cube 2, bureau Ubuntu Portfolio OS |
  | Certificats | salle des trophées | vases, coffre, lanterne ; fontaine |
  | Tux World | banquise à ciel ouvert | neige, blocs de glace, neige qui tombe ; vent |
  | Contact | bureau de poste | sacs postaux, coffre, panneau ; vent |
  | Colisée | arène de combat | murets, piliers-abris, armes et munitions |

- **Progression** (10 fragments du portfolio, annoncés dans la console) :
  1. **exploration** : Profil, Compétences, Projets (les 5 stands), Certificats, Tux World,
     Contact ;
  2. **parkour** : *Parcours des piliers*, une série de piliers puis un jump pad, et *Parcours
     des toits*, avec un jump pad vers le toit de la galerie, le toit du Profil, puis une
     poutre jusqu'au toit des Compétences. Une chute ramène au départ du parcours sans
     mourir ; à l'arrivée, un téléporteur ramène à la place ;
  3. **combat** : en entrant sur la banquise ou dans le Colisée, une vague de monstres se
     déclenche. L'arène reste fermée (mur d'énergie en particules) jusqu'à ce que la vague
     soit nettoyée ;
  4. **boss** : avec les 10 fragments, le boss **KernelPanic** (un bauul du jeu de base, 1500
     PV, armure, lance-roquettes, dégâts doublés) apparaît au Colisée avec 3 renforts. Sa
     défaite conclut l'histoire.
- **Multijoueur** : PvP, frags, morts et réapparition selon les règles d'origine (le
  serveur fait autorité) ; chat avec `T`, scores avec `Tab`.
- **Monstres** : ce sont les *bots* multijoueur du moteur (`aiman.h`), avec les modèles et
  les cris des monstres du mode solo (rat, slith, bauul, hellpig). Le serveur décide de leur
  nombre, de leur santé, des vagues et du boss, et confie la simulation de chaque monstre à
  un client, qui la diffuse à tous. Tout le monde voit donc les mêmes monstres. Ils
  naviguent grâce à un graphe de points de passage généré avec la carte (`portfolio.wpt`),
  à l'intérieur comme à l'extérieur. Ils n'attaquent que les joueurs humains et ne se
  blessent pas entre eux.

## Fidélité au jeu de base : d'où viennent les assets

- **Du jeu de base, sans retouche de contenu** : armes à la 1re personne et en main (Mr. Fixit),
  modèle de joueur, objets, monstres, sons et ambiances, textures des bâtiments et du sol,
  décors (plantes, bancs, réverbères, arbres, consoles…), skybox, HUD, police, icônes,
  particules, scripts et menus d'origine (`data/*.cfg`). Ces assets **ne sont pas dans le
  dépôt** : `scripts/fetch-assets.sh` télécharge l'archive officielle Sauerbraten 2020
  (SourceForge, somme SHA-256 épinglée) et `tools/prepare_sauer.py` n'en extrait que le
  sous-ensemble listé dans `tools/sauer_assets.txt`, avec les licences et readme de chaque
  dossier.
- **Maison, seulement quand rien n'existe dans le jeu de base** (`tools/gen_assets.py`) :
  panneaux muraux avec le texte du portfolio, blocs façon voxels (Mineport), neige et glace
  (Tux World), fond d'écran du bureau Portfolio OS, vignette de la carte.
- **Musique** : 3 morceaux CC0 de Juhani Junkala (OpenGameArt), téléchargés depuis la
  source officielle (somme SHA-256), servis à part dans `/cube2/music/` et **chargés à la
  demande** au premier clic. Ils sont joués en boucle par la commande `music` du jeu (SDL2_mixer + Ogg).

Les licences de chaque asset et les crédits musicaux sont détaillés dans **[CREDITS.md](CREDITS.md)**.

## Caméra et contrôles (navigateur)

- La souris n'est capturée qu'après un vrai pointer lock, demandé au clic dans le canvas
  (`unadjustedMovement` : pas d'accélération du système). Elle n'est jamais capturée sur un
  simple focus de l'iframe, et elle est relâchée à `Échap` ou à la perte du focus.
- Pas de saut de la vue à la capture : les 2 premiers mouvements sont ignorés, ainsi que les
  deltas aberrants (> 300 px).
- Les réglages d'origine (`sensitivity`, `fov`, `invmouse`…) sont conservés.
  `sensitivity` vaut 5 par défaut, car `movementX` est mesuré en pixels CSS. La résolution
  suit la taille de l'iframe et le plein écran, ce qui évite l'étirement de l'image.

Commandes d'origine : `ZQSD`/`WASD`, souris, `Espace`/clic droit (saut), clic (tir), `1`–`6`
et la molette (armes), `T` (chat), `Tab` (scores), `Échap` (menu).

## Architecture

```
navigateur (iframe /cube2/?name=X)
  └─ cube2.wasm : moteur Cube 2 + ENet ; sockets UDP émulées par Emscripten
     au-dessus d'un WebSocket  ──►  wss://<hôte>/cube2/ws
conteneur « cube2-portfolio » (Node.js, 127.0.0.1:8083)
  ├─ sert /cube2/ (HTML, JS, .wasm en application/wasm, .data, musiques .ogg, gzip)
  └─ pont WebSocket ⇄ UDP (1 socket UDP par visiteur)  ──►  cube2-server:28785/udp
conteneur « cube2-portfolio-server » (réseau Docker interne)
  └─ serveur dédié Cube 2 natif (même code source) : carte, monstres, vagues, boss
```

| Chemin | Rôle |
|---|---|
| `engine/` | Moteur (C++), dérivé de Sour, modifications signalées `PORTFOLIO` |
| `engine/fpsgame/portfolio.cpp` | Progression côté client : zones, fragments, parkour, arènes fermées, boss |
| `engine/fpsgame/server.cpp` (`pfgame`), `aiman.h` | Côté serveur : monstres, vagues, boss |
| `game/data/portfolio.cfg` | Réglages propres à la visite (modèles de joueur et de monstres, listes de cartes des menus) |
| `tools/sauer_assets.txt`, `tools/prepare_sauer.py`, `scripts/fetch-assets.sh` | Récupération du sous-ensemble d'assets d'origine et des musiques |
| `tools/gen_map.py`, `tools/gen_assets.py`, `tools/content.py` | Carte, assets maison, textes |
| `web/` | Coquille HTML/JS minimale |
| `server/relay.js` | Serveur web + pont WebSocket ⇄ UDP |

Poids : `cube2.wasm` ≈ 1,0 Mo gzip, `cube2.data` ≈ 16 Mo gzip, `cube2.js` 55 Ko gzip, et
la musique (4,9 Mo) chargée à part, à la demande.

## Construire et lancer

```bash
docker compose up -d --build        # http://127.0.0.1:8083/cube2/?name=MonPseudo
```

Le premier build télécharge l'archive officielle de Sauerbraten (≈ 1 Go). Cette étape est
gardée en cache dans une couche Docker. En local (Emscripten 6.x, python3 + Pillow + numpy) :

```bash
source ~/emsdk/emsdk_env.sh
./scripts/build-web.sh                 # -> dist/cube2/ (cache des téléchargements : third_party/cache)
python3 -m http.server -d dist 8099    # http://127.0.0.1:8099/cube2/?offline=1
```

## Intégration dans le portfolio

- Préfixe `/cube2/` et WebSocket `/cube2/ws` sur la même origine (`ws`/`wss` déduit de
  `location`) ; conteneur web sur `127.0.0.1:8083`.
- Pseudo lu dans `?name=` : accents retirés, seuls `A-Z a-z 0-9 _ . -` sont gardés, 15
  caractères au maximum ; sinon `inviteNNN`.
- Iframe : `<iframe src="/cube2/?name=..." allow="fullscreen; pointer-lock" allowfullscreen>`.

Contenu du portfolio : © Jules ROGUE. Licences : voir [CREDITS.md](CREDITS.md) et `LICENSE`.
