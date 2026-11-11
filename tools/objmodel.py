# -*- coding: utf-8 -*-
"""Mini-générateur de modèles OBJ « low poly » pour Cube 2.

Les modèles sont décrits en coordonnées du moteur (x = avant, y = côté, z = haut,
unités du monde : un joueur mesure ~15 unités) puis convertis vers le repère OBJ
attendu par le chargeur de Cube 2 (engine/obj.h : pos = (z, -x, y)).

Chaque modèle possède une « palette » (skin.png de 8x8 cases de couleur) et,
éventuellement, des groupes texturés par une image (écran, affiche...).
"""
import math
import os

from PIL import Image, ImageDraw


class Model:
    def __init__(self, name):
        self.name = name
        self.v, self.vt, self.vn = [], [], []
        self.groups = {}           # nom de groupe -> liste de faces [(vi, ti, ni)...]
        self.colors = []           # couleurs de palette utilisées
        self.images = {}           # groupe -> image PIL
        self.extra_cfg = []

    # --- utilitaires -----------------------------------------------------
    # Cube 2 divise l'échelle des modèles par 4 (animmodel::loaded) : on multiplie donc
    # les coordonnées pour que 1 unité ici = 1 unité du monde.
    UNIT = 4.0

    def _vert(self, p):
        x, y, z = (c * self.UNIT for c in p)
        self.v.append((-y, z, x))  # moteur -> OBJ
        return len(self.v)

    def _norm(self, n):
        x, y, z = n
        self.vn.append((-y, z, x))
        return len(self.vn)

    def _uv(self, u, v):
        self.vt.append((u, v))
        return len(self.vt)

    def _cell(self, color):
        color = tuple(color)
        if color not in self.colors:
            if len(self.colors) >= 64:
                raise ValueError("palette pleine pour " + self.name)
            self.colors.append(color)
        i = self.colors.index(color)
        return ((i % 8) * 8 + 4) / 64.0, 1.0 - ((i // 8) * 8 + 4) / 64.0

    def quad(self, pts, color=None, group="pal", uvs=None):
        """Quadrilatère (ou polygone) ; pts dans l'ordre anti-horaire vu de face."""
        a, b, c = pts[0], pts[1], pts[2]
        e1 = [b[i] - a[i] for i in range(3)]
        e2 = [c[i] - a[i] for i in range(3)]
        n = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
        ln = math.sqrt(sum(x * x for x in n)) or 1
        ni = self._norm(tuple(x / ln for x in n))
        if uvs is None:
            u, v = self._cell(color)
            t = self._uv(u, v)
            tis = [t] * len(pts)
        else:
            tis = [self._uv(u, v) for (u, v) in uvs]
        face = [(self._vert(p), tis[k], ni) for k, p in enumerate(pts)]
        self.groups.setdefault(group, []).append(face)

    def box(self, x0, x1, y0, y1, z0, z1, color, faces="xXyYzZ", img=None):
        """Boîte alignée. img = (groupe, faces texturées) : ces faces reçoivent toute l'image."""
        P = lambda x, y, z: (x, y, z)
        sides = {
            "x": [P(x0, y1, z0), P(x0, y0, z0), P(x0, y0, z1), P(x0, y1, z1)],
            "X": [P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1)],
            "y": [P(x0, y0, z0), P(x1, y0, z0), P(x1, y0, z1), P(x0, y0, z1)],
            "Y": [P(x1, y1, z0), P(x0, y1, z0), P(x0, y1, z1), P(x1, y1, z1)],
            "z": [P(x0, y0, z0), P(x0, y1, z0), P(x1, y1, z0), P(x1, y0, z0)],
            "Z": [P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)],
        }
        for f in faces:
            if img and f in img[1]:
                self.quad(sides[f], group=img[0], uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
            else:
                self.quad(sides[f], color)

    def cyl(self, cx, cy, z0, z1, r, color, seg=10, r1=None, caps=True, top=None):
        """Cylindre (ou tronc de cône si r1) vertical."""
        r1 = r if r1 is None else r1
        pts0 = [(cx + r * math.cos(2 * math.pi * i / seg), cy + r * math.sin(2 * math.pi * i / seg), z0) for i in range(seg)]
        pts1 = [(cx + r1 * math.cos(2 * math.pi * i / seg), cy + r1 * math.sin(2 * math.pi * i / seg), z1) for i in range(seg)]
        for i in range(seg):
            j = (i + 1) % seg
            self.quad([pts0[i], pts0[j], pts1[j], pts1[i]], color)
        if caps:
            self.quad(list(reversed(pts0)), color)
            if r1 > 0.01:
                self.quad(pts1, top or color)

    def hcyl(self, x0, x1, cy, cz, r, color, seg=10):
        """Cylindre horizontal selon l'axe x (canons, roues...)."""
        ring = lambda x: [(x, cy + r * math.cos(2 * math.pi * i / seg), cz + r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
        a, b = ring(x0), ring(x1)
        for i in range(seg):
            j = (i + 1) % seg
            self.quad([a[i], b[i], b[j], a[j]], color)
        self.quad(a, color)
        self.quad(list(reversed(b)), color)

    def ycyl(self, cx, y0, y1, cz, r, color, seg=10):
        """Cylindre horizontal selon l'axe y (roues de voiture)."""
        ring = lambda y: [(cx + r * math.cos(2 * math.pi * i / seg), y, cz + r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
        a, b = ring(y0), ring(y1)
        for i in range(seg):
            j = (i + 1) % seg
            self.quad([a[j], b[j], b[i], a[i]], color)
        self.quad(list(reversed(a)), color)
        self.quad(b, color)

    def sphere(self, cx, cy, cz, r, color, seg=8, rings=5, sz=1.0):
        pts = []
        for k in range(rings + 1):
            phi = math.pi * k / rings - math.pi / 2
            pts.append([(cx + r * math.cos(phi) * math.cos(2 * math.pi * i / seg),
                         cy + r * math.cos(phi) * math.sin(2 * math.pi * i / seg),
                         cz + r * sz * math.sin(phi)) for i in range(seg)])
        for k in range(rings):
            for i in range(seg):
                j = (i + 1) % seg
                q = [pts[k][i], pts[k][j], pts[k + 1][j], pts[k + 1][i]]
                if k == 0:
                    q = [pts[k][i], pts[k + 1][j], pts[k + 1][i]]
                elif k == rings - 1:
                    q = [pts[k][i], pts[k][j], pts[k + 1][i]]
                self.quad(q, color)

    def spikes(self, cx, cy, cz, r, length, color, n=12):
        """Pointes coniques autour d'une sphère (virus)."""
        for i in range(n):
            a = 2 * math.pi * i / n
            e = (i % 3 - 1) * 0.7
            d = (math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e))
            tip = (cx + d[0] * (r + length), cy + d[1] * (r + length), cz + d[2] * (r + length))
            base = (cx + d[0] * r * 0.8, cy + d[1] * r * 0.8, cz + d[2] * r * 0.8)
            # petit tétraèdre
            ux = (-d[1], d[0], 0) if abs(d[2]) < 0.9 else (1, 0, 0)
            w = r * 0.25
            b1 = tuple(base[k] + ux[k] * w for k in range(3))
            b2 = tuple(base[k] - ux[k] * w for k in range(3))
            b3 = tuple(base[k] + (0, 0, w)[k] for k in range(3))
            self.quad([b1, b2, tip], color)
            self.quad([b2, b3, tip], color)
            self.quad([b3, b1, tip], color)

    # --- écriture -----------------------------------------------------------
    def save(self, root, ambient=40, spec=0, scale=None, collide=True):
        d = os.path.join(root, "packages", "models", self.name)
        os.makedirs(d, exist_ok=True)
        L = ["# %s - généré par tools/gen_assets.py (création originale, licence zlib)" % self.name]
        L += ["v %.3f %.3f %.3f" % p for p in self.v]
        L += ["vt %.4f %.4f" % t for t in self.vt]
        L += ["vn %.4f %.4f %.4f" % n for n in self.vn]
        for g, faces in self.groups.items():
            L.append("g " + g)
            for f in faces:
                L.append("f " + " ".join("%d/%d/%d" % x for x in f))
        with open(os.path.join(d, "tris.obj"), "w") as fh:
            fh.write("\n".join(L) + "\n")
        skin = Image.new("RGB", (64, 64), (128, 128, 128))
        dr = ImageDraw.Draw(skin)
        for i, c in enumerate(self.colors):
            x, y = (i % 8) * 8, (i // 8) * 8
            dr.rectangle([x, y, x + 7, y + 7], fill=c)
        skin.save(os.path.join(d, "skin.png"), optimize=True)
        cfg = ['objload "tris.obj"']
        for g in self.groups:
            if g == "pal":
                cfg.append('objskin pal "skin.png"')
            else:
                self.images[g].convert("RGB").save(os.path.join(d, g + ".jpg"), quality=88, optimize=True)
                cfg.append('objskin %s "%s.jpg"' % (g, g))
        cfg += ["mdlspec %d" % spec, "mdlambient %d" % ambient]
        if scale:
            cfg.append("mdlscale %d" % scale)
        if not collide:
            cfg.append("mdlcollide 0")
        cfg += self.extra_cfg
        with open(os.path.join(d, "obj.cfg"), "w") as fh:
            fh.write("\n".join(cfg) + "\n")
