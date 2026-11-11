#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère la carte « portfolio » de Cube 2 (packages/base/portfolio.ogz, .cfg, .wpt).

Carte EN EXTÉRIEUR : un terrain à ciel ouvert (skybox et soleil du jeu de base)
sur lequel sont posés les bâtiments du portfolio, reliés par des chemins à une
place centrale. Le monde est une grille de voxels de 32 unités (monde de 2048) :
sol plein sous z = FLOOR, air au-dessus, puis on « construit » les bâtiments
(murs, toit, portes) et les blocs de décor. Le script écrit ensuite l'octree au
format OCTA v33 (cubes entièrement pleins ou vides, sans lightmaps : l'éclairage
— soleil + lumières des salles — est calculé par le client au chargement).

Textures : celles du jeu de base (ik2k, ikbase, tech1soc, philipk) ; « pf/ » =
textures maison quand rien d'équivalent n'existe (voxels, banquise, fond d'écran
Portfolio OS, panneaux de texte).

Usage : gen_map.py <sortie> [racines de données où lire la taille des textures...]
"""
import gzip
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from content import ZONES, STORY, FRAGMENTS, cubescript_string  # noqa: E402

VOX = 32            # taille d'un voxel en unités du monde
N = 64              # voxels par axe -> monde de 2048
WORLDSIZE = VOX * N
MAPVERSION = 33
FLOOR = 16          # sol à z = 16 voxels (512 unités)
GROUND = FLOOR * VOX
H = 4               # hauteur intérieure des bâtiments (128 unités)

# Faces Sauerbraten : 0=-X 1=+X 2=-Y 3=+Y 4=-Z 5=+Z
DIRS = [(-1, 0, 0), (1, 0, 0), (0, -1, 0), (0, 1, 0), (0, 0, -1), (0, 0, 1)]

# ---------------------------------------------------------------------------
# Textures (ordre = indices des slots du .cfg ; 0 = ciel)
# ---------------------------------------------------------------------------
TEXTURES, TEXIDX = [], {}
SEARCH = sys.argv[1:]


def addtex(name, line):
    TEXIDX[name] = len(TEXTURES)
    TEXTURES.append((name, line))


def texscale(path, units=32.0):
    """Échelle pour qu'une répétition de la texture couvre `units` unités du monde."""
    from PIL import Image
    for root in SEARCH:
        f = os.path.join(root, "packages", path)
        if os.path.exists(f):
            return units * 8 / Image.open(f).size[0]
    return 1.0


TEX = {
    "default": "ikbase/ik_floor_conc128b.jpg",
    # extérieur
    "grass": ("ik2k/ik_ground_grass128.jpg", 64),
    "path": "ik2k/ik_ground_cobbles128.jpg",
    "plaza": "ik2k/ik_floor_brick128b.jpg",
    "cliff": ("ik2k/ik_cliff256.jpg", 64),
    "roof": "ik2k/ik_wood_planks128b.jpg",
    "ext_brick": "ik2k/ik_brickwall_gry.jpg",
    "ext_conc": "ikbase/ik_cwall04a.jpg",
    "ceiling": "ikbase/ik_floor_conc128b.jpg",
    # salles
    "profil_floor": "ik2k/ik_floor_wood128b.jpg", "profil_wall": "ik2k/ik_wpaperplain128a.jpg",
    "profil_ceil": "ik2k/ik_wood_planks128b.jpg",
    "comp_floor": "tech1soc/grate1b.jpg", "comp_wall": "philipk/pk01_panel01a_d.jpg", "comp_ceil": "tech1soc/blank02a.jpg",
    "gal_floor": "ikbase/ik_floor_conc128a.jpg", "gal_wall": "ikbase/ik_cwall04a.jpg",
    "garage_floor": "ik2k/ik_ground_pavement128.jpg", "garage_wall": "ikbase/ik_cwall06a.jpg",
    "neon_floor": "tech1soc/flr_tmtl_drk.jpg", "neon_wall": "tech1soc/064lig22bb.jpg",
    "mine_floor": "pf/floor_grass.jpg", "mine_wall": "pf/wall_dirt.jpg", "mine_stone": "pf/wall_stone.jpg",
    "arena_floor": "philipk/pk01_floor01a_d.jpg", "arena_wall": "tech1soc/s064-02b.jpg",
    "os_floor": "philipk/pk01_tile_floor01a_d.jpg", "os_wall": "pf/wall_ubuntu.jpg",
    "cert_floor": "ik2k/ik_floor_wood128d.jpg", "cert_wall": "ik2k/ik_wpaperplain128d.jpg",
    "tux_floor": "pf/floor_snow.jpg", "tux_wall": "pf/wall_ice.jpg",
    "post_floor": "ik2k/ik_floor_tile128b.jpg", "post_wall": "ik2k/ik_brick_3216d.jpg",
}

