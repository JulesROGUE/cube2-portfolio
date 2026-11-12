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
  est entourée de bâtiments reliés par des chemins. La carte utilise les cubes partiels de
  Cube 2 pour sortir du « tout en blocs » : toits à deux pans, corniches en saillie,
  fenêtres, colonnes de part et d'autre des portes, soubassement en pierre, bordures de
  chemins, collines douces (pentes générées en champ de hauteur), un étang (matériau eau du
  jeu de base) et des lanternes colorées à l'entrée de chaque bâtiment, avec les décors
  d'origine (arbres, buissons, puits, bancs, réverbères, lampes au sol, roseaux), de l'herbe
  animée du moteur (`autograss`) sur les pelouses et les collines, un étang et un ruisseau
  peu profond (eau du jeu de base, fonds en pente douce : on en ressort partout) ; chaque
  pièce est habillée densément de décors du jeu de base selon son thème (mobilier, armoires,
  baies, caisses, tonneaux, plantes, lustres, torches, tuyaux, grilles…), avec lambris,
  tapis ou allées au sol, poutres au plafond, lumières colorées propres à chaque salle et
  particules du moteur (flammes, vapeur) ; dehors, rochers, arbres, bancs près de l'étang et
  lampadaires aux angles de la place. Les décors longent les murs : portes, allées, objets,
  départs, arènes et parcours restent libres (vérifié par la sonde de blocage) :

  | Lieu | Thème | Éléments |
  |---|---|---|
  | Place d'accueil | pavés, réverbères, puits | panneau d'accueil, départs des joueurs |
  | Profil | bureau / bibliothèque | lambris, parquet, poutres, lustre, armoires d'archives, bureau et chaises, lampe de lecture, lierre ; ambiance feu de cheminée |
  | Compétences | salle serveur | deux rangées de baies, allée en caillebotis, vannes, ventilation qui fume, ampoules, lumières bleue et verte, consoles, biotanks ; bourdonnement |
  | Galerie des projets | 5 stands | allée centrale, poutres, suspensions, bancs ; garage Leboncoin (machine, fût), ampoules colorées et braseros Magic Shape, rochers et torche Mineport à ciel ouvert, caisses de l'arène Cube 2, bureau Ubuntu Portfolio OS |
  | Certificats | salle des trophées | tapis rouge, coupes sur socle, lustre, torches allumées, vases, coffre, lanterne ; fontaine |
  | Tux World | banquise à ciel ouvert | neige, blocs de glace, neige qui tombe ; vent |
  | Contact | bureau de poste | casiers à lettres, comptoir, colis sur palette, sacs postaux, suspension, lampe à huile ; vent |
  | Colisée | arène de combat | murets, piliers-abris, armes et munitions |

- **Progression** (10 fragments du portfolio, annoncés dans la console) :
  1. **exploration** : Profil, Compétences, Projets (les 5 stands), Certificats, Tux World,
     Contact ;
  2. **parkour** : *Parcours des piliers*, six marches de 8 unités espacées d'un bloc, et
     *Parcours des poutres*, un jump pad vers une plateforme puis deux poutres étroites. Les
     hauteurs et écarts sont calibrés sur le saut réel du moteur (environ 20 unités de haut
     et 110 de long) et chaque saut est vérifié en headless par un vrai saut (avancer +
     espace). Une chute ramène au départ du parcours sans
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

