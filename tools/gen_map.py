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
from content import ZONES, STORY, FRAGMENTS, FRAGMENT_KIND, SIGNS, cubescript_string  # noqa: E402

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
    "plinth": "ik2k/ik_brick_6464a.jpg",
    "cornice": "ik2k/ik_wood_trimh64d.jpg",
    "curb": "ik2k/ik_brick_6464a.jpg",
    "stone": "ik2k/ik_floor_brick128a.jpg",
    "pond": "ik2k/ik_floor_brick128a.jpg",
    "pondedge": "ik2k/ik_brick_6464a.jpg",
    "rooftile": "ik2k/ik_brick_3216d.jpg",
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
    # détails d'architecture intérieurs (lambris, tapis, poutres)
    "wainscot": "ik2k/ik_woodwall128128b.jpg", "beam": "ik2k/ik_woodv256a.jpg",
    "parquet": "ik2k/ik_wood_planks128d.jpg", "rug_red": "philipk/pk01_panel_small01red_d.jpg",
    "metalfloor": "ikbase/ik_floor_met1f.jpg", "metaltrim": "ikbase/ik_wtrimh_64a.jpg",
    "panelwall": "philipk/pk01_panel03a_d.jpg", "grafloor": "philipk/pk01_gra_floor01_d.jpg",
    "trimwood": "ik2k/ik_wood_trimh64e.jpg",
    # mobilier en géométrie
    "books": "pf/books.jpg", "rack": ("pf/rack.jpg", 16), "screen": ("pf/screen.jpg", 16),
    "pigeonholes": ("pf/pigeonholes.jpg", 16), "darkmetal": "tech1soc/flr_tmtl_drk.jpg",
    "lightwood": "ik2k/ik_floor_wood128b.jpg",
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
shape = {}                         # voxel plein -> 12 arêtes Cube 2 (cube partiel : pente, biseau, demi-bloc...)
material = {}                      # voxel vide -> matériau (eau)
propblock = set()                  # cellules (x, y) occupées par un décor : pas de point de passage
MAT_WATER = 1 << 2


# Arêtes d'un cube Cube 2 (octa.h) : 3 dimensions x 4 arêtes, octet = (fin << 4) | début, en huitièmes.
def box_edges(x0=0, x1=8, y0=0, y1=8, z0=0, z1=8):
    return (((x1 << 4) | x0),) * 4 + (((y1 << 4) | y0),) * 4 + (((z1 << 4) | z0),) * 4


def hf_edges(h00, h10, h01, h11):
    """Champ de hauteur : hauteur (huitièmes) de chacun des 4 coins (x, y) du voxel."""
    return (0x80,) * 4 + (0x80,) * 4 + tuple((h << 4) for h in (h00, h10, h01, h11))


FULL = box_edges()


def isopen(v):
    """Voxel vide ou partiel : ses voisins pleins y montrent une face."""
    return not solid[v] or v in shape


def idx(x, y, z):
    return (z * N + y) * N + x


class Room:
    def __init__(self, rid, box, floor, wall, ceil="ceiling", ext="ext_brick", zone=None):
        self.rid, self.box, self.floor, self.wall, self.ceil, self.ext = rid, box, floor, wall, ceil, ext
        self.zone = zone
        self.doors = []


WINDOWS = []   # fenêtres à percer une fois les panneaux posés


# Sol plein
for z in range(FLOOR):
    for y in range(N):
        for x in range(N):
            solid[idx(x, y, z)] = 1


def setshape(x, y, z, edges, tex):
    v = idx(x, y, z)
    if edges == FULL:
        shape.pop(v, None)
    else:
        shape[v] = edges
    solid[v] = 1
    roomof[v] = None
    blocktex[v] = tex


def fill(box, tex=None, shell=None):
    x0, x1, y0, y1, z0, z1 = box
    for z in range(z0, z1):
        for y in range(y0, y1):
            for x in range(x0, x1):
                v = idx(x, y, z)
                solid[v] = 1
                shape.pop(v, None)
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
                shape.pop(v, None)


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


def pitched_roof(xa, xb, ya, yb, z):
    """Toit à deux pans au-dessus de la dalle (bornes incluses des murs), faîtage selon x."""
    k = 0
    while ya + k <= yb - k:
        lo, hi, zz = ya + k, yb - k, z + k
        for x in range(xa, xb + 1):
            for y in range(lo, hi + 1):
                if lo == hi:
                    setshape(x, y, zz, box_edges(z1=4), "rooftile")          # faîtage
                elif y == lo:
                    setshape(x, y, zz, hf_edges(0, 0, 8, 8), "rooftile")     # pan qui monte vers +y
                elif y == hi:
                    setshape(x, y, zz, hf_edges(8, 8, 0, 0), "rooftile")     # pan qui monte vers -y
                else:
                    setshape(x, y, zz, FULL, "rooftile")
        k += 1


def building(rid, x0, x1, y0, y1, floor, wall, ceil="ceiling", ext="ext_brick", doors=(), zone=None, roof="pitched",
             windows=True):
    """Bâtiment : intérieur [x0,x1)x[y0,y1), murs d'un voxel autour, toit, portes.
    doors : (côté 'n','s','e','w', début, fin) le long du mur."""
    r = Room(rid, (x0, x1, y0, y1, FLOOR, FLOOR + H), floor, wall, ceil, ext, zone)
    ROOMS.append(r)
    ROOMBYID[rid] = r
    fill((x0 - 1, x1 + 1, y0 - 1, y1 + 1, FLOOR, FLOOR + H + 1), shell=r)
    carve(r.box, r)
    doorcells = set()
    for side, a, b in doors:
        if side == "s":
            carve((a, b, y0 - 1, y0, FLOOR, FLOOR + 2), r)
            out = [(a - 1, y0 - 2), (b, y0 - 2)]
            doorcells |= {(x, y0 - 1) for x in range(a - 1, b + 1)}
        elif side == "n":
            carve((a, b, y1, y1 + 1, FLOOR, FLOOR + 2), r)
            out = [(a - 1, y1 + 1), (b, y1 + 1)]
            doorcells |= {(x, y1) for x in range(a - 1, b + 1)}
        elif side == "w":
            carve((x0 - 1, x0, a, b, FLOOR, FLOOR + 2), r)
            out = [(x0 - 2, a - 1), (x0 - 2, b)]
            doorcells |= {(x0 - 1, y) for y in range(a - 1, b + 1)}
        else:
            carve((x1, x1 + 1, a, b, FLOOR, FLOOR + 2), r)
            out = [(x1 + 1, a - 1), (x1 + 1, b)]
            doorcells |= {(x1, y) for y in range(a - 1, b + 1)}
        r.doors.append((side, a, b))
        for (cx, cy) in out:                              # colonnes de part et d'autre de la porte
            if not solid[idx(cx, cy, FLOOR)]:
                for z in range(FLOOR, FLOOR + 2):
                    setshape(cx, cy, z, box_edges(2, 6, 2, 6), "stone")
                propblock.add((cx, cy))
    xa, xb, ya, yb = x0 - 1, x1, y0 - 1, y1
    if roof == "pitched":
        if (xb - xa) >= (yb - ya):
            pitched_roof(xa, xb, ya, yb, FLOOR + H + 1)
    # corniche en saillie sous le toit
    zc = FLOOR + H - 1
    for x in range(xa - 1, xb + 2):
        for y in range(ya - 1, yb + 2):
            if xa <= x <= xb and ya <= y <= yb:
                continue
            if solid[idx(x, y, zc)]:
                continue
            bx0, bx1, by0, by1 = 0, 8, 0, 8
            if x < xa: bx0 = 5
            if x > xb: bx1 = 3
            if y < ya: by0 = 5
            if y > yb: by1 = 3
            setshape(x, y, zc, box_edges(bx0, bx1, by0, by1, 4, 8), "cornice")
    # fenêtres (ouvertures) tous les 3 voxels, hors coins, portes et panneaux
    if windows:
        zw = FLOOR + 2
        cand = [(x, ya) for x in range(xa + 2, xb - 1, 3)] + [(x, yb) for x in range(xa + 2, xb - 1, 3)] + \
               [(xa, y) for y in range(ya + 2, yb - 1, 3)] + [(xb, y) for y in range(ya + 2, yb - 1, 3)]
        for (x, y) in cand:
            if (x, y) in doorcells:
                continue
            nb = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
            outside = [c for c in nb if not (x0 <= c[0] < x1 and y0 <= c[1] < y1)]
            if any(solid[idx(cx, cy, zw)] for (cx, cy) in outside if 0 <= cx < N and 0 <= cy < N):
                continue
            WINDOWS.append((x, y, zw, r))
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
         doors=[("e", 30, 32)], zone=None, roof="flat", windows=False)

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