addtex("sky", 'texture 0 "textures/sky.png"')
for _name, _spec in TEX.items():
    _path, _units = (_spec if isinstance(_spec, tuple) else (_spec, 32.0))
    addtex(_name, 'texture 0 "%s" 0 0 0 %g' % (_path, texscale(_path, _units)))

# ---------------------------------------------------------------------------
# Voxels
# ---------------------------------------------------------------------------
solid = bytearray(N * N * N)
roomof = [None] * (N * N * N)      # zone d'un voxel vide (intérieur de bâtiment) ou None = dehors
shellof = {}                       # voxel plein de mur/toit -> bâtiment (texture extérieure)
blocktex = {}                      # voxel plein -> texture imposée (blocs, cloisons)
facetex = {}                       # (voxel plein, face) -> texture imposée (panneaux)
groundtex = {}                     # (x, y) -> texture du sol extérieur


def idx(x, y, z):
    return (z * N + y) * N + x


class Room:
    def __init__(self, rid, box, floor, wall, ceil="ceiling", ext="ext_brick", zone=None):
        self.rid, self.box, self.floor, self.wall, self.ceil, self.ext = rid, box, floor, wall, ceil, ext
        self.zone = zone


# Sol plein
for z in range(FLOOR):
    for y in range(N):
        for x in range(N):
            solid[idx(x, y, z)] = 1


def fill(box, tex=None, shell=None):
    x0, x1, y0, y1, z0, z1 = box
    for z in range(z0, z1):
        for y in range(y0, y1):
            for x in range(x0, x1):
                v = idx(x, y, z)
                solid[v] = 1
                roomof[v] = None
                if tex:
                    blocktex[v] = tex
                if shell:
                    shellof[v] = shell


def carve(box, room):
    x0, x1, y0, y1, z0, z1 = box
    for z in range(z0, z1):
        for y in range(y0, y1):
            for x in range(x0, x1):
                v = idx(x, y, z)
                solid[v] = 0
                roomof[v] = room
                blocktex.pop(v, None)
                shellof.pop(v, None)


def paint(x0, x1, y0, y1, tex):
    for y in range(y0, y1):
        for x in range(x0, x1):
            groundtex[(x, y)] = tex


# Bordure : falaises tout autour du terrain (on ne sort pas de la carte)
for y in range(N):
    for x in range(N):
        if x < 2 or y < 2 or x >= N - 2 or y >= N - 2:
            for z in range(FLOOR, FLOOR + 4):
                solid[idx(x, y, z)] = 1
                blocktex[idx(x, y, z)] = "cliff"

ROOMS, ROOMBYID = [], {}


def building(rid, x0, x1, y0, y1, floor, wall, ceil="ceiling", ext="ext_brick", doors=(), zone=None):
    """Bâtiment : intérieur [x0,x1)x[y0,y1), murs d'un voxel autour, toit, portes.
    doors : (côté 'n','s','e','w', début, fin) le long du mur."""
    r = Room(rid, (x0, x1, y0, y1, FLOOR, FLOOR + H), floor, wall, ceil, ext, zone)
    ROOMS.append(r)
    ROOMBYID[rid] = r
    fill((x0 - 1, x1 + 1, y0 - 1, y1 + 1, FLOOR, FLOOR + H + 1), shell=r)
    carve(r.box, r)
    for side, a, b in doors:
        if side == "s":
            carve((a, b, y0 - 1, y0, FLOOR, FLOOR + 2), r)
        elif side == "n":
            carve((a, b, y1, y1 + 1, FLOOR, FLOOR + 2), r)
        elif side == "w":
            carve((x0 - 1, x0, a, b, FLOOR, FLOOR + 2), r)
        elif side == "e":
            carve((x1, x1 + 1, a, b, FLOOR, FLOOR + 2), r)
    return r


# --- Bâtiments du portfolio, autour de la place centrale --------------------
building("profil", 15, 23, 42, 50, "profil_floor", "profil_wall", "profil_ceil", "ext_brick",
         doors=[("s", 18, 20)], zone="profil")
building("competences", 27, 38, 42, 50, "comp_floor", "comp_wall", "comp_ceil", "ext_conc",
         doors=[("s", 31, 33)], zone="competences")
building("certificats", 15, 23, 12, 20, "cert_floor", "cert_wall", "ceiling", "ext_brick",
         doors=[("n", 18, 20)], zone="certificats")
building("contact", 46, 54, 28, 36, "post_floor", "post_wall", "ceiling", "ext_brick",
         doors=[("w", 31, 33)], zone="contact")
building("galerie", 3, 13, 20, 51, "gal_floor", "gal_wall", "ceiling", "ext_conc",
         doors=[("e", 30, 32)], zone=None)

