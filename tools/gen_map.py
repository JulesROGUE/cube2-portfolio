#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère la carte « portfolio » de Cube 2 (packages/base/portfolio.ogz + .cfg).

Le monde est décrit comme une grille de voxels de 32 unités (monde de 2048³) :
on part d'un bloc plein et on « creuse » le Hall, les salles et les portes.
Le script construit ensuite l'octree au format OCTA v33 de Sauerbraten
(cubes entièrement pleins ou vides uniquement, sans lightmaps), avec une texture
par face qui dépend de la salle voisine (sol, murs, plafond) et des panneaux
muraux (textures générées par gen_assets.py) alignés sur les murs.

Usage : gen_map.py <dossier_sortie>   (écrit <sortie>/packages/base/portfolio.*)
"""
import gzip
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from content import ZONES, STORY, cubescript_string  # noqa: E402

VOX = 32            # taille d'un voxel en unités du monde
N = 64              # voxels par axe -> monde de 2048
WORLDSIZE = VOX * N
MAPVERSION = 33

# Faces Sauerbraten : 0=-X 1=+X 2=-Y 3=+Y 4=-Z 5=+Z
DIRS = [(-1, 0, 0), (1, 0, 0), (0, -1, 0), (0, 1, 0), (0, 0, -1), (0, 0, 1)]

# ---------------------------------------------------------------------------
# Textures (l'ordre = indices des slots dans portfolio.cfg ; 0 = ciel, 1 = défaut)
# ---------------------------------------------------------------------------
TEXTURES = []          # (nom, ligne cubescript)
TEXIDX = {}


def addtex(name, line):
    TEXIDX[name] = len(TEXTURES)
    TEXTURES.append((name, line))


addtex("sky", 'texture 0 "pf/sky.jpg"')
addtex("default", 'texture 0 "pf/wall_grey.jpg" 0 0 0 2')
for t in ["floor_hall", "floor_wood", "floor_tile", "floor_ice", "floor_dark",
          "wall_grey", "wall_blue", "wall_green", "wall_orange", "wall_purple",
          "wall_ice", "wall_gold", "wall_teal", "wall_red", "ceiling"]:
    addtex(t, 'texture 0 "pf/%s.jpg" 0 0 0 2' % t)

# ---------------------------------------------------------------------------
# Plan : salles (boîtes [x0,x1) x [y0,y1) x [z0,z1) en voxels)
# ---------------------------------------------------------------------------
FLOOR = 16  # sol à z = 16 voxels (512 unités)


class Room:
    def __init__(self, rid, box, floor, wall, ceil="ceiling", zone=None):
        self.rid, self.box, self.floor, self.wall, self.ceil = rid, box, floor, wall, ceil
        self.zone = zone


ROOMS = []
# Hall d'accueil
ROOMS.append(Room("accueil", (22, 42, 26, 34, FLOOR, FLOOR + 5), "floor_hall", "wall_grey", zone="accueil"))
# Nord
ROOMS.append(Room("profil", (22, 30, 35, 43, FLOOR, FLOOR + 4), "floor_wood", "wall_blue", zone="profil"))
ROOMS.append(Room("competences", (31, 42, 35, 43, FLOOR, FLOOR + 4), "floor_tile", "wall_green", zone="competences"))
# Sud
ROOMS.append(Room("certificats", (22, 30, 17, 25, FLOOR, FLOOR + 4), "floor_wood", "wall_gold", zone="certificats"))
ROOMS.append(Room("tux", (31, 42, 17, 25, FLOOR, FLOOR + 4), "floor_ice", "wall_ice", zone="tux"))
# Est
ROOMS.append(Room("contact", (43, 51, 26, 34, FLOOR, FLOOR + 4), "floor_dark", "wall_teal", zone="contact"))
# Ouest : galerie des projets (allée + 5 stands séparés par des cloisons)
ROOMS.append(Room("galerie", (8, 21, 14, 43, FLOOR, FLOOR + 4), "floor_tile", "wall_orange", zone=None))

# Portes : boîtes creusées dans les murs (largeur 2 voxels, hauteur 2 voxels)
DOORS = [
    (25, 27, 34, 35, FLOOR, FLOOR + 2, "accueil"),   # hall -> profil
    (35, 37, 34, 35, FLOOR, FLOOR + 2, "accueil"),   # hall -> compétences
    (25, 27, 25, 26, FLOOR, FLOOR + 2, "accueil"),   # hall -> certificats
    (35, 37, 25, 26, FLOOR, FLOOR + 2, "accueil"),   # hall -> tux
    (42, 43, 29, 31, FLOOR, FLOOR + 2, "accueil"),   # hall -> contact
    (21, 22, 29, 31, FLOOR, FLOOR + 2, "accueil"),   # hall -> galerie
]

# Cloisons des stands (pleines) dans la galerie : de x=8 à x=15, épaisseur 1
DIVIDERS = [(8, 15, y, y + 1, FLOOR, FLOOR + 4) for y in (19, 25, 31, 37)]

# Stands (zones) de la galerie, du sud au nord
STANDS = [("leboncoin", 14, 19, "wall_orange"), ("magic", 20, 25, "wall_purple"),
          ("mineport", 26, 31, "wall_green"), ("cube2", 32, 37, "wall_gold"),
          ("portfolioos", 38, 43, "wall_teal")]

# Socles décoratifs (blocs pleins posés au sol) : (x0,x1,y0,y1,z0,z1,texture)
PILLARS = [
    (31, 33, 29, 31, FLOOR, FLOOR + 1, "wall_gold"),   # socle central du hall
    (36, 37, 21, 22, FLOOR, FLOOR + 1, "wall_ice"),    # banquise Tux
    (34, 35, 19, 20, FLOOR, FLOOR + 1, "wall_ice"),
    (39, 40, 22, 23, FLOOR, FLOOR + 1, "wall_ice"),
]

# Panneaux : (texture, axe 'x' ou 'y', coordonnée du voxel mur, face, u0 en voxels, z0 en voxels)
#   face = indice de face Sauerbraten visible (0..3), u0 = début du panneau le long du mur.
#   Un panneau fait 4 voxels de large (128 u) et 2 de haut (64 u).
PANELS = [
    ("sign_accueil", "y", 34, 2, 28, FLOOR + 2),        # mur nord du hall, vu depuis le sud
    ("sign_profil", "y", 43, 2, 24, FLOOR + 1),         # profil, mur nord
    ("sign_experiences", "x", 21, 1, 37, FLOOR + 1),    # profil, mur ouest (face +X)
    ("sign_bloc1", "y", 43, 2, 36, FLOOR + 1),         # (x croît vers la gauche du joueur)
    ("sign_bloc2", "y", 43, 2, 32, FLOOR + 1),
    ("sign_bloc3", "x", 30, 1, 37, FLOOR + 1),          # compétences, mur de droite (face +X)
    ("sign_certificats", "y", 16, 3, 24, FLOOR + 1),    # certificats, mur sud (face +Y)
    ("sign_tux", "y", 16, 3, 36, FLOOR + 1),            # tux, mur sud
    ("sign_contact", "x", 51, 0, 28, FLOOR + 1),        # contact, mur est
    ("sign_projets", "x", 21, 0, 32, FLOOR + 1),        # galerie, mur est (vu depuis l'ouest)
    ("sign_leboncoin", "x", 7, 1, 15, FLOOR + 1),       # stands : mur ouest de la galerie
    ("sign_magic", "x", 7, 1, 21, FLOOR + 1),
    ("sign_mineport", "x", 7, 1, 27, FLOOR + 1),
    ("sign_cube2", "x", 7, 1, 33, FLOOR + 1),
    ("sign_portfolioos", "x", 7, 1, 39, FLOOR + 1),
]


def panel_texline(name, axis, face, u0, z0):
    """Ligne `texture` avec rotation/décalage pour que le panneau tombe pile sur
    son rectangle de mur et se lise à l'endroit (voir calctexgen d'octarender.cpp)."""
    W, H = 512, 256            # taille de l'image du panneau
    k = 4                      # texels par unité -> scale = 8/k = 2
    p0, p1 = u0 * VOX, u0 * VOX + 128
    top = z0 * VOX + 64
    # Faces 1 (+X) et 2 (-Y) : texture vue en miroir -> rotation 4 (flip X)
    flip = face in (1, 2)
    xoff = (p1 * k) % W if flip else (p0 * k) % W
    yoff = (-top * k) % H
    return 'texture 0 "pf/%s.jpg" %d %d %d 2' % (name, 4 if flip else 0, xoff, yoff)


# ---------------------------------------------------------------------------
# Voxelisation
# ---------------------------------------------------------------------------
solid = bytearray([1]) * (N * N * N)
roomof = [None] * (N * N * N)     # salle à laquelle appartient un voxel vide
blocktex = {}                      # voxel plein -> texture imposée (socles, cloisons)
facetex = {}                       # (voxel plein, face) -> texture imposée (panneaux)


def idx(x, y, z):
    return (z * N + y) * N + x


def carve(box, room):
    x0, x1, y0, y1, z0, z1 = box
    for z in range(z0, z1):
        for y in range(y0, y1):
            for x in range(x0, x1):
                solid[idx(x, y, z)] = 0
                roomof[idx(x, y, z)] = room


def fill(box, tex):
    x0, x1, y0, y1, z0, z1 = box
    for z in range(z0, z1):
        for y in range(y0, y1):
            for x in range(x0, x1):
                solid[idx(x, y, z)] = 1
                roomof[idx(x, y, z)] = None
                blocktex[idx(x, y, z)] = tex


ROOMBYID = {r.rid: r for r in ROOMS}
for r in ROOMS:
    carve(r.box, r)
for d in DOORS:
    carve(d[:6], ROOMBYID[d[6]])
for d in DIVIDERS:
    fill(d, "wall_orange")
for p in PILLARS:
    fill(p[:6], p[6])

# Les stands ont leur propre teinte de mur : salles virtuelles pour le texturage
STANDROOMS = {}
for sid, y0, y1, wall in STANDS:
    sr = Room(sid, (8, 15, y0, y1, FLOOR, FLOOR + 4), "floor_tile", wall, zone=sid)
    STANDROOMS[sid] = sr
    for z in range(FLOOR, FLOOR + 4):
        for y in range(y0, y1):
            for x in range(8, 15):
                if not solid[idx(x, y, z)]:
                    roomof[idx(x, y, z)] = sr

for name, axis, coord, face, u0, z0 in PANELS:
    addtex(name, panel_texline(name, axis, face, u0, z0))
    for du in range(4):
        for dz in range(2):
            if axis == "x":
                v = idx(coord, u0 + du, z0 + dz)
            else:
                v = idx(u0 + du, coord, z0 + dz)
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
            elif room is not None:
                if f == 5:
                    t = TEXIDX[room.floor]      # face du dessus = sol de la salle
                elif f == 4:
                    t = TEXIDX[room.ceil]       # face du dessous = plafond
                else:
                    t = TEXIDX[room.wall]
        out.append(t)
    return tuple(out)


# ---------------------------------------------------------------------------
# Octree
# ---------------------------------------------------------------------------
OCTSAV_CHILDREN, OCTSAV_EMPTY, OCTSAV_SOLID = 0, 1, 2
EMPTYTEX = (TEXIDX["default"],) * 6


def leafkey(x, y, z):
    if not solid[idx(x, y, z)]:
        return ("e",)
    return ("s",) + face_textures(x, y, z)


def build(x, y, z, size, out):
    """size en voxels ; écrit les 8 enfants d'un noeud (comme savec)."""
    half = size // 2
    for i in range(8):
        cx = x + (half if i & 1 else 0)
        cy = y + (half if i & 2 else 0)
        cz = z + (half if i & 4 else 0)
        key = uniform(cx, cy, cz, half)
        if key is None:
            out.append(struct.pack("<B", OCTSAV_CHILDREN))
            build(cx, cy, cz, half, out)
        elif key[0] == "e":
            out.append(struct.pack("<B6H", OCTSAV_EMPTY, *EMPTYTEX))
        else:
            out.append(struct.pack("<B6H", OCTSAV_SOLID, *key[1:]))


