# Crédits et licences

Projet non commercial (portfolio étudiant, BTS SIO SLAM). Les assets de Cube 2:
Sauerbraten ne sont **pas** versionnés dans ce dépôt : ils sont téléchargés au build
depuis l'archive officielle, avec une somme de contrôle épinglée, puis réduits au
sous-ensemble listé dans `tools/sauer_assets.txt`. Les fichiers de licence et les
readme de chaque dossier sont copiés avec les assets dans le paquet de données
(`cube2.data`).

- **Archive** : `sauerbraten_2020_12_29_linux.tar.bz2` (Cube 2: Sauerbraten, édition « Justice » 2020)
  — <https://sourceforge.net/projects/sauerbraten/files/sauerbraten/2020_11_29/>
  — SHA-256 `cdba7c4a47cefd30d0afdd6a912199a1384319cf1619923cb7189e72e468be70`

## Code

| Élément | Auteur(s) | Licence |
|---|---|---|
| Moteur Cube 2: Sauerbraten (`engine/`) | W. van Oortmerssen, L. Salzman, M. Dysart, R. Pointon, Q. Reeves et contributeurs | zlib |
| Portage Emscripten (base de `engine/`) | Caleb Foust — [cfoust/sour](https://github.com/cfoust/sour), issu de [kripken/BananaBread](https://github.com/kripken/BananaBread) | MIT (Sour), zlib (BananaBread) |
| ENet | Lee Salzman | MIT |
| Code propre au projet (module portfolio, scripts, coquille web, relais) | Jules ROGUE | zlib |

## Assets de Sauerbraten repris (sans modification de contenu)

Optimisations appliquées au build : fichiers `.dds` ignorés, images des modèles réduites
(512 px pour le joueur, ses armes et les monstres, 256 px pour le reste) et PNG opaques
convertis en JPEG, reflets d'environnement (envmap) retirés des `.cfg` des modèles.

| Assets | Auteur(s) | Licence / conditions |
|---|---|---|
| `data/` : scripts d'origine (menus, touches, shaders `glsl.cfg`, sons…) et images d'interface | Équipe Sauerbraten | zlib (licence du jeu) ; `guioverlay`, `guiskin`, `guislider` : CC BY-NC-SA, Markus « makkE » Bekel (`data/license.txt`) |
| `packages/fonts`, `packages/hud`, `packages/icons`, `packages/crosshairs`, `packages/blendbrush`, `packages/particles`, `packages/textures` (notexture, ciel) | Équipe Sauerbraten ; police DejaVu (Bitstream Vera / domaine public) ; icônes de `blip_*` dérivées de Glyphish (CC BY 3.0) | licence du jeu / licences indiquées dans les dossiers |
| Joueur Mr. Fixit (`models/mrfixit`), armes à la 1re personne (`models/hudguns`), armes en main (`models/vwep`) | John « geartrooper » Siar, Anthony « Acord » Cord, Nieb | CC BY-NC 3.0 |
| Apparences IronSnout X10K (`models/snoutx10k`) | John « geartrooper » Siar | CC BY 3.0 (`license.txt`) |
| Apparences Inky (`models/inky`) et Captain Cannon (`models/captaincannon`) | John « geartrooper » Siar | CC BY-NC 3.0 (`license.txt`) |
| Objets : munitions, santé, armure, boost, quad, projectiles, débris, téléporteur | Équipe Sauerbraten / makkE | CC BY-NC-SA (`models/ammo/license.txt`…) |
| Monstres : rat (Ratamahatta), slith, bauul, hellpig | Auteurs Quake II indiqués dans chaque readme (rat/bauul : non commercial, crédit ; hellpig : libre avec crédit ; slith : libre redistribution) | readme de chaque dossier |
| Décors `models/dcp` (plantes, bancs, consoles, tonneaux, piliers, arbres, réverbères, roseaux, poubelles, cartons, palettes, bougies…) | Dietmar « dcp » Pier | libre pour les cartes Cube (`Readme.txt`) |
| Décors `models/mitaman/locker1`, `locker3` (casiers) | Mike « MitaMAN » Poeschl | libre, crédit demandé (`locker1.txt`, `locker3.txt`) |
| Décors `models/psionic/barrel2`, `crate4` (tonneau, caisse) | Psionic | libre, y compris commercial, crédit apprécié (`Psionic permission.txt`) |
| Décors `models/xeno/box1`, `box2` (caisses en bois) | Matthias « Xeno » Breuer | « Feel free to do whatever you want with those » (`Xeno permission.txt`) |
| Décors `models/objects` (table, chaise, lampe, panneau, wagonnet, lanterne, puits, banc) | makkE, Kurtis Kesler | CC BY-NC-SA 2.5 |
| Eau : `golgotha/water2` | Jeu Golgotha (art versé au domaine public, readme fourni) | libre usage non commercial |
| Eau : `textures/water*`, `waterfall*`, reflets `caustics` ; herbe animée `textures/grass.png` | Équipe Sauerbraten | licence du jeu |
| Décor `models/aftas/caixa` | Jésus « aftasardem » Maia | libre pour les cartes Sauerbraten/Cube |
| Textures `ik2k`, `ikbase` | Iikka Keränen | distribution libre non commerciale, crédit |
| Textures `tech1soc` | Sock | crédit demandé (readme fourni) |
| Textures `philipk` | Philip Klevestav (set PK01) | libres de modification (readme fourni) |
| Skybox `skyboxes/remus/sky01` | Remus | libre usage personnel et commercial, crédit (readme fourni) |
| Sons du jeu (`aard`, `q009`, `free`, `ppm`, `nieb`, `soundsnap`, `awesund`, `blindabuser`) | aard (domaine public), q009 (CC BY-SA 3.0), sons libres « free », Sin sound pack (awesund), Soundsnap (licence libre), ppm, nieb | `packages/sounds/readme.txt` et licences des dossiers |
| Ambiances (`sounds/ambience`) | Bahutan, Slanesh, Therac 25, RHumphries, dobroide, acclivity, oyes, ignotus, fresco, WIM (freesound) | CC Sampling+ 1.0 (`authors.txt`) |
| Ambiances `sounds/razgriz` (energy_hum_01, high_wind_01) | Sllarson (CC BY), ERR0 (CC0) via freesound | voir `license.txt` |
| Ambiance `sounds/akari/stadiumsound` | — | libre (voir `README.txt`) |

Le modèle Ogro (`models/ogro2`), dérivé d'un modèle Quake II sans licence de redistribution
explicite, n'est pas repris.

## Assets maison (aucun équivalent dans le jeu de base)

Générés par `tools/gen_assets.py` (licence zlib du projet) : panneaux muraux avec le
texte du portfolio, textures de blocs façon voxels (Mineport), neige et glace (Tux World),
fond d'écran du bureau Portfolio OS, vignette de la carte. La carte elle-même
(`portfolio.ogz`, `.cfg`, `.wpt`) est générée par `tools/gen_map.py`.

## Musique (chargée à la demande, hors paquet de données)

| Titre | Auteur | Source | Licence |
|---|---|---|---|
| Stage 1 | Juhani Junkala | [« 4 Chiptunes (Adventure) », OpenGameArt](https://opengameart.org/content/4-chiptunes-adventure) | CC0 1.0 (domaine public) |
| Stage 2 | Juhani Junkala | idem | CC0 1.0 |
| Stage Select | Juhani Junkala | idem | CC0 1.0 |

La licence CC0 n'impose pas de crédit ; l'auteur est néanmoins cité. Les fichiers sont
téléchargés depuis OpenGameArt et vérifiés par somme SHA-256 (`scripts/fetch-assets.sh`).