# Galerie : 5 stands séparés par des cloisons (de x=3 à x=9), allée côté est
for y in (26, 32, 38, 44):
    fill((3, 9, y, y + 1, FLOOR, FLOOR + H), "gal_wall")
STANDS = [("leboncoin", 20, 26, "garage_floor", "garage_wall"),      # garage auto
          ("magic", 27, 32, "neon_floor", "neon_wall"),              # salle rythmique néon
          ("mineport", 33, 38, "mine_floor", "mine_wall"),           # blocs / voxels, ciel ouvert
          ("cube2", 39, 44, "arena_floor", "arena_wall"),            # arène
          ("portfolioos", 45, 51, "os_floor", "os_wall")]            # bureau Ubuntu géant
STANDROOMS = {}
for sid, y0, y1, floor, wall in STANDS:
    sr = Room(sid, (3, 9, y0, y1, FLOOR, FLOOR + H), floor, wall, "sky" if sid == "mineport" else "ceiling", zone=sid)
    STANDROOMS[sid] = sr
    for z in range(FLOOR, FLOOR + H):
        for y in range(y0, y1):
            for x in range(3, 9):
                if not solid[idx(x, y, z)]:
                    roomof[idx(x, y, z)] = sr
# Mineport : toit ouvert sur le ciel, blocs de pierre / terre
for y in range(33, 38):
    for x in range(3, 9):
        v = idx(x, y, FLOOR + H)
        solid[v] = 0
        shellof.pop(v, None)
fill((7, 9, 34, 35, FLOOR, FLOOR + 1), "mine_stone")
fill((3, 4, 33, 35, FLOOR, FLOOR + 2), "mine_wall")

# --- Tux World : banquise à ciel ouvert (pas de bâtiment) --------------------
TUXBOX = (42, 57, 8, 22, FLOOR, FLOOR + 6)
paint(42, 57, 8, 22, "tux_floor")
for b in ((45, 47, 11, 13, FLOOR, FLOOR + 1), (52, 54, 10, 11, FLOOR, FLOOR + 1), (50, 51, 15, 17, FLOOR, FLOOR + 2)):
    fill(b, "tux_wall")
fill((47, 51, 22, 23, FLOOR, FLOOR + 3), "tux_wall")   # mur de glace portant le panneau Tux

# --- Colisée : arène de combat à ciel ouvert, murets et porte au nord ----------
COLISEE = (26, 40, 4, 20, FLOOR, FLOOR + 6)
fill((25, 41, 3, 4, FLOOR, FLOOR + 2), "arena_wall")
fill((25, 41, 20, 21, FLOOR, FLOOR + 2), "arena_wall")
fill((25, 26, 3, 21, FLOOR, FLOOR + 2), "arena_wall")
fill((40, 41, 3, 21, FLOOR, FLOOR + 2), "arena_wall")
carve((31, 35, 20, 21, FLOOR, FLOOR + 2), None)               # porte nord, face à la place
paint(26, 40, 4, 20, "arena_floor")
for b in ((29, 30, 8, 9), (36, 37, 8, 9), (29, 30, 15, 16), (36, 37, 15, 16)):   # piliers-abris
    fill((b[0], b[1], b[2], b[3], FLOOR, FLOOR + 3), "arena_wall")

# --- Parkour 1 « Les piliers » : piliers de plus en plus hauts (nord-est) -------
PK1 = [(42, 44, 41, 43, 1), (46, 48, 41, 43, 2), (50, 52, 41, 43, 3), (54, 56, 41, 43, 4),
       (54, 56, 45, 47, 5), (54, 56, 49, 51, 6), (52, 58, 54, 58, 9)]
for (x0, x1, y0, y1, h) in PK1:
    fill((x0, x1, y0, y1, FLOOR, FLOOR + h), "ext_conc")
# --- Parkour 2 « Les toits » : jump pad vers le toit de la galerie, toit du Profil,
#     poutre jusqu'au toit des Compétences
fill((24, 26, 46, 47, FLOOR + H, FLOOR + H + 1), "roof")      # poutre entre Profil et Compétences

# --- Place centrale (accueil) et chemins -------------------------------------
PLAZA = (25, 39, 24, 38, FLOOR, FLOOR + 6)
paint(25, 39, 24, 38, "plaza")
fill((30, 34, 38, 39, FLOOR, FLOOR + 3), "ext_brick")  # mur d'accueil portant le panneau
for r in ((18, 20, 38, 41), (18, 25, 36, 38),           # -> Profil
          (31, 33, 38, 41),                             # -> Compétences
          (18, 20, 21, 26), (18, 25, 24, 26),           # -> Certificats
          (39, 45, 31, 33),                             # -> Contact
          (14, 25, 30, 32),                             # -> Galerie
          (39, 44, 24, 26), (42, 44, 20, 26),           # -> Tux World
          (32, 34, 21, 24)):                            # -> Colisée
    paint(r[0], r[1], r[2], r[3], "path")