def uniform(x, y, z, size):
    """Clé commune si le bloc est homogène, sinon None."""
    first = leafkey(x, y, z)
    if size == 1:
        return first
    for dz in range(size):
        for dy in range(size):
            for dx in range(size):
                if leafkey(x + dx, y + dy, z + dz) != first:
                    return None
    return first


# Accélération : un bloc ne peut être homogène que si tous ses voxels sont pleins
# ou tous vides ; on pré-calcule des sommes pour éviter de tout parcourir.
_cache = {}


def _uniform_fast(x, y, z, size):
    if size == 1:
        return leafkey(x, y, z)
    key = (x, y, z, size)
    if key in _cache:
        return _cache[key]
    half = size // 2
    res = None
    k0 = _uniform_fast(x, y, z, half)
    if k0 is not None:
        same = True
        for i in range(1, 8):
            ki = _uniform_fast(x + (half if i & 1 else 0), y + (half if i & 2 else 0), z + (half if i & 4 else 0), half)
            if ki != k0:
                same = False
                break
        if same:
            res = k0
    _cache[key] = res
    return res


uniform = _uniform_fast  # noqa: F811

# ---------------------------------------------------------------------------
# Entités : départs de joueurs + lumières
# ---------------------------------------------------------------------------
ENTS = []  # (x, y, z, a1..a5, type)
ET_LIGHT, ET_PLAYERSTART = 1, 3