- **En jeu**, la souris est capturée (pointer lock, demandé au clic dans le canvas, jamais
  sur un simple focus de l'iframe). **Dans les menus**, elle est libre : le curseur est
  celui du système (CSS `cursor`), le moteur ne dessine plus le sien, et sa position
  absolue est transmise au jeu (`pf_mousepos`, en fractions du canvas, donc juste quelle que
  soit la taille de l'iframe, le plein écran ou `devicePixelRatio`).
- **Un seul Échap** : le navigateur réserve le premier Échap à la sortie du pointer lock ;
  toute perte de capture non demandée (Échap, alt-tab, perte de focus) ouvre donc
  directement le menu principal. Un menu ouvert en jeu libère la souris ; quand tous les
  menus se ferment (bouton « Reprendre la visite »), la capture reprend ; sinon un clic
  dans le jeu la reprend (« Clique pour reprendre la visite »).
- `?rawmouse=1` demande `unadjustedMovement` (mouvement brut), avec repli automatique sur
  le pointer lock classique si le navigateur refuse. Le mode relatif de SDL n'est plus
  utilisé (il demandait et relâchait le pointer lock de son côté).
- Les mouvements viennent directement des événements `pointermove` (y compris les événements
  regroupés par le navigateur, `getCoalescedEvents`) : la coquille web les transmet au jeu
  (`pf_mousemove`), qui les cumule et les applique une seule fois par image, pour la vue comme
  pour le curseur des menus. Aucun delta n'est perdu ; seuls les 2 premiers après la capture
  et les valeurs absurdes (> 4000 px) sont ignorés.
- La boucle principale suit `requestAnimationFrame` (pas de `maxfps`, pas d'Asyncify) ; un
  onglet masqué passe en minuterie lente et revient au rythme de l'écran quand il réapparaît.
- Les réglages d'origine (`sensitivity`, `fov`, `invmouse`…) sont conservés, avec leurs
  valeurs par défaut. La résolution
  suit la taille de l'iframe et le plein écran, ce qui évite l'étirement de l'image.

Menu principal (Échap), minimal et en anglais : *Resume*, *Respawn (R)*, *Spectator* /
*Stop spectating*, *Appearance* (choix du modèle de joueur, mémorisé dans le navigateur et
vu des autres joueurs), *Fullscreen (F)*, *Options*, *About*, *Quit game* (confirmation,
déconnexion, puis `postMessage({ type: 'cube2:quit' })` à la page parente, ou retour à `/`
sans parent). Le navigateur de serveurs, le vote de mode/carte, *master* et *disconnect* ont
été retirés. Un clic hors du menu le ferme et reprend la visite. Le pseudo est celui de la
session du portfolio (`?name=`) : `/name` est refusé et le serveur ignore tout changement de
nom après la connexion.

- **Progression vers la page parente** : dans une iframe (`window.parent !== window`), le jeu
  envoie `postMessage({ type: 'cube2:progress', fragments, total: 10, boss }, location.origin)`
  avec `boss` = `'locked'` (fragments incomplets), `'alive'` (KernelPanic est apparu) ou
  `'dead'` (boss vaincu : déchiffrement côté portfolio). Envoyé à l'entrée dans la partie
  (état courant), à chaque fragment, à l'apparition du boss et à sa mort
  (`Module.pfProgress` dans `web/portfolio.js`, appelé par `sendprogress()` du module
  portfolio).

- **Secours** : `R` (ou *Respawn*) fait réapparaître tout de suite sur un départ de la place
  d'accueil, même coincé ou en spectateur (commandes d'origine `suicide` puis `respawn`).
- **Spectateur** : commande d'origine `spectator 1/0` (le serveur l'autorise pour soi sans
  être master) ; vol libre à travers la carte, invisible pour les autres.
- **Réapparition** : toujours sur un départ (`playerstart`) de la place. Mourir dans une
  arène fermée libère de l'arène (avant, la réapparition était aussitôt annulée et l'on
  revenait à l'endroit de sa mort, au milieu des monstres). Une vague qui ne finit pas en
  3 minutes rouvre l'arène.
- **Protection d'apparition** (ajoutée, absente de Sauerbraten) : 3 s d'invulnérabilité,
  appliquée par le serveur (PvP, monstres, dégâts sur soi), signalée par une bulle bleue
  (sphère d'explosion bleue d'origine du moteur) visible de tous, et des étincelles bleues
  à la 1re personne.
- **Histoire** : racontée en jouant, en 5 chapitres dans la console d'origine (le
  portfolio en panne, les salles, les hauteurs, les gardiens des arènes, KernelPanic) puis
  un épilogue ; après chaque fragment, l'objectif suivant est rappelé avec le compte.
  Des inscriptions flottantes (texte en particules du moteur) marquent la place (fragments
  retrouvés), les arènes, les départs des parcours et la galerie. Textes : `tools/content.py`.
- **Armes à ramasser** (objets du jeu de base, réapparition normale gérée par le serveur) :
  fusil à pompe et chaingun près de la place, lance-grenades, pistolet et fusil à pompe sur
  les chemins, armure dans un recoin, et deux lance-roquettes en récompense à l'arrivée des
  parcours (un message d'histoire accompagne la première prise d'une arme importante).
- **Connexion perdue** (serveur redémarré, réseau) : rechargement de la carte et
  reconnexion automatique, avec un délai croissant.

Clavier AZERTY : `Z` `Q` `S` `D` pour se déplacer (les flèches restent actives), souris, `Espace`/clic droit (saut), clic (tir), `1`–`6`
et la molette (armes), `T` (chat), `Tab` (scores), `Échap` (menu). Le jeu reçoit le
caractère de la touche (`keyCode` du navigateur, via SDL), pas sa position physique : `Z`
est bien la touche Z d'un clavier AZERTY.

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