# ---------------------------------------------------------------------------
# Panneaux muraux (textures maison) : (texture, axe, voxel mur, face visible, u0, z0)
#   4 voxels de large (128 u) x 2 de haut (64 u)
# ---------------------------------------------------------------------------
PANELS = [
    ("sign_accueil", "y", 38, 2, 30, FLOOR + 1),        # mur d'accueil de la place
    ("sign_profil", "y", 50, 2, 16, FLOOR + 1),
    ("sign_experiences", "x", 14, 1, 44, FLOOR + 1),
    ("sign_bloc1", "y", 50, 2, 33, FLOOR + 1),          # x croît vers la gauche du joueur
    ("sign_bloc2", "y", 50, 2, 28, FLOOR + 1),
    ("sign_bloc3", "x", 26, 1, 44, FLOOR + 1),
    ("sign_certificats", "y", 11, 3, 17, FLOOR + 1),
    ("sign_contact", "x", 54, 0, 30, FLOOR + 1),
    ("sign_tux", "y", 22, 2, 47, FLOOR + 1),
    ("sign_projets", "x", 13, 0, 36, FLOOR + 1),
    ("sign_leboncoin", "x", 2, 1, 21, FLOOR + 1),
    ("sign_magic", "x", 2, 1, 27, FLOOR + 1),
    ("sign_mineport", "x", 2, 1, 33, FLOOR + 1),
    ("sign_cube2", "x", 2, 1, 39, FLOOR + 1),
    ("sign_portfolioos", "x", 2, 1, 46, FLOOR + 1),
]


def panel_texline(name, axis, face, u0, z0):
    """Ligne `texture` avec rotation/décalage pour que le panneau tombe pile sur
    son rectangle de mur et se lise à l'endroit (voir calctexgen d'octarender.cpp)."""
    W, Hh = 512, 256
    k = 4
    p0, p1 = u0 * VOX, u0 * VOX + 128
    top = z0 * VOX + 64
    flip = face in (1, 2)          # faces +X et -Y vues en miroir -> rotation 4
    xoff = (p1 * k) % W if flip else (p0 * k) % W
    yoff = (-top * k) % Hh
    return 'texture 0 "pf/%s.jpg" %d %d %d 2' % (name, 4 if flip else 0, xoff, yoff)


for name, axis, coord, face, u0, z0 in PANELS:
    addtex(name, panel_texline(name, axis, face, u0, z0))
    for du in range(4):
        for dz in range(2):
            v = idx(coord, u0 + du, z0 + dz) if axis == "x" else idx(u0 + du, coord, z0 + dz)
            if not solid[v]:
                raise SystemExit("panneau %s posé sur un voxel vide" % name)
            facetex[(v, face)] = TEXIDX[name]


def face_textures(x, y, z):
    """Tuple des 6 textures d'un voxel plein (faces cachées = texture par défaut)."""
    v = idx(x, y, z)
    out = []
    for f, (dx, dy, dz) in enumerate(DIRS):
        nx, ny, nz = x + dx, y + dy, z + dz
        t = TEXIDX["default"]
        if 0 <= nx < N and 0 <= ny < N and 0 <= nz < N and not solid[idx(nx, ny, nz)]:
            room = roomof[idx(nx, ny, nz)]
            if (v, f) in facetex:
                t = facetex[(v, f)]
            elif v in blocktex:
                t = TEXIDX[blocktex[v]]
            elif room is None:                       # face donnant sur l'extérieur
                if f == 5 and z == FLOOR - 1:
                    t = TEXIDX[groundtex.get((x, y), "grass")]
                elif f == 5:
                    t = TEXIDX["roof"]
                elif v in shellof:
                    t = TEXIDX[shellof[v].ext]
                else:
                    t = TEXIDX["cliff"]
            else:
                t = TEXIDX[room.floor if f == 5 else room.ceil if f == 4 else room.wall]
        out.append(t)
    return tuple(out)

# ---------------------------------------------------------------------------
# Octree
# ---------------------------------------------------------------------------
OCTSAV_CHILDREN, OCTSAV_EMPTY, OCTSAV_SOLID = 0, 1, 2
EMPTYTEX = (TEXIDX["default"],) * 6
_cache = {}


def leafkey(x, y, z):
    if not solid[idx(x, y, z)]:
        return ("e",)
    return ("s",) + face_textures(x, y, z)


def uniform(x, y, z, size):
    if size == 1:
        return leafkey(x, y, z)
    key = (x, y, z, size)
    if key in _cache:
        return _cache[key]
    half = size // 2
    res = None
    k0 = uniform(x, y, z, half)
    if k0 is not None:
        res = k0
        for i in range(1, 8):
            if uniform(x + (half if i & 1 else 0), y + (half if i & 2 else 0), z + (half if i & 4 else 0), half) != k0:
                res = None
                break
    _cache[key] = res
    return res