def center(box):
    x0, x1, y0, y1, z0, z1 = box
    return ((x0 + x1) / 2 * VOX, (y0 + y1) / 2 * VOX, z0 * VOX, z1 * VOX)


hx, hy, hz0, hz1 = center(ROOMBYID["accueil"].box)
# Départs alignés au sud du Hall, tournés vers le nord (yaw 0) : on voit le panneau d'accueil.
for dx in (-288, -192, -96, 96, 192, 288):
    ENTS.append((hx + dx, hy - 64, hz0 + 4, 0, 0, 0, 0, 0, ET_PLAYERSTART))
for r in list(ROOMS) + list(STANDROOMS.values()):
    cx, cy, z0, z1 = center(r.box)
    ENTS.append((cx, cy, z1 - 20, 300, 255, 245, 230, 0, ET_LIGHT))


def write_ogz(path):
    body = []
    hdr = struct.pack("<4s9i", b"OCTA", MAPVERSION, 40, WORLDSIZE, len(ENTS), 0, 0, 0, 0, 0)
    body.append(hdr)
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
    L = []
    L.append("// portfolio.cfg - généré par tools/gen_map.py, ne pas modifier à la main")
    L.append("// Réglages, textures et zones de la carte de la visite.")
    L.append("")
    L.append("maptitle " + cubescript_string("Visite du portfolio de Jules ROGUE"))
    L.append("skybox \"\"")
    L.append("ambient 0x404040")
    L.append("skylight 0x000000")
    L.append("fog 4000")
    L.append("fogcolour 0x0A1018")
    L.append("")
    L.append("texturereset")
    L.append("setshader stdworld")
    for name, line in TEXTURES:
        L.append(line + "   // " + name)
    L.append("")
    L.append("// --- Histoire et zones -----------------------------------------------")
    L.append("pfreset")
    L.append("pfobjective " + cubescript_string(STORY["objective"]))
    L.append("pfintrotitle " + cubescript_string(STORY["intro_title"]))
    L.append("pfintrotext " + cubescript_string(STORY["intro_text"]))
    L.append("pfendtitle " + cubescript_string(STORY["end_title"]))
    L.append("pfendtext " + cubescript_string(STORY["end_text"]))
    zoneboxes = []
    for r in ROOMS:
        if r.zone and r.rid != "galerie":
            zoneboxes.append((r.zone, r.box))
    for sid, sr in STANDROOMS.items():
        zoneboxes.append((sid, sr.box))
    # La galerie hors stands (allée) : zone d'information hors progression
    gal = ROOMBYID["galerie"].box
    zoneboxes.append(("galerie", (15, gal[1], gal[2], gal[3], gal[4], gal[5])))
    order = ["accueil", "profil", "competences", "leboncoin", "magic", "mineport", "cube2",
             "portfolioos", "certificats", "tux", "contact", "galerie"]
    zoneboxes.sort(key=lambda zb: order.index(zb[0]))
    for zid, (x0, x1, y0, y1, z0, z1) in zoneboxes:
        if zid == "galerie":
            title, text, story = ("Galerie des projets",
                                  "Cinq stands présentent les projets de Jules. Approche-toi de chacun "
                                  "pour restaurer son fragment.", False)
        else:
            title, text, story = ZONES[zid]
        L.append("pfzone %s %d %d %d %d %d %d %s %s %d" % (
            zid, x0 * VOX, y0 * VOX, z0 * VOX - 8, x1 * VOX, y1 * VOX, z1 * VOX + 8,
            cubescript_string(title), cubescript_string(text), 1 if story else -1))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "build/gamedata"
    base = os.path.join(out, "packages", "base")
    os.makedirs(base, exist_ok=True)
    n = write_ogz(os.path.join(base, "portfolio.ogz"))
    write_cfg(os.path.join(base, "portfolio.cfg"))
    print("portfolio.ogz : %d octets décompressés, %d entités, %d textures" % (n, len(ENTS), len(TEXTURES)))


if __name__ == "__main__":
    main()