# --- Parkours recalibrés sur la physique réelle (saut mesuré : ~20 u de haut,
#     ~110 u de long) : marches de 8 u, écarts d'un voxel (32 u), plateformes de 96 u de
#     profondeur pour absorber la longueur du saut, parcours compacts.
def platform(x0, x1, y0, y1, height, tex):
    """Plateforme pleine dont le dessus est à `height` unités au-dessus du sol."""
    full, rem = divmod(height, VOX)
    if full:
        fill((x0, x1, y0, y1, FLOOR, FLOOR + full), tex)
    if rem:
        for y in range(y0, y1):
            for x in range(x0, x1):
                setshape(x, y, FLOOR + full, box_edges(z1=rem // 4), tex)


def beam(x0, x1, y, height, tex):
    """Poutre étroite (16 u de large) selon x, dessus à `height` unités."""
    full, rem = divmod(height, VOX)
    for x in range(x0, x1):
        for z in range(FLOOR, FLOOR + full):
            setshape(x, y, z, box_edges(0, 8, 2, 6, 0, 8), tex)
        if rem:
            setshape(x, y, FLOOR + full, box_edges(0, 8, 2, 6, 0, rem // 4), tex)


# Parcours 1 « Les piliers » (nord-est) : 6 marches de 8 u puis la plateforme d'arrivée
PK1 = [(42, 45, 41, 44, 8), (46, 49, 41, 44, 16), (50, 53, 41, 44, 24), (50, 53, 45, 48, 32),
       (46, 49, 45, 48, 40), (46, 49, 49, 52, 48)]
PK1END = (50, 56, 49, 53, 48)
for (x0, x1, y0, y1, h) in PK1:
    platform(x0, x1, y0, y1, h, "ext_conc")
platform(*PK1END, "stone")
# Parcours 2 « Les poutres » (sud-ouest) : jump pad -> plateforme haute, poutres, arrivée
PK2P0 = (4, 7, 9, 13, 80)
PK2END = (13, 16, 9, 12, 68)
platform(*PK2P0, "ext_conc")
beam(7, 10, 10, 80, "cornice")          # poutre 1
beam(11, 13, 10, 80, "cornice")         # poutre 2 (un voxel de vide entre les deux)
platform(*PK2END, "stone")

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


# --- Détails d'architecture intérieurs : lambris, tapis, poutres au plafond -----------
WAINSCOT = {"profil": "wainscot", "certificats": "wainscot", "contact": "trimwood", "competences": "panelwall",
            "galerie": "metaltrim", "leboncoin": "plinth", "portfolioos": "metaltrim", "cube2": "metaltrim"}
floorpatch = {}


def rug(x0, x1, y0, y1, tex):
    for y in range(y0, y1):
        for x in range(x0, x1):
            floorpatch[(x, y)] = tex


rug(17, 21, 45, 49, "parquet")           # Profil : parquet sous le bureau
rug(17, 21, 14, 18, "rug_red")           # Certificats : tapis rouge des trophées
rug(31, 34, 43, 50, "grafloor")          # Compétences : allée centrale entre les baies
rug(49, 53, 29, 35, "parquet")           # Contact : derrière le comptoir
rug(10, 12, 20, 51, "grafloor")          # Galerie : allée centrale


def beam(room, along, at, z=None):
    """Poutre de plafond (dessous à 108 u, hors de portée) traversant la salle."""
    x0, x1, y0, y1 = room.box[:4]
    zz = FLOOR + H - 1 if z is None else z
    cells = [(x, at) for x in range(x0, x1)] if along == "x" else [(at, y) for y in range(y0, y1)]
    for (x, y) in cells:
        v = idx(x, y, zz)
        if solid[v] or roomof[v] is not room:
            continue
        setshape(x, y, zz, box_edges(0, 8, 2, 6, 5, 8) if along == "x" else box_edges(2, 6, 0, 8, 5, 8), "beam")
        roomof[v] = room                     # reste « intérieur » pour les faces voisines


_rooms = {r.rid: r for r in ROOMS}
_rooms.update(STANDROOMS)
for at in (43, 48):
    beam(_rooms["profil"], "x", at)
for at in (44, 47):
    beam(_rooms["competences"], "x", at)
for at in (14, 17):
    beam(_rooms["certificats"], "x", at)
for at in (49, 51):
    beam(_rooms["contact"], "y", at)
for at in (23, 29, 35, 41, 47):
    beam(_rooms["galerie"], "x", at)

for (wx, wy, wz, wr) in WINDOWS:
    v = idx(wx, wy, wz)
    if any(k[0] == v for k in facetex):
        continue
    carve((wx, wx + 1, wy, wy + 1, wz, wz + 1), wr)

# --- Étang (eau du jeu de base) au nord, bordé de pierres -----------------------
POND = (26, 32, 53, 59)
# Eau du jeu de base : étang en cuvette et ruisseau peu profond vers l'est. Fonds en
# pente douce (16 u au plus par voxel) : on ressort partout en marchant, sans sauter.
STREAM = (32, 41, 55, 57)            # x0, x1, y0, y1 (2 voxels de large, 16 u de fond au milieu)
WATERC = {}                          # coins (X, Y) -> hauteur du fond (huitièmes de voxel)


def pond_corner(i, j):
    w, h = POND[1] - POND[0], POND[3] - POND[2]
    d = min(i, w - i, j, h - j)
    return max(0, 8 - 4 * d)


for Y in range(POND[2], POND[3] + 1):
    for X in range(POND[0], POND[1] + 1):
        WATERC[(X, Y)] = pond_corner(X - POND[0], Y - POND[2])
for Y in range(STREAM[2], STREAM[3] + 1):
    for X in range(STREAM[0], STREAM[1] + 1):
        mid = Y == (STREAM[2] + STREAM[3]) // 2 and X < STREAM[1]
        WATERC[(X, Y)] = min(WATERC.get((X, Y), 8), 4 if mid else 8)
WATERCELLS = [(x, y) for y in range(POND[2], POND[3]) for x in range(POND[0], POND[1])] + \
             [(x, y) for y in range(STREAM[2], STREAM[3]) for x in range(STREAM[0], STREAM[1])]
for (x, y) in WATERCELLS:
    v = idx(x, y, FLOOR - 1)
    hc = (WATERC[(x, y)], WATERC[(x + 1, y)], WATERC[(x, y + 1)], WATERC[(x + 1, y + 1)])
    if max(hc) == 0:
        solid[v] = 0
    else:
        setshape(x, y, FLOOR - 1, hf_edges(*hc), "stone")
    material[v] = MAT_WATER
    blocktex[idx(x, y, FLOOR - 2)] = "stone"
    groundtex[(x, y)] = "pond"
for y in range(POND[2] - 1, POND[3] + 1):
    for x in range(POND[0] - 1, POND[1] + 1):
        if not (POND[0] <= x < POND[1] and POND[2] <= y < POND[3]) and (x, y) not in groundtex:
            groundtex[(x, y)] = "pondedge"         # margelle au ras du sol

# --- Bordures de chemins (4 u, franchissables sans sauter) ---------------------
for (x, y), t in list(groundtex.items()):
    if t not in ("path", "plaza"):
        continue
    for (nx, ny) in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if (nx, ny) in groundtex or not (2 <= nx < N - 2 and 2 <= ny < N - 2):
            continue
        if solid[idx(nx, ny, FLOOR)] or not solid[idx(nx, ny, FLOOR - 1)]:
            continue
        setshape(nx, ny, FLOOR, box_edges(z1=1), "curb")
        groundtex[(nx, ny)] = "curb"

# --- Relief : collines douces (pentes <= 26°, max 32 u) hors lieux aménagés -------
import math
flat = [[False] * N for _ in range(N)]
for y in range(N):
    for x in range(N):
        if (x, y) in groundtex or x < 2 or y < 2 or x >= N - 2 or y >= N - 2:
            flat[y][x] = True
        elif any(solid[idx(x, y, z)] for z in range(FLOOR, FLOOR + 3)) or not solid[idx(x, y, FLOOR - 1)] \
                or roomof[idx(x, y, FLOOR)] is not None:      # intérieur des bâtiments : sol plat
            flat[y][x] = True
# marge de 2 voxels autour des lieux aménagés (sauf la bordure de falaises)
keep = [[flat[y][x] and 2 <= x < N - 2 and 2 <= y < N - 2 for x in range(N)] for y in range(N)]
for y in range(N):
    for x in range(N):
        if keep[y][x]:
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    if 0 <= x + dx < N and 0 <= y + dy < N:
                        flat[y + dy][x + dx] = True
HC = [[0] * (N + 1) for _ in range(N + 1)]          # hauteurs aux coins (huitièmes de voxel)
for y in range(N + 1):
    for x in range(N + 1):
        cells = [(x - 1, y - 1), (x, y - 1), (x - 1, y), (x, y)]
        if any(0 <= cx < N and 0 <= cy < N and flat[cy][cx] for (cx, cy) in cells):
            continue
        n = 4 + 3 * math.sin(x * 0.45) * math.cos(y * 0.37) + 2 * math.sin((x + y) * 0.23)
        HC[y][x] = max(0, min(8, int(round(n))))
for _ in range(10):                                  # pentes douces : écart <= 2 entre coins voisins
    for y in range(N + 1):
        for x in range(N + 1):
            for (nx, ny) in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx <= N and 0 <= ny <= N:
                    HC[y][x] = min(HC[y][x], HC[ny][nx] + 2)
for y in range(N):
    for x in range(N):
        h = (HC[y][x], HC[y][x + 1], HC[y + 1][x], HC[y + 1][x + 1])
        if flat[y][x] or max(h) == 0:
            continue
        setshape(x, y, FLOOR, hf_edges(*h), "grass")


def terrainh(x, y):
    """Hauteur du relief (unités) au point (x, y) en voxels."""
    ix, iy = int(x), int(y)
    if not (0 <= ix < N and 0 <= iy < N):
        return 0
    fx, fy = x - ix, y - iy
    h = (HC[iy][ix] * (1 - fx) * (1 - fy) + HC[iy][ix + 1] * fx * (1 - fy) +
         HC[iy + 1][ix] * (1 - fx) * fy + HC[iy + 1][ix + 1] * fx * fy)
    return h * 4


def face_textures(x, y, z):
    """Tuple des 6 textures d'un voxel plein (faces cachées = texture par défaut)."""
    v = idx(x, y, z)
    out = []
    for f, (dx, dy, dz) in enumerate(DIRS):
        nx, ny, nz = x + dx, y + dy, z + dz
        t = TEXIDX["default"]
        if 0 <= nx < N and 0 <= ny < N and 0 <= nz < N and isopen(idx(nx, ny, nz)):
            room = roomof[idx(nx, ny, nz)]
            if (v, f) in facetex:
                t = facetex[(v, f)]
            elif v in blocktex:
                t = TEXIDX[blocktex[v]]
            elif room is None:                       # face donnant sur l'extérieur
                if f == 5 and z == FLOOR - 1:
                    gt = groundtex.get((x, y), "grass")
                    t = TEXIDX[gt if gt in TEXIDX else "grass"]
                elif f == 5:
                    t = TEXIDX["roof"]
                elif v in shellof:
                    t = TEXIDX["plinth" if z == FLOOR else shellof[v].ext]
                else:
                    t = TEXIDX["cliff"]
            else:
                t = TEXIDX[room.floor if f == 5 else room.ceil if f == 4 else room.wall]
                if f == 5 and (x, y) in floorpatch:
                    t = TEXIDX[floorpatch[(x, y)]]          # tapis, allée, estrade
                elif f < 4 and z == FLOOR and room.rid in WAINSCOT:
                    t = TEXIDX[WAINSCOT[room.rid]]           # lambris / plinthe intérieure
        out.append(t)
    return tuple(out)

# ---------------------------------------------------------------------------
# Octree
# ---------------------------------------------------------------------------
OCTSAV_CHILDREN, OCTSAV_EMPTY, OCTSAV_SOLID, OCTSAV_NORMAL = 0, 1, 2, 3
EMPTYTEX = (TEXIDX["default"],) * 6
_cache = {}


def leafkey(x, y, z):
    v = idx(x, y, z)
    if v in FURN:
        return ("f", v)
    if not solid[v]:
        return ("e", material.get(v, 0))
    if v in shape:
        return ("n",) + face_textures(x, y, z) + shape[v] + (material.get(v, 0),)
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
        elif key[0] == "f":
            furn_node(cx * VOX, cy * VOX, cz * VOX, VOX, FURN[key[1]], out)
        elif key[0] == "e":
            if key[1]:
                out.append(struct.pack("<B6HH", OCTSAV_EMPTY | 0x40, *(EMPTYTEX + (key[1],))))
            else:
                out.append(struct.pack("<B6H", OCTSAV_EMPTY, *EMPTYTEX))
        elif key[0] == "n":
            if key[19]:     # cube partiel immergé (berges de l'étang)
                out.append(struct.pack("<B12B6HH", OCTSAV_NORMAL | 0x40, *(key[7:19] + key[1:7] + (key[19],))))
            else:
                out.append(struct.pack("<B12B6H", OCTSAV_NORMAL, *(key[7:19] + key[1:7])))
        else:
            out.append(struct.pack("<B6H", OCTSAV_SOLID, *key[1:]))

# ---------------------------------------------------------------------------
# Mobilier en géométrie : boîtes à l'échelle du joueur (1 unité près), découpées en
# sous-cubes de l'octree (un voxel de 32 unités est subdivisé jusqu'à 1 unité).
# ---------------------------------------------------------------------------
FURNBOXES = []     # (x0, y0, z0, x1, y1, z1, textures des 6 faces) en unités du monde
FURN = {}          # voxel -> boîtes qui le touchent


def meuble(x0, x1, y0, y1, z0, z1, tex, **faces):
    """Boîte de mobilier : x, y en voxels (flottants), z en unités au-dessus du sol intérieur.
    tex = texture de toutes les faces ; faces : xn, xp, yn, yp, bas, haut (DIRS)."""
    keys = ("xn", "xp", "yn", "yp", "bas", "haut")
    t6 = tuple(TEXIDX[faces.get(k, tex)] for k in keys)
    r = lambda v: int(v + 0.5) if v >= 0 else -int(-v + 0.5)        # arrondi à l'unité (pas d'arrondi pair)
    b = (r(x0 * VOX), r(y0 * VOX), r(GROUND + z0), r(x1 * VOX), r(y1 * VOX), r(GROUND + z1), t6)
    assert b[3] > b[0] and b[4] > b[1] and b[5] > b[2], b
    FURNBOXES.append(b)
    for vz in range(b[2] // VOX, (b[5] - 1) // VOX + 1):
        for vy in range(b[1] // VOX, (b[4] - 1) // VOX + 1):
            for vx in range(b[0] // VOX, (b[3] - 1) // VOX + 1):
                v = idx(vx, vy, vz)
                assert not solid[v], ("meuble dans un mur", vx, vy, vz)
                FURN.setdefault(v, []).append(b)
                if b[2] < GROUND + 18:
                    propblock.add((vx, vy))
    return b


def furn_node(ox, oy, oz, s, boxes, out):
    inter = []
    for b in boxes:
        c = (max(b[0], ox), max(b[1], oy), max(b[2], oz), min(b[3], ox + s), min(b[4], oy + s), min(b[5], oz + s))
        if c[3] > c[0] and c[4] > c[1] and c[5] > c[2]:
            inter.append((c, b[6]))
    if not inter:
        out.append(struct.pack("<B6H", OCTSAV_EMPTY, *EMPTYTEX))
        return
    for c, t in inter:
        if c == (ox, oy, oz, ox + s, oy + s, oz + s):
            out.append(struct.pack("<B6H", OCTSAV_SOLID, *t))
            return
    e = s / 8.0
    def ok(c):
        return all(abs((c[i] - (ox, oy, oz)[i % 3]) / e - round((c[i] - (ox, oy, oz)[i % 3]) / e)) < 1e-6 for i in range(6))
    if (len(inter) == 1 and ok(inter[0][0])) or s <= 1:
        c, t = inter[0]
        r = [int(round((c[i] - (ox, oy, oz)[i % 3]) / e)) for i in range(6)]
        if r[3] <= r[0] or r[4] <= r[1] or r[5] <= r[2]:
            out.append(struct.pack("<B6H", OCTSAV_EMPTY, *EMPTYTEX))
            return
        out.append(struct.pack("<B12B6H", OCTSAV_NORMAL, *(box_edges(r[0], r[3], r[1], r[4], r[2], r[5]) + t)))
        return
    out.append(struct.pack("<B", OCTSAV_CHILDREN))
    h = s // 2
    for i in range(8):
        furn_node(ox + (h if i & 1 else 0), oy + (h if i & 2 else 0), oz + (h if i & 4 else 0), h, inter_boxes(inter), out)


def inter_boxes(inter):
    return [c + (t,) for c, t in inter]


def furn_top(x, y, below):
    """Plus haut dessus de mobilier sous la hauteur `below` (unités absolues) au point (x, y) en unités."""
    best = None
    for b in FURNBOXES:
        if b[0] <= x <= b[3] and b[1] <= y <= b[4] and b[5] <= below + 1.5:
            best = b[5] if best is None else max(best, b[5])
    return best


def furn_bottom(x, y, above):
    """Plus bas dessous de mobilier au-dessus de `above` au point (x, y)."""
    best = None
    for b in FURNBOXES:
        if b[0] <= x <= b[3] and b[1] <= y <= b[4] and b[2] >= above - 1.5:
            best = b[2] if best is None else min(best, b[2])
    return best


# ---------------------------------------------------------------------------
# Boîtes englobantes des mapmodels (lues dans les fichiers du jeu de base) :
# md2 / md3 / obj, mdlscale (pourcentage, divisé par 4 par le moteur), mdltrans.
# ---------------------------------------------------------------------------
_bounds = {}


def model_bounds(name):
    if name in _bounds:
        return _bounds[name]
    import re
    res = None
    for root in SEARCH:
        d = os.path.join(root, "packages", "models", name)
        if not os.path.isdir(d):
            continue
        cfg, cfgname = "", None
        for c in ("md2.cfg", "md3.cfg", "obj.cfg"):
            if os.path.exists(os.path.join(d, c)):
                cfg, cfgname = open(os.path.join(d, c), encoding="latin-1").read(), c
                break
        if re.search(r"mdlpitch|mdlyaw", cfg):
            raise SystemExit("décor %s : mdlpitch / mdlyaw non pris en charge par la vérification" % name)
        sc = 1.0
        m = re.search(r"mdlscale\s+([-\d.]+)", cfg)
        if m:
            sc = float(m.group(1)) / 100
        tr = (0.0, 0.0, 0.0)
        m = re.search(r"mdltrans\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)", cfg)
        if m:
            tr = tuple(map(float, m.groups()))
        kind = (cfgname or "md2.cfg")[:3]
        m = re.search(r"%sload\s+\"?([^\s\"]+)" % kind, cfg)
        f = os.path.join(d, m.group(1) if m else {"md2": "tris.md2", "md3": "tris.md3", "obj": "tris.obj"}[kind])
        if not os.path.exists(f):
            continue
        b = open(f, "rb").read()
        if kind == "md2":
            nv, ofs = struct.unpack("<i", b[24:28])[0], struct.unpack("<i", b[56:60])[0]
            fs = struct.unpack("<3f", b[ofs:ofs + 12])
            ft = struct.unpack("<3f", b[ofs + 12:ofs + 24])
            vs = [(b[ofs + 40 + i * 4] * fs[0] + ft[0], -(b[ofs + 41 + i * 4] * fs[1] + ft[1]),
                   b[ofs + 42 + i * 4] * fs[2] + ft[2]) for i in range(nv)]
        elif kind == "md3":
            ofs = struct.unpack("<i", b[92:96])[0]
            mn, mx = struct.unpack("<3f", b[ofs:ofs + 12]), struct.unpack("<3f", b[ofs + 12:ofs + 24])
            vs = [mn, mx]
        else:
            vs = []
            for l in b.decode("latin-1").splitlines():
                if l.startswith("v "):
                    px, py, pz = map(float, l.split()[1:4])
                    vs.append((pz, -px, py))
        lo = tuple((min(v[i] for v in vs) + tr[i]) * sc / 4 for i in range(3))
        hi = tuple((max(v[i] for v in vs) + tr[i]) * sc / 4 for i in range(3))
        res = (lo, hi)
        break
    _bounds[name] = res
    return res


FIREMODELS = {"dcp/firebowl", "dcp/candle"}
ASSEMBLAGES = {"objects/well_roof": "objects/well_base"}


def verifier_decors():
    """Chaque décor doit être posé (sol, relief ou dessus d'un meuble), suspendu à un plafond
    ou à un meuble, sans entrer dans un mur ; chaque flamme doit sortir d'un brasero ou d'une
    bougie ; aucun objet ni départ dans un meuble."""
    import math
    errs = []
    fires = []
    for e in ENTS:
        if e[8] != ET_MAPMODEL:
            continue
        name = MAPMODELS[e[4]]
        bb = model_bounds(name)
        if bb is None:
            errs.append("%s : modèle introuvable" % name)
            continue
        (lx, ly, lz), (hx, hy, hz) = bb
        x, y, z = e[0], e[1], e[2]
        bottom, top = z + lz, z + hz
        vx, vy = x / VOX, y / VOX
        room = roomof[idx(int(vx), int(vy), FLOOR)]
        ground = GROUND + (0 if room else terrainh(vx, vy))
        ft = furn_top(x, y, bottom)
        sup = max(ground, ft) if ft is not None else ground
        posed = -4 <= bottom - sup <= 1.5          # légèrement enfoncé : toléré ; flottant : refusé
        if name in ASSEMBLAGES:                       # pièce posée sur un autre décor au même endroit
            posed = any(f[8] == ET_MAPMODEL and MAPMODELS[f[4]] == ASSEMBLAGES[name] and f[:3] == e[:3] for f in ENTS)
        # suspendu : plafond (voxel plein au-dessus) ou dessous d'un meuble
        fb = furn_bottom(x, y, top)
        cz = int(math.floor((top + 0.5) / VOX))
        ceil = (0 <= cz < N and solid[idx(int(vx), int(vy), cz)] and abs(top - cz * VOX) <= 1.5)
        pendu = hz <= 0.5 and (ceil or (fb is not None and abs(top - fb) <= 1.5))
        if not (posed or pendu):
            errs.append("%s en (%.2f, %.2f) : bas %.1f / haut %.1f, support %.1f -> ni posé ni suspendu"
                        % (name, vx, vy, bottom - GROUND, top - GROUND, sup - GROUND))
        # emprise : les coins (tournés selon yaw) ne doivent pas entrer dans un voxel plein
        a = math.radians(e[3])
        zz = int((max(bottom, ground) + 2) // VOX)
        for (px, py) in ((lx / 2, ly / 2), (hx / 2, ly / 2), (lx / 2, hy / 2), (hx / 2, hy / 2)):
            wx = x + px * math.cos(a) - py * math.sin(a)
            wy = y + px * math.sin(a) + py * math.cos(a)
            v = idx(int(wx // VOX), int(wy // VOX), zz)
            if solid[v] and v not in shape:
                errs.append("%s en (%.2f, %.2f) : entre dans un mur" % (name, vx, vy))
                break
        if name in FIREMODELS:
            fires.append((x + (lx + hx) / 2, y + (ly + hy) / 2, top))
    for e in ENTS:
        if e[8] == ET_PARTICLES and e[3] == 0:
            if not any(math.hypot(e[0] - fx, e[1] - fy) <= 6 and -3 <= e[2] - fz <= 8 for (fx, fy, fz) in fires):
                errs.append("flamme en (%.2f, %.2f, %d) sans brasero ni bougie" % (e[0] / VOX, e[1] / VOX, e[2] - GROUND))
        if e[8] == ET_PLAYERSTART or I_SHELLS <= e[8] <= I_QUAD:
            for b in FURNBOXES:
                if b[0] - 8 < e[0] < b[3] + 8 and b[1] - 8 < e[1] < b[4] + 8 and b[2] < e[2] + 4 and b[5] > e[2] - 20:
                    errs.append("objet / départ en (%.2f, %.2f) contre un meuble" % (e[0] / VOX, e[1] / VOX))
                    break
    if errs:
        raise SystemExit("Décors mal posés :\n  " + "\n  ".join(errs))
    return len([e for e in ENTS if e[8] == ET_MAPMODEL])


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


def prop(name, x, y, yaw=0, z=0, block=0):
    """Décor du jeu de base ; posé sur le relief ; bloque les points de passage autour."""
    if name not in MAPMODELS:
        MAPMODELS.append(name)
    ENTS.append((W(x), W(y), GROUND + z + terrainh(x, y), yaw, MAPMODELS.index(name), 0, 0, 0, ET_MAPMODEL))
    for dy in range(-block, block + 1):
        for dx in range(-block, block + 1):
            propblock.add((int(x) + dx, int(y) + dy))


def item(kind, x, y, z=4):
    ENTS.append((W(x), W(y), GROUND + z + terrainh(x, y), 0, 0, 0, 0, 0, kind))


def light(x, y, rgb, radius=260, z=110):
    ENTS.append((W(x), W(y), GROUND + z, radius, rgb[0], rgb[1], rgb[2], 0, ET_LIGHT))


def ambience(name, x, y, radius, inner):
    if name not in MAPSOUNDS:
        MAPSOUNDS.append(name)
    ENTS.append((W(x), W(y), GROUND + 40, MAPSOUNDS.index(name), radius, inner, 0, 0, ET_SOUND))


def monster_spawn(x, y, yaw=0):
    # posé sur le relief (sinon le départ est enfoui dans une colline)
    ENTS.append((W(x), W(y), GROUND + 4 + terrainh(x, y), yaw, MONSTER_TAG, 0, 0, 0, ET_PLAYERSTART))


# Départs des visiteurs : au sud de la place, tournés vers le nord (panneau d'accueil)
for x in (27, 29, 31, 33, 35, 37):
    ENTS.append((W(x), W(26), GROUND + 4, 0, 0, 0, 0, 0, ET_PLAYERSTART))

# --- Place centrale et paysage -------------------------------------------------
for (x, y) in ((25.5, 37.5), (38.5, 37.5), (25.5, 24.5), (38.5, 24.5)):
    prop("dcp/streetlamp", x, y)
    light(x, y, (255, 210, 150), 160, 60)
for (x, y) in ((21.5, 31.5), (40.5, 32.5), (19.5, 26.5), (33.5, 22.5), (42.5, 26.5), (19.5, 37.5)):
    prop("dcp/groundlamp", x, y)
prop("objects/bench01", 28, 35.5, 0, 0, 0)
prop("objects/bench01", 36, 35.5, 0, 0, 0)
prop("objects/well_base", 32.5, 31.5, 0, 0, 1)        # puits au centre de la place
prop("objects/well_roof", 32.5, 31.5, 0, 0)

TREES = ((22, 6, "dcp/tree2"), (44, 4, "dcp/tree3"), (40, 37, "dcp/tree2"), (22, 56, "dcp/tree2"),
         (14, 57, "dcp/tree3"), (58, 30, "dcp/palmtree"), (40, 58, "dcp/palmtree"), (60, 4, "dcp/tree2"),
         (22, 28, "dcp/tree3"), (58, 20, "dcp/tree3"), (35, 57, "dcp/tree2"), (6, 57, "dcp/tree2"),
         (60, 47, "dcp/tree3"), (24, 9, "dcp/tree2"), (10, 17, "dcp/tree3"), (45, 38, "dcp/palmtree"))
for (x, y, m) in TREES:
    prop(m, x + 0.5, y + 0.5, 0, 0, 1)
for (x, y) in ((24.5, 40.5), (39.5, 40.5), (14.4, 22.5), (24.5, 22.5), (44.5, 27.5), (44.5, 36.5), (33.5, 52.5)):
    prop("dcp/plant1", x, y, 0, 0, 0)                 # buissons au pied des bâtiments
for (x, y) in ((28.5, 52.5), (31.5, 52.5), (25.5, 56.5)):
    prop("dcp/leafs", x, y)                           # végétation autour de l'étang
for (x, y) in ((26.4, 53.4), (31.6, 58.6), (26.3, 58.5), (34.5, 54.6), (37.5, 57.4), (40.6, 54.5)):
    prop("dcp/reed", x, y)                            # roseaux au bord de l'eau
item(I_SHELLS, 28, 29)
item(I_BULLETS, 37, 29)
item(I_HEALTH, 32.5, 27)
item(I_QUAD, 29, 60)
ambience("ambience/forest1", 32, 31, 420, 200)
ambience("ambience/creek", 29, 56, 200, 80)
for (x, y) in ((38, 54), (20, 4), (59, 38), (22, 22), (8, 58), (59, 9)):
    monster_spawn(x, y)
# éclairage coloré à l'entrée de chaque bâtiment (lanternes)
DOORLIGHTS = {"profil": (255, 200, 120), "competences": (110, 170, 255), "certificats": (255, 210, 110),
              "contact": (255, 240, 200), "galerie": (255, 140, 90)}
for r in ROOMS:
    col = DOORLIGHTS.get(r.rid)
    for (side, a, b) in r.doors:
        x0, x1, y0, y1 = r.box[:4]
        mx = (a + b) / 2.0
        lx, ly = {"s": (mx, y0 - 1.6), "n": (mx, y1 + 1.6), "w": (x0 - 1.6, mx), "e": (x1 + 1.6, mx)}[side]
        light(lx, ly, col, 150, 80)

# --- Profil : bureau / bibliothèque ----------------------------------------------
light(19, 46, (255, 214, 150), 240)
item(I_CARTRIDGES, 20, 44)
item(I_HEALTH, 21, 48)
monster_spawn(21, 49, 270)
ambience("ambience/fire_light", 19, 46, 190, 80)

# --- Compétences : salle serveur -------------------------------------------------
light(32.5, 46, (120, 170, 230), 240)
item(I_ROUNDS, 33, 44)
item(I_HEALTH, 33, 49)
monster_spawn(36, 49, 270)
ambience("razgriz/energy_hum_01", 32.5, 46, 210, 90)

# --- Certificats : salle des trophées --------------------------------------------
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
light(50, 32, (255, 240, 200), 240)
item(I_HEALTH, 48, 34.5)
item(I_BOOST, 48, 29.5)
monster_spawn(51, 35, 270)
ambience("ambience/wind", 50, 32, 190, 80)

# --- Galerie des projets ---------------------------------------------------------------
light(11, 26, (255, 250, 240), 260)
light(11, 45, (255, 250, 240), 260)
monster_spawn(11, 22, 90)
monster_spawn(11, 50, 270)
# Leboncoin : garage
light(6, 23, (255, 190, 120), 170)
item(I_BULLETS, 7.5, 23)
ambience("ambience/distant_cars", 6, 23, 120, 50)
# Magic Shape Generator : salle néon, braseros et lampes
light(6, 29.5, (230, 80, 255), 170)
item(I_GRENADES, 4, 29.5)
ambience("ambience/creek", 6, 29.5, 120, 50)
# Mineport : voxels à ciel ouvert, champignons géants
item(I_SHELLS, 6, 35.5)
ambience("ambience/forest1", 6, 35.5, 120, 50)
# Cube 2 : arène
light(6, 41.5, (255, 110, 80), 170)
item(I_ROCKETS, 5.5, 41.5)
item(I_ROUNDS, 8, 40)
monster_spawn(5, 43.5, 0)
ambience("akari/stadiumsound", 6, 41.5, 120, 50)
# Portfolio OS : postes de travail devant le fond d'écran Ubuntu
light(6, 48, (255, 160, 110), 170)
item(I_GREENARMOUR, 8, 46)
ambience("soundsnap/fan", 6, 48, 120, 50)

# --- Mobilier et décors des salles (voir CREDITS.md) ---------------------------------
# Mobilier en géométrie à l'échelle du joueur (15 unités de haut, yeux à 14) : bureaux,
# bibliothèques, baies, guichet, podium, stands. Portes, allées, objets à ramasser et
# départs restent libres ; verifier_decors() refuse tout décor flottant ou dans un mur.


def outside_ok(x, y):
    """Décor extérieur : jamais sur un chemin, la place, une bordure ou l'eau."""
    return groundtex.get((int(x), int(y))) not in ("path", "plaza", "curb", "pond", "pondedge")


def particles(x, y, z, ptype, a2=0, a3=0, a4=0):
    """Particules d'entité du moteur (0 feu, 1 vapeur, 10 eau qui goutte...)."""
    ENTS.append((W(x), W(y), GROUND + z, ptype, a2, a3, a4, 0, ET_PARTICLES))


U = 1.0 / VOX          # une unité du monde, en voxels


def pendant(x, y, zbas, col, rayon=110):
    """Suspension : tige depuis le plafond, abat-jour, lumière dessous."""
    meuble(x - U, x + U, y - U, y + U, zbas + 3, H * VOX, "darkmetal")
    meuble(x - 5 * U, x + 5 * U, y - 5 * U, y + 5 * U, zbas, zbas + 3, "darkmetal")
    light(x, y, col, rayon, zbas - 6)


def ecran(x0, x1, y0, y1, z0, z1, face):
    """Moniteur : coque sombre, dalle allumée sur la face `face`, pied jusqu'à z0 - 1.5."""
    meuble(x0, x1, y0, y1, z0, z1, "darkmetal", **{face: "screen"})
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    meuble(cx - U, cx + U, cy - U, cy + U, z0 - 1.5, z0, "darkmetal")


def braise(x, y, nom="dcp/firebowl"):
    """Brasero posé au sol, flamme au sommet du modèle."""
    prop(nom, x, y)
    (lx, ly, lz), (hx, hy, hz) = model_bounds(nom)
    particles(x + (lx + hx) / 2 * U, y + (ly + hy) / 2 * U, hz + 1, 0, 30, 40)


# --- Profil (CV) : grand bureau face à l'entrée, bibliothèques, rayonnages ---------
# Hauteurs un peu au-dessus du réel : l'architecture de la carte est à double échelle.
meuble(17.4, 20.6, 47.0, 47.9, 11, 12, "beam")                                 # plateau
meuble(17.45, 18.2, 47.05, 47.85, 0, 11, "lightwood")                           # caissons
meuble(19.8, 20.55, 47.05, 47.85, 0, 11, "lightwood")
meuble(18.2, 19.8, 47.75, 47.85, 3, 11, "lightwood")                            # voile de fond
for x0 in (17.95, 18.65, 19.35):
    ecran(x0, x0 + 0.65, 47.55, 47.65, 14, 22, "yn")                           # 3 écrans vers l'entrée
meuble(18.6, 19.4, 47.1, 47.35, 12, 12.5, "darkmetal")                          # clavier
prop("dcp/vase", 17.7, 47.3, 0, 12)
prop("objects/chair01", 19, 46.5, 180)
meuble(15.0, 15.9, 49.55, 50.0, 0, 56, "lightwood", yn="books")                # bibliothèque du fond
meuble(15.9, 18.1, 49.55, 50.0, 0, 30, "lightwood", yn="books")                # (sous le panneau Profil)
meuble(18.1, 20.6, 49.55, 50.0, 0, 56, "lightwood", yn="books")
meuble(15.0, 15.45, 42.6, 49.55, 0, 30, "lightwood", xp="books")               # bibliothèque ouest
meuble(16.4, 16.8, 43.2, 46.2, 0, 40, "lightwood", xn="books", xp="books")     # rayonnages au milieu
meuble(21.3, 21.7, 43.0, 46.6, 0, 40, "lightwood", xn="books", xp="books")
meuble(15.75, 16.65, 47.6, 48.5, 6, 7, "beam")                                  # table basse du coin lecture
meuble(16.15, 16.25, 48.0, 48.1, 0, 6, "beam")
prop("dcp/candle", 16.2, 48.25, 0, 7)
prop("objects/chair01", 16.2, 47.2, 0)
for y in (45.4, 46.5):
    prop("mitaman/locker1", 22.75, y, 90)                                       # armoires d'archives
prop("dcp/plant1", 22.4, 42.6)
prop("dcp/bin", 20.9, 42.5)
prop("dcp/smplant", 15.8, 42.85)
pendant(19, 46.6, 36, (255, 190, 120), 150)
pendant(16.2, 47.9, 34, (255, 200, 140), 80)
light(19, 46.9, (90, 140, 255), 80, 18)                                         # lueur des écrans
light(17.5, 48.8, (255, 170, 90), 110, 30)                                      # bibliothèque

# --- Compétences : salle serveur dense, allée froide centrale, allées chaudes ------
for (x0, y0, y1) in ((28.4, 44.2, 47.8), (30.0, 43.0, 49.0), (34.8, 43.0, 49.0), (36.6, 43.0, 47.5)):
    meuble(x0, x0 + 0.8, y0, y1, 0, 36, "darkmetal", xn="rack", xp="rack")      # rangées de baies
for y in (44.9, 47.1):
    meuble(30.0, 35.6, y, y + 0.2, 36, 37, "metaltrim")                         # chemins de câbles
meuble(28.4, 37.4, 46.0, 46.2, 36, 37, "metaltrim")
prop("dcp/biotank", 28, 43)
prop("dcp/biotank", 28, 49)
prop("psionic/barrel2", 29.2, 42.6)
prop("dcp/vent", 33, 49.6, 180)
prop("dcp/console", 37.3, 48.6, 180)
light(32.8, 44.5, (60, 140, 255), 120, 14)
light(32.8, 47.5, (60, 255, 140), 120, 14)
light(29.6, 46.0, (255, 90, 60), 80, 20)
light(36.2, 45.0, (255, 90, 60), 80, 20)

# --- Certificats : podium central, vitrines, braseros, kakémonos -------------------
meuble(17.4, 18.5, 15.0, 16.2, 0, 8, "beam", haut="rug_red")                    # 2e marche
meuble(18.5, 19.5, 15.0, 16.2, 0, 13, "beam", haut="rug_red")                   # 1re marche
meuble(19.5, 20.6, 15.0, 16.2, 0, 5, "beam", haut="rug_red")                    # 3e marche
prop("dcp/waterbowl", 19.0, 15.6, 0, 13)
prop("dcp/vase", 17.95, 15.6, 0, 8)
prop("dcp/vase", 20.05, 15.6, 0, 5)
for (x0, y0, m) in ((15.4, 13.8, "dcp/waterbowl"), (15.4, 15.6, "dcp/chest"), (15.4, 17.4, "dcp/vase"),
                    (22.0, 14.0, "dcp/vase"), (22.0, 15.8, "dcp/waterbowl")):
    meuble(x0, x0 + 0.6, y0, y0 + 0.6, 0, 14, "beam", haut="rug_red")          # vitrines
    prop(m, x0 + 0.3, y0 + 0.3, 90 if x0 < 19 else 270, 14)
    light(x0 + 0.3, y0 + 0.3, (255, 220, 150), 60, 34)
for x0 in (17.0, 20.85):
    meuble(x0, x0 + 0.15, 15.2, 16.0, 0, 52, "darkmetal", yp="rug_red")         # kakémonos
braise(17.6, 17.2)
braise(20.4, 17.2)
light(17.6, 17.2, (255, 130, 50), 90, 26)
light(20.4, 17.2, (255, 130, 50), 90, 26)
light(19, 15.6, (255, 225, 150), 120, 44)

# --- Contact : guichet de poste, casiers de tri, rayonnage à colis -----------------
meuble(50.3, 51.0, 29.0, 34.2, 0, 14, "lightwood", xn="trimwood")              # guichet
meuble(50.2, 51.1, 29.0, 34.2, 14, 15, "beam")
for y in (29.05, 31.55, 34.05):
    meuble(50.6, 50.7, y, y + 0.1, 15, 38, "darkmetal")                         # montants de l'hygiaphone
meuble(50.6, 50.7, 29.05, 34.15, 38, 40, "darkmetal")
meuble(50.55, 50.75, 30.6, 32.4, 40, 46, "trimwood", xn="post_floor")           # enseigne du guichet
ecran(50.45, 50.55, 29.9, 30.7, 17, 23, "xn")                                   # terminal du guichet
prop("dcp/cbbox", 50.65, 33.4, 0, 15)
prop("objects/chair01", 51.9, 31.5, 270)
meuble(53.55, 54.0, 28.6, 33.5, 0, 30, "lightwood", xn="pigeonholes")          # casiers de tri
for x0 in (52.2, 53.8):
    meuble(x0, x0 + 0.1, 35.5, 36.0, 0, 36, "lightwood")                       # rayonnage à colis
for z0 in (0, 13, 26, 35):
    meuble(52.2, 53.9, 35.5, 36.0, z0, z0 + 1, "lightwood")
prop("dcp/cbbox", 52.7, 35.75, 0, 1)
prop("xeno/box1", 53.3, 35.75, 0, 1)
prop("dcp/cbbox", 53.0, 35.75, 0, 14)
prop("dcp/sack", 52.5, 29.2)
prop("dcp/sack", 53.0, 29.7, 40)
prop("objects/bench01", 47.6, 28.3, 0)
pendant(50.2, 30.0, 46, (255, 220, 160), 120)
pendant(50.2, 33.0, 46, (255, 220, 160), 120)
light(53.0, 31.0, (255, 180, 100), 90, 22)

# --- Galerie des projets : colonnes, bandeaux de stands, totem d'écrans ------------
for y in (26.5, 32.5, 38.5, 44.5):
    meuble(9.0, 9.3, y - 0.2, y + 0.2, 0, H * VOX, "beam")                    # colonnes entre les stands
for (y0, y1) in ((20, 26), (27, 32), (33, 38), (39, 44), (45, 51)):
    meuble(8.85, 9.0, y0, y1, 44, 52, "trimwood")                               # bandeau au-dessus de chaque stand
meuble(10.6, 11.4, 34.6, 35.4, 0, 4, "beam")                                    # totem central
meuble(10.85, 11.15, 34.85, 35.15, 4, 14, "darkmetal")
meuble(10.7, 11.3, 34.7, 35.3, 14, 28, "darkmetal", xn="screen", xp="screen", yn="screen", yp="screen")
for y in (26.0, 38.0, 44.0):
    pendant(11, y, 60, (255, 240, 220), 140)
for y in (24.5, 36.5, 47.5):
    prop("objects/bench01", 12.55, y, 90)
for y in (21.0, 50.0):
    prop("dcp/smplant", 12.5, y)
light(11, 35, (120, 170, 255), 80, 20)
# Leboncoin (garage) : voiture rouge sur le pont, établi et panneau à outils, fûts
meuble(4.9, 5.7, 21.9, 24.1, 3, 12, "rug_red")                                  # carrosserie
meuble(4.95, 5.65, 21.9, 22.3, 12, 13, "rug_red")                               # capot
meuble(5.0, 5.6, 22.5, 23.6, 12, 19, "darkmetal", xn="screen", xp="screen", yn="screen", yp="screen")  # habitacle vitré
for wx in (4.8, 5.7):
    for wy in (22.2, 23.5):
        meuble(wx, wx + 0.1, wy, wy + 0.35, 0, 7, "darkmetal")                  # roues
meuble(3.0, 3.7, 23.0, 25.0, 0, 13, "lightwood", haut="beam")                   # établi
meuble(3.0, 3.1, 23.0, 25.0, 18, 40, "metaltrim")                               # panneau à outils
prop("dcp/barrel", 3.6, 20.6)
prop("dcp/cask", 8.3, 20.7)
prop("psionic/barrel2", 4.3, 21.2)
prop("dcp/palette", 7.6, 21.5)
prop("xeno/box1", 3.35, 24.0, 0, 13)
light(5.3, 23, (255, 170, 90), 120, 34)
# Magic Shape Generator : borne interactive et sculpture de formes néon
meuble(6.0, 6.8, 28.8, 30.2, 0, 14, "darkmetal")                                # borne
ecran(6.1, 6.2, 29.0, 30.0, 16, 28, "xp")
meuble(4.4, 5.2, 30.6, 31.4, 0, 20, "neon_wall")                                 # sculpture : formes empilées
meuble(4.55, 5.05, 30.75, 31.25, 20, 36, "rug_red")
meuble(4.65, 4.95, 30.85, 31.15, 36, 48, "screen")
prop("dcp/groundlamp", 4, 28)
light(6.6, 29.5, (230, 80, 255), 100, 26)
light(4.8, 31.0, (80, 220, 255), 90, 40)
# Mineport : arbre et établi façon voxels
meuble(4.35, 4.65, 36.35, 36.65, 0, 36, "beam")                                 # tronc
meuble(3.8, 5.2, 35.8, 37.2, 36, 60, "mine_floor")                              # feuillage
meuble(5.5, 6.1, 33.1, 33.7, 0, 20, "lightwood", haut="mine_stone")             # établi façon voxels
prop("dcp/mushroom", 7.5, 36.6)
prop("dcp/grass", 6, 36)
prop("dcp/grass", 5, 34)
prop("dcp/reed", 7.4, 37.4)
# Cube 2 : borne d'arcade, piliers, caisses
meuble(3.05, 3.8, 41.1, 42.0, 0, 14, "darkmetal")                               # borne d'arcade
meuble(3.05, 4.0, 41.1, 42.0, 14, 17, "darkmetal")
meuble(3.05, 3.8, 41.1, 42.0, 17, 30, "darkmetal", xp="screen")
meuble(3.05, 3.9, 41.1, 42.0, 30, 36, "neon_wall")
prop("dcp/pillar", 4, 40)
prop("dcp/pillar", 4, 43)
prop("dcp/turret", 8.2, 41.5, 180)
prop("aftas/caixa", 6.5, 39.8, 0, 10.4)
prop("aftas/caixa", 6.5, 43.2, 0, 10.4)
light(4.2, 41.55, (255, 80, 60), 90, 24)
# Portfolio OS : bureau à trois écrans devant le fond d'écran Ubuntu
meuble(5.3, 6.3, 46.9, 49.1, 11, 12, "lightwood")
meuble(5.35, 6.25, 46.95, 47.2, 0, 11, "lightwood")
meuble(5.35, 6.25, 48.8, 49.05, 0, 11, "lightwood")
for y0 in (47.1, 47.75, 48.4):
    ecran(5.7, 5.8, y0, y0 + 0.6, 14, 22, "xp")
prop("objects/chair01", 4.9, 48.0, 270)
prop("dcp/console", 3.6, 46.5, 0)
prop("dcp/console", 3.6, 49.5, 0)
prop("dcp/bin", 8.4, 49.5)
light(6.5, 48, (255, 120, 200), 100, 20)

# --- Extérieurs : rochers, bancs près de l'étang, arbres ----------------------------
for (x, y, m, yaw) in ((23.5, 53.0, "razgriz/rocks/set1/4", 0), (34.5, 61.0, "razgriz/rocks/set1/5", 40),
                       (2.8, 12.5, "razgriz/rocks/set1/6", 80), (60.5, 13.5, "razgriz/rocks/set1/7", 120),
                       (44.0, 61.0, "razgriz/rocks/set2/2", 10), (17.0, 61.0, "razgriz/rocks/set2/4", 200),
                       (60.5, 56.0, "razgriz/rocks/set2/5", 90), (14.0, 5.0, "razgriz/rocks/set1/8", 30)):
    if outside_ok(x, y):
        prop(m, x, y, yaw, 0, 1)
for (x, y, yaw) in ((27.5, 60.6, 0), (30.5, 51.6, 180)):
    if outside_ok(x, y):
        prop("objects/bench01", x, y, yaw, 0, 0)
for (x, y, m) in ((50.5, 58.5, "dcp/tree2"), (8.5, 52.5, "dcp/tree3"), (56.5, 41.5, "dcp/tree2"), (19.5, 8.5, "dcp/tree3")):
    if outside_ok(x, y):
        prop(m, x, y, 0, 0, 1)

# --- Phases de parkour : jump pads et téléporteurs du jeu de base -------------
JUMPPAD, TELEPORT, TELEDEST = 23, 19, 20


def jumppad(x, y, z, zpush, ypush=0, xpush=0):
    """attr1 = poussée verticale (x12,5), attr2 = y (x10), attr3 = x (x10) — entities.cpp"""
    ENTS.append((W(x), W(y), z, zpush, ypush, xpush, 0, 0, JUMPPAD))


def teleport(x, y, z, idx, tx, ty, tyaw):
    ENTS.append((W(x), W(y), z, idx, 0, 0, 0, 0, TELEPORT))
    ENTS.append((W(tx), W(ty), GROUND + 4, tyaw, idx, 0, 0, 0, TELEDEST))


# Parcours 2 : jump pad au sol qui envoie sur la plateforme haute
jumppad(5.5, 5.5, GROUND + 2, 30, 28, 0)
teleport(54.5, 51, GROUND + 48 + 4, 1, 32, 33, 180)          # parcours 1 -> place
teleport(15, 11, GROUND + 68 + 4, 2, 32, 33, 180)            # parcours 2 -> place
PARKOURS = [
    ("pk1", "Parcours des piliers", (43.5, 42.5, 8, 270),
     (46, 49, 41, 44, FLOOR, FLOOR + 3), (41, 57, 40, 54, FLOOR, FLOOR + 0.3125), (50, 56, 49, 53, FLOOR + 1, FLOOR + 3)),
    ("pk2", "Parcours des poutres", (5.5, 10.5, 80, 90),
     (7, 10, 10, 11, FLOOR + 3, FLOOR + 5), (3, 17, 6, 16, FLOOR, FLOOR + 1), (13, 16, 9, 12, FLOOR + 3, FLOOR + 5)),
]

# --- Phases de combat : départs des vagues (tag 10 banquise, 11 Colisée) et du boss (12)
for (x, y) in ((44, 10), (55, 9), (55, 20), (44, 20), (49, 13), (52, 18)):
    ENTS.append((W(x), W(y), GROUND + 4, 0, 10, 0, 0, 0, ET_PLAYERSTART))
for (x, y) in ((27, 5), (39, 5), (27, 12), (39, 12), (33, 6), (33, 10)):
    ENTS.append((W(x), W(y), GROUND + 4, 0, 11, 0, 0, 0, ET_PLAYERSTART))
for (x, y) in ((33, 7), (28, 6), (38, 6), (33, 12)):
    ENTS.append((W(x), W(y), GROUND + 4, 0, 12, 0, 0, 0, ET_PLAYERSTART))
# armes et munitions à proximité des arènes
for (k, x, y) in ((I_SHELLS, 33, 22.5), (I_BULLETS, 30, 22.5), (I_HEALTH, 33, 17),
                  (I_ROUNDS, 27.5, 18.5), (I_GRENADES, 38.5, 18.5), (I_YELLOWARMOUR, 33, 14), (I_HEALTH, 27.5, 9),
                  (I_HEALTH, 38.5, 9), (I_BULLETS, 41.5, 23), (I_SHELLS, 44, 23)):
    item(k, x, y)
light(33, 12, (255, 200, 160), 300, 140)
# Armes à ramasser (objets du jeu de base, réapparition normale gérée par le serveur) :
# communes sur les chemins, les plus fortes en récompense des parcours (avant les arènes).
for (k, x, y) in ((I_GRENADES, 16, 30.5),          # chemin ouest, vers la galerie
                  (I_CARTRIDGES, 18.5, 38.5),      # chemin nord-ouest, vers le Profil
                  (I_SHELLS, 42.5, 31),            # chemin est, vers le Contact
                  (I_HEALTH, 41.5, 41.5),          # pied du parcours des piliers
                  (I_GREENARMOUR, 34.5, 59.5)):    # recoin derrière l'étang
    item(k, x, y)
item(I_ROCKETS, 51.5, 51, 4 + PK1END[4])           # arrivée du parcours des piliers
item(I_ROCKETS, 13.6, 10.5, 4 + PK2END[4])         # arrivée du parcours des poutres (près du Colisée)
ambience("akari/stadiumsound", 33, 12, 300, 120)

# ---------------------------------------------------------------------------
# Points de passage des monstres (IA) : grille au sol, intérieur ET extérieur
# ---------------------------------------------------------------------------


def waypoints():
    def walkable(x, y):
        if (x, y) in propblock:
            return None
        v0, v1 = idx(x, y, FLOOR), idx(x, y, FLOOR + 1)
        if not solid[idx(x, y, FLOOR - 1)] or (solid[v1] and v1 not in shape):
            return None
        if solid[v0]:
            if v0 not in shape:
                return None
            e = shape[v0]
            if e[:8] != (0x80,) * 8:                  # colonne, poutre... : pas un sol
                return None
            h = max(x >> 4 for x in e[8:])
            if h > 2 and (x, y) not in groundtex and max(HC[y][x], HC[y][x + 1], HC[y + 1][x], HC[y + 1][x + 1]) == 0:
                return None                         # plateformes de parkour
            return h * 4
        return 0
    nodes, index, zs = [], {}, {}
    for y in range(N):
        for x in range(N):
            h = walkable(x, y)
            if h is None:
                continue
            index[(x, y)] = len(nodes) + 1
            nodes.append((x, y))
            zs[(x, y)] = h
    out = []
    for (x, y) in nodes:
        links = [index[(x + dx, y + dy)] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (x + dx, y + dy) in index]
        for dx, dy in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
            if len(links) >= 6:
                break
            if (x + dx, y + dy) in index and (x + dx, y) in index and (x, y + dy) in index:
                links.append(index[(x + dx, y + dy)])
        out.append(((x + 0.5) * VOX, (y + 0.5) * VOX, GROUND + 1.0 + zs[(x, y)], links))
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
         "// eau (textures du jeu de base, comme data/default_map_settings.cfg d'origine)",
         "materialreset",
         'texture water "golgotha/water2.jpg"', 'texture 1 "textures/waterfall.jpg"',
         'texture 1 "textures/watern.jpg"', 'texture 1 "textures/waterdudv.jpg"',
         'texture 1 "textures/waterfalln.jpg"', 'texture 1 "textures/waterfalldudv.jpg"',
         "watercolour 0x284858", "",
         "texturereset", "setshader stdworld"]
    for name, line in TEXTURES:
        L.append(line + "   // " + name)
        if name == "grass":
            L.append('autograss "textures/grass.png"   // herbe animée du moteur sur les pelouses')
    L += ["", "// --- Décors (mapmodels du jeu de base) --------------------------------", "mapmodelreset"]
    for i, name in enumerate(MAPMODELS):
        L.append('mmodel "%s"   // %d' % (name, i))
    L += ["", "// --- Ambiances sonores (sons du jeu de base) ---------------------------", "mapsoundreset"]
    for i, name in enumerate(MAPSOUNDS):
        L.append('mapsound "%s" 200   // %d' % (name, i))
    L += ["", "// --- Progression : fragments, zones, parcours, arènes --------------------", "pfreset",
          "pfend " + cubescript_string(STORY["end"])]
    L.append("// histoire (chapitres, objectifs, armes) : voir tools/content.py")
    for key, text in STORY.items():
        L.append("pfstory_%s = %s" % (key, cubescript_string(text)))
    for fid, title in FRAGMENTS:
        L.append("pffragment %s %s %s" % (fid, cubescript_string(title), FRAGMENT_KIND.get(fid, "")))
    L.append("// inscriptions flottantes (particules de texte du moteur)")
    for (x, y, h, color, text) in SIGNS:
        L.append("pfsign %g %g %g %d %s" % (W(x), W(y), GROUND + terrainh(x, y) + h, color, cubescript_string(text)))

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
        L.append("pfcourse %s %g %g %g %g %s" % (cid, W(sx), W(sy), GROUND + sh + 16, syaw, cubescript_string(title)))
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
    nd = verifier_decors()
    print("décors vérifiés : %d posés ou suspendus, %d boîtes de mobilier" % (nd, len(FURNBOXES)))
    n = write_ogz(os.path.join(base, "portfolio.ogz"))
    write_cfg(os.path.join(base, "portfolio.cfg"))
    nw = write_wpt(os.path.join(base, "portfolio.wpt"))
    print("portfolio.ogz : %d octets décompressés, %d entités, %d textures, %d décors, %d points de passage"
          % (n, len(ENTS), len(TEXTURES), len(MAPMODELS), nw))


if __name__ == "__main__":
    main()