def build(x, y, z, size, out):
    half = size // 2
    for i in range(8):
        cx, cy, cz = x + (half if i & 1 else 0), y + (half if i & 2 else 0), z + (half if i & 4 else 0)
        key = uniform(cx, cy, cz, half)
        if key is None:
            out.append(struct.pack("<B", OCTSAV_CHILDREN))
            build(cx, cy, cz, half, out)
        elif key[0] == "e":
            out.append(struct.pack("<B6H", OCTSAV_EMPTY, *EMPTYTEX))
        else:
            out.append(struct.pack("<B6H", OCTSAV_SOLID, *key[1:]))

# ---------------------------------------------------------------------------
# Entités : départs, monstres, lumières, décors du jeu de base, objets, ambiances
# ---------------------------------------------------------------------------
ENTS = []  # (x, y, z, a1..a5, type)
ET_LIGHT, ET_MAPMODEL, ET_PLAYERSTART, ET_PARTICLES, ET_SOUND = 1, 2, 3, 5, 6
I_SHELLS, I_BULLETS, I_ROCKETS, I_ROUNDS, I_GRENADES, I_CARTRIDGES = 8, 9, 10, 11, 12, 13
I_HEALTH, I_BOOST, I_GREENARMOUR, I_YELLOWARMOUR, I_QUAD = 14, 15, 16, 17, 18
MONSTER_TAG = 9                # attr2 des départs réservés aux monstres (cf. fps.cpp)
MAPMODELS, MAPSOUNDS = [], []


def W(v):
    """coordonnée en voxels -> unités du monde."""
    return v * VOX


def prop(name, x, y, yaw=0, z=0):
    if name not in MAPMODELS:
        MAPMODELS.append(name)
    ENTS.append((W(x), W(y), GROUND + z, yaw, MAPMODELS.index(name), 0, 0, 0, ET_MAPMODEL))


def item(kind, x, y):
    ENTS.append((W(x), W(y), GROUND + 4, 0, 0, 0, 0, 0, kind))


def light(x, y, rgb, radius=260, z=110):
    ENTS.append((W(x), W(y), GROUND + z, radius, rgb[0], rgb[1], rgb[2], 0, ET_LIGHT))


def ambience(name, x, y, radius, inner):
    if name not in MAPSOUNDS:
        MAPSOUNDS.append(name)
    ENTS.append((W(x), W(y), GROUND + 40, MAPSOUNDS.index(name), radius, inner, 0, 0, ET_SOUND))


def monster_spawn(x, y, yaw=0):
    ENTS.append((W(x), W(y), GROUND + 4, yaw, MONSTER_TAG, 0, 0, 0, ET_PLAYERSTART))


# Départs des visiteurs : au sud de la place, tournés vers le nord (panneau d'accueil)
for x in (27, 29, 31, 33, 35, 37):
    ENTS.append((W(x), W(26), GROUND + 4, 0, 0, 0, 0, 0, ET_PLAYERSTART))

# --- Place centrale et paysage -------------------------------------------------
for (x, y) in ((26, 37), (38, 37), (26, 25), (38, 25)):
    prop("dcp/streetlamp", x, y)
prop("dcp/bench", 28, 35, 0)
prop("dcp/bench", 36, 35, 0)
for (x, y, m) in ((6, 6, "dcp/tree2"), (12, 8, "dcp/tree3"), (22, 6, "dcp/tree2"), (44, 4, "dcp/tree3"),
                  (40, 37, "dcp/tree2"), (24, 56, "dcp/tree2"), (14, 57, "dcp/tree3"), (58, 30, "dcp/palmtree"),
                  (40, 58, "dcp/palmtree"), (60, 4, "dcp/tree2"), (22, 28, "dcp/tree3")):
    prop(m, x, y)
item(I_SHELLS, 28, 30)
item(I_BULLETS, 36, 30)
item(I_HEALTH, 32, 28)
item(I_QUAD, 32, 55)
ambience("ambience/forest1", 32, 31, 420, 200)
for (x, y) in ((38, 54), (10, 4), (59, 38), (22, 22)):
    monster_spawn(x, y)

# --- Profil : bureau / bibliothèque ----------------------------------------------
prop("objects/table01", 16.5, 46.5, 90)
prop("objects/chair01", 17.5, 46.5, 270)
prop("objects/lamp01", 15.6, 49.3)
prop("dcp/plant1", 22.3, 42.7)
prop("dcp/vase", 22.3, 49.3)
light(19, 46, (255, 214, 150), 240)
item(I_CARTRIDGES, 20, 44)
item(I_HEALTH, 21, 48)
monster_spawn(21, 49, 270)
ambience("ambience/fire_light", 19, 46, 190, 80)

# --- Compétences : salle serveur -------------------------------------------------
for y in (43.5, 46, 48.5):
    prop("dcp/console", 37.4, y, 180)
prop("dcp/biotank", 28, 43)
prop("dcp/biotank", 28, 49)
light(31, 46, (120, 180, 255), 220)
light(36, 46, (80, 255, 170), 200)
item(I_ROUNDS, 33, 44)
item(I_HEALTH, 33, 49)
monster_spawn(36, 49, 270)
ambience("razgriz/energy_hum_01", 32.5, 46, 210, 90)

# --- Certificats : salle des trophées --------------------------------------------
prop("dcp/vase", 15.6, 13)
prop("dcp/vase", 15.6, 19)
prop("dcp/chest", 22.3, 13, 180)
prop("objects/lantern01", 15.1, 16, 0, 40)
light(19, 16, (255, 220, 140), 240)
item(I_YELLOWARMOUR, 20, 13)
item(I_GRENADES, 21, 18)
monster_spawn(17, 13, 90)
ambience("ambience/water", 19, 16, 190, 80)

# --- Tux World : banquise à ciel ouvert -------------------------------------------
item(I_ROCKETS, 49, 12)
item(I_HEALTH, 54, 18)
monster_spawn(52, 14, 180)
ENTS.append((W(49.5), W(15), GROUND + 200, 13, 256 + 14, 220, 0xFFF, 6000, ET_PARTICLES))   # neige
ambience("razgriz/high_wind_01", 49.5, 15, 260, 120)

# --- Contact : bureau de poste ------------------------------------------------------
prop("objects/table01", 52.5, 32, 0)
prop("objects/sign01", 47, 35.3, 0)
for (x, y) in ((53.2, 29), (53.4, 30), (52.6, 29.5)):
    prop("dcp/sack", x, y)
prop("dcp/chest", 53, 35, 180)
light(50, 32, (255, 240, 200), 240)
item(I_HEALTH, 48, 34.5)
item(I_BOOST, 48, 29.5)
monster_spawn(51, 35, 270)
ambience("ambience/wind", 50, 32, 190, 80)

# --- Galerie des projets ---------------------------------------------------------------
prop("dcp/bench", 12.3, 36, 90)
prop("dcp/bench", 12.3, 46, 90)
light(11, 26, (255, 250, 240), 260)
light(11, 45, (255, 250, 240), 260)
monster_spawn(11, 22, 90)
monster_spawn(11, 50, 270)
# Leboncoin : garage
prop("objects/minekart", 6, 23, 0)
prop("dcp/barrel", 3.6, 20.6)
prop("dcp/barrel", 3.6, 25.3)
prop("dcp/cask", 8.3, 20.7)
prop("dcp/cart", 8.2, 25.2, 0)
light(6, 23, (255, 190, 120), 170)
item(I_BULLETS, 7.5, 23)
ambience("ambience/distant_cars", 6, 23, 120, 50)
# Magic Shape Generator : planètes de feu et de glace d'ADOFAI
prop("makke/planet", 6, 29, 0, 16)
prop("makke/moon", 6, 30.6, 0, 16)
prop("dcp/firebowl", 8.3, 27.6)
prop("dcp/firebowl", 8.3, 31.4)
light(6, 29.5, (230, 80, 255), 170)
item(I_GRENADES, 4, 29.5)
ambience("ambience/creek", 6, 29.5, 120, 50)
# Mineport : voxels à ciel ouvert, champignons géants
prop("dcp/mushroom", 4.5, 36.5)
prop("dcp/mushroom", 7.5, 33.5)
prop("dcp/grass", 6, 36)
prop("dcp/grass", 5, 34)
item(I_SHELLS, 6, 35.5)
ambience("ambience/forest1", 6, 35.5, 120, 50)
# Cube 2 : arène
prop("dcp/pillar", 4, 40)
prop("dcp/pillar", 4, 43)
prop("dcp/turret", 8.2, 41.5, 180)
prop("aftas/caixa", 6.5, 39.8)
prop("aftas/caixa", 6.5, 43.2)
light(6, 41.5, (255, 110, 80), 170)
item(I_ROCKETS, 5.5, 41.5)
item(I_ROUNDS, 8, 40)
monster_spawn(5, 43.5, 0)
ambience("akari/stadiumsound", 6, 41.5, 120, 50)
# Portfolio OS : postes de travail devant le fond d'écran Ubuntu
prop("dcp/console", 3.6, 46.5, 0)
prop("dcp/console", 3.6, 49.5, 0)
prop("objects/table01", 6.8, 48, 0)
prop("objects/chair01", 7.8, 48, 180)
light(6, 48, (255, 160, 110), 170)
item(I_GREENARMOUR, 8, 46)
ambience("soundsnap/fan", 6, 48, 120, 50)

# --- Phases de parkour : jump pads et téléporteurs du jeu de base -------------
JUMPPAD, TELEPORT, TELEDEST = 23, 19, 20


def jumppad(x, y, z, zpush, ypush=0, xpush=0):
    """attr1 = poussée verticale (x12,5), attr2 = y (x10), attr3 = x (x10) — entities.cpp"""
    ENTS.append((W(x), W(y), z, zpush, ypush, xpush, 0, 0, JUMPPAD))


def teleport(x, y, z, idx, tx, ty, tyaw):
    ENTS.append((W(x), W(y), z, idx, 0, 0, 0, 0, TELEPORT))
    ENTS.append((W(tx), W(ty), GROUND + 4, tyaw, idx, 0, 0, 0, TELEDEST))


# Parkour 1 : jump pad sur le dernier pilier pour atteindre la plateforme d'arrivée
jumppad(55, 50, GROUND + 6 * VOX + 2, 30, 32, 0)
teleport(57, 57, GROUND + 9 * VOX + 4, 1, 32, 33, 180)        # retour à la place
# Parkour 2 : jump pad au pied de la galerie, vers son toit
jumppad(17, 37, GROUND + 2, 46, 0, -30)
teleport(37, 49, GROUND + (H + 1) * VOX + 4, 2, 32, 33, 180)  # retour à la place
PARKOURS = [
    ("pk1", "Parcours des piliers", (43, 42, 1, 270),
     (46, 48, 41, 43, FLOOR + 2, FLOOR + 4), (40, 60, 39, 60, FLOOR, FLOOR + 1), (52, 58, 54, 58, FLOOR + 9, FLOOR + 12)),
    ("pk2", "Parcours des toits", (11.5, 37, H + 1, 90),
     (15, 23, 42, 50, FLOOR + H + 1, FLOOR + H + 3), (14, 41, 33, 54, FLOOR, FLOOR + 1), (34, 38, 42, 50, FLOOR + H + 1, FLOOR + H + 3)),
]

# --- Phases de combat : départs des vagues (tag 10 banquise, 11 Colisée) et du boss (12)
for (x, y) in ((44, 10), (55, 9), (55, 20), (44, 20), (49, 13), (52, 18)):
    ENTS.append((W(x), W(y), GROUND + 4, 0, 10, 0, 0, 0, ET_PLAYERSTART))
for (x, y) in ((27, 5), (39, 5), (27, 12), (39, 12), (33, 6), (33, 10)):
    ENTS.append((W(x), W(y), GROUND + 4, 0, 11, 0, 0, 0, ET_PLAYERSTART))
for (x, y) in ((33, 7), (28, 6), (38, 6), (33, 12)):
    ENTS.append((W(x), W(y), GROUND + 4, 0, 12, 0, 0, 0, ET_PLAYERSTART))
# armes et munitions à proximité des arènes
for (k, x, y) in ((I_SHELLS, 33, 22.5), (I_BULLETS, 30, 22.5), (I_ROCKETS, 36, 22.5), (I_HEALTH, 33, 17),
                  (I_ROUNDS, 27.5, 18.5), (I_GRENADES, 38.5, 18.5), (I_YELLOWARMOUR, 33, 14), (I_HEALTH, 27.5, 9),
                  (I_HEALTH, 38.5, 9), (I_BULLETS, 41.5, 23), (I_SHELLS, 44, 23)):
    item(k, x, y)
light(33, 12, (255, 200, 160), 300, 140)
ambience("akari/stadiumsound", 33, 12, 300, 120)

# ---------------------------------------------------------------------------
# Points de passage des monstres (IA) : grille au sol, intérieur ET extérieur
# ---------------------------------------------------------------------------


def waypoints():
    nodes, index = [], {}
    for y in range(N):
        for x in range(N):
            if not solid[idx(x, y, FLOOR)] and not solid[idx(x, y, FLOOR + 1)] and solid[idx(x, y, FLOOR - 1)]:
                index[(x, y)] = len(nodes) + 1
                nodes.append((x, y))
    out = []
    for (x, y) in nodes:
        links = [index[(x + dx, y + dy)] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (x + dx, y + dy) in index]
        for dx, dy in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
            if len(links) >= 6:
                break
            if (x + dx, y + dy) in index and (x + dx, y) in index and (x, y + dy) in index:
                links.append(index[(x + dx, y + dy)])
        out.append(((x + 0.5) * VOX, (y + 0.5) * VOX, GROUND + 1.0, links))
    return out


def write_wpt(path):
    wps = waypoints()
    data = [b"OWPT", struct.pack("<H", len(wps))]
    for (x, y, z, links) in wps:
        data.append(struct.pack("<3fB", x, y, z, len(links)))
        data.append(struct.pack("<%dH" % len(links), *links))
    with gzip.open(path, "wb", compresslevel=9) as f:
        f.write(b"".join(data))
    return len(wps)


def write_ogz(path):
    body = [struct.pack("<4s9i", b"OCTA", MAPVERSION, 40, WORLDSIZE, len(ENTS), 0, 0, 0, 0, 0)]
    gameident = b"fps"
    body.append(struct.pack("<B", len(gameident)) + gameident + b"\0")
    body.append(struct.pack("<H", 0))   # extraentinfosize
    body.append(struct.pack("<H", 0))   # extras
    body.append(struct.pack("<H", 0))   # texmru
    for e in ENTS:
        body.append(struct.pack("<3f5hBB", e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8], 0))
    octree = []
    build(0, 0, 0, N, octree)
    body.append(b"".join(octree))
    data = b"".join(body)
    with gzip.open(path, "wb", compresslevel=9) as f:
        f.write(data)
    return len(data)


def write_cfg(path):
    L = ["// portfolio.cfg - généré par tools/gen_map.py, ne pas modifier à la main",
         "// Réglages, textures, décors, ambiances et zones de la carte de la visite.", "",
         "maptitle " + cubescript_string("Visite du portfolio de Jules ROGUE"),
         'skybox "skyboxes/remus/sky01"',
         "// soleil et lumière du ciel (éclairage extérieur calculé au chargement)",
         "sunlight 0xFFF0D8", "sunlightyaw 50", "sunlightpitch 55", "sunlightscale 1.2",
         "skylight 0x5A6478", "ambient 0x1C1C1C", "lightprecision 32",
         "fog 6000", "fogcolour 0x8FA8C8", "",
         "texturereset", "setshader stdworld"]
    for name, line in TEXTURES:
        L.append(line + "   // " + name)
    L += ["", "// --- Décors (mapmodels du jeu de base) --------------------------------", "mapmodelreset"]
    for i, name in enumerate(MAPMODELS):
        L.append('mmodel "%s"   // %d' % (name, i))
    L += ["", "// --- Ambiances sonores (sons du jeu de base) ---------------------------", "mapsoundreset"]
    for i, name in enumerate(MAPSOUNDS):
        L.append('mapsound "%s" 200   // %d' % (name, i))
    L += ["", "// --- Progression : fragments, zones, parcours, arènes --------------------", "pfreset",
          "pfend " + cubescript_string(STORY["end"])]
    for fid, title in FRAGMENTS:
        L.append("pffragment %s %s" % (fid, cubescript_string(title)))

    def zone(zid, box, title, text, spec):
        x0, x1, y0, y1, z0, z1 = box
        L.append("pfzone %s %d %d %d %d %d %d %s %s %s" % (
            zid, x0 * VOX, y0 * VOX, z0 * VOX - 8, x1 * VOX, y1 * VOX, z1 * VOX + 8,
            cubescript_string(title), cubescript_string(text), cubescript_string(spec)))

    zoneboxes = [("accueil", PLAZA), ("tux", TUXBOX), ("colisee", COLISEE)]
    for r in ROOMS:
        if r.zone:
            zoneboxes.append((r.zone, r.box))
    for sid, sr in STANDROOMS.items():
        zoneboxes.append((sid, sr.box))
    zoneboxes.append(("galerie", (9, 13, 20, 51, FLOOR, FLOOR + H)))
    for zid, box in zoneboxes:
        title, text, spec = ZONES[zid]
        zone(zid, box, title, text, spec)
    for cid, title, (sx, sy, sh, syaw), arm, fail, end in PARKOURS:
        L.append("pfcourse %s %g %g %g %g %s" % (cid, W(sx) + 16, W(sy) + 16, GROUND + sh * VOX + 16, syaw, cubescript_string(title)))
        zone(cid + "_arm", arm, title, "", "arm:" + cid)
        zone(cid + "_fail", fail, title, "", "fail:" + cid)
        zone(cid + "_end", end, title, "", "end:" + cid)
    zone("arene_banquise", TUXBOX, "Combat de la banquise", "", "arena:0")
    zone("arene_colisee", COLISEE, "Combat du Colisée", "", "arena:1")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "build/gamedata"
    base = os.path.join(out, "packages", "base")
    os.makedirs(base, exist_ok=True)
    n = write_ogz(os.path.join(base, "portfolio.ogz"))
    write_cfg(os.path.join(base, "portfolio.cfg"))
    nw = write_wpt(os.path.join(base, "portfolio.wpt"))
    print("portfolio.ogz : %d octets décompressés, %d entités, %d textures, %d décors, %d points de passage"
          % (n, len(ENTS), len(TEXTURES), len(MAPMODELS), nw))


if __name__ == "__main__":
    main()
