# -*- coding: utf-8 -*-
"""Tous les modèles 3D du jeu, générés par script (créations originales, licence zlib) :

- avatar des visiteurs et ses armes à la première personne (hudguns) ;
- monstres (virus, bug, glitch) ;
- objets ramassables (munitions, santé, armure), projectiles, débris ;
- décors thématiques de chaque salle (bibliothèque, salle serveur, garage,
  néons, voxels, arène, bureau Ubuntu, trophées, banquise, bureau de poste).

Repère : x = avant, y = côté, z = haut ; un joueur mesure ~15 unités.
"""
import math
import random

from PIL import Image, ImageDraw, ImageFont

from objmodel import Model

# --- couleurs ---------------------------------------------------------------
WHITE, BLACK = (235, 238, 242), (24, 26, 30)
GREY, DARK, STEEL = (130, 134, 140), (52, 56, 64), (170, 176, 186)
RED, ORANGE, YELLOW = (220, 50, 50), (240, 130, 30), (245, 205, 50)
GREEN, BLUE, CYAN = (70, 190, 80), (60, 120, 230), (80, 220, 230)
PURPLE, PINK, BROWN = (150, 70, 220), (240, 80, 180), (120, 76, 44)
WOOD, WOODL, GOLD = (140, 92, 52), (176, 124, 76), (230, 186, 60)

_fontcache = {}


def _font(size, bold=True):
    import gen_assets
    return gen_assets.font(size, bold)

# ---------------------------------------------------------------------------
# Avatar + armes
# ---------------------------------------------------------------------------


def avatar(root):
    m = Model("pfavatar")
    m.box(-1.2, 1.2, 0.6, 2.6, 0, 6, DARK)            # jambes
    m.box(-1.2, 1.2, -2.6, -0.6, 0, 6, DARK)
    m.box(-2, 2, -3.4, 3.4, 6, 11.5, BLUE)            # torse
    m.box(1.9, 2.1, -1.5, 1.5, 7, 10, YELLOW)         # écusson
    m.box(-1, 1, 3.4, 4.6, 6.5, 11, WHITE)            # bras
    m.box(-1, 1, -4.6, -3.4, 6.5, 11, WHITE)
    m.box(-2.4, 2.4, -2.6, 2.6, 11.5, 16, WHITE)      # tête
    m.box(2.4, 2.6, -2, 2, 13, 15, CYAN)              # visière
    m.box(-0.3, 0.3, -0.3, 0.3, 16, 18, YELLOW)       # antenne
    m.save(root, ambient=50)
    hudguns(root)


class _Shift(Model):
    """Décale les armes vers l'avant (X0 unités) pour qu'elles restent petites à l'écran."""
    X0 = 16.0
    UNIT = 1.0  # les armes à la 1re personne ont un rendu dédié : échelle d'origine conservée

    def _vert(self, p):
        return Model._vert(self, (p[0] + self.X0, p[1], p[2]))


def _gun(name, build):
    m = _Shift("pfavatar/hudguns/" + name)
    build(m)
    return m


def hudguns(root):
    # Arme tenue à droite, sous les yeux ; canon vers +x. Origine = oeil du joueur.
    # (dans ce repère, +y est à droite de l'écran une fois l'arme affichée)
    Y, Z = 3.2, -3.4

    def pistol(m):
        m.box(2, 8, Y - 0.6, Y + 0.6, Z, Z + 1.3, DARK)
        m.box(2.5, 3.8, Y - 0.5, Y + 0.5, Z - 2.5, Z, BLACK)
        m.box(7.6, 8.1, Y - 0.3, Y + 0.3, Z + 1.2, Z + 1.6, ORANGE)

    def shotgun(m):
        m.hcyl(3, 14, Y + 0.45, Z + 0.8, 0.45, STEEL)
        m.hcyl(3, 14, Y - 0.45, Z + 0.8, 0.45, STEEL)
        m.box(1, 6, Y - 0.9, Y + 0.9, Z - 0.4, Z + 0.4, WOOD)
        m.box(1, 2.6, Y - 0.6, Y + 0.6, Z - 3, Z - 0.3, WOOD)

    def chaingun(m):
        for a in range(6):
            ang = a * math.pi / 3
            m.hcyl(4, 15, Y + 0.7 * math.cos(ang), Z + 0.6 + 0.7 * math.sin(ang), 0.25, STEEL, seg=6)
        m.box(1, 5, Y - 1.3, Y + 1.3, Z - 0.8, Z + 1.8, DARK)
        m.box(2, 3.4, Y - 0.5, Y + 0.5, Z - 3, Z - 0.8, BLACK)
        m.box(4.5, 5.5, Y - 1.4, Y + 1.4, Z + 1.8, Z + 2.2, GREEN)

    def rocket(m):
        m.hcyl(0, 15, Y, Z + 1.2, 1.4, (90, 110, 70), seg=10)
        m.hcyl(14.5, 15.2, Y, Z + 1.2, 1.6, RED, seg=10)
        m.box(3, 4.4, Y - 0.5, Y + 0.5, Z - 2.4, Z, BLACK)
        m.box(5, 9, Y + 1.3, Y + 1.8, Z + 1.6, Z + 2.4, YELLOW)

    def rifle(m):
        m.hcyl(4, 18, Y, Z + 0.9, 0.35, BLACK)
        m.box(0.5, 8, Y - 0.6, Y + 0.6, Z - 0.3, Z + 0.7, (60, 80, 110))
        m.hcyl(4, 9, Y, Z + 2.1, 0.6, DARK)            # lunette
        m.box(1.5, 2.8, Y - 0.5, Y + 0.5, Z - 2.6, Z - 0.3, BLACK)
        m.box(8, 8.6, Y - 0.2, Y + 0.2, Z + 2.6, Z + 2.9, CYAN)

    def grenade(m):
        m.hcyl(3, 11, Y, Z + 0.8, 1.1, (70, 90, 60), seg=8)
        m.box(1, 5, Y - 1.2, Y + 1.2, Z - 0.6, Z + 0.6, DARK)
        m.box(2, 3.3, Y - 0.5, Y + 0.5, Z - 2.8, Z - 0.6, BLACK)
        m.hcyl(10.8, 11.3, Y, Z + 0.8, 1.3, ORANGE, seg=8)

    def fist(m):
        # « scie » : clé de dépannage / tronçonneuse stylisée
        m.box(3, 13, Y - 0.25, Y + 0.25, Z, Z + 1.6, STEEL)
        for k in range(10):
            m.box(3.2 + k, 3.8 + k, Y - 0.3, Y + 0.3, Z + 1.6, Z + 2, DARK)
        m.box(0.5, 4, Y - 1, Y + 1, Z - 0.8, Z + 1.8, ORANGE)

    for name, fn in (("pistol", pistol), ("shotg", shotgun), ("chaing", chaingun), ("rocket", rocket),
                     ("rifle", rifle), ("gl", grenade), ("fist", fist)):
        _gun(name, fn).save(root, ambient=60, collide=False)

# ---------------------------------------------------------------------------
# Monstres (bots) : le joueur doit faire ~15 unités de haut, pieds en z=0
# ---------------------------------------------------------------------------


def monsters(root):
    # Virus : boule hérissée qui flotte
    m = Model("pfmonster/virus")
    m.sphere(0, 0, 9, 5, (120, 210, 60), seg=10, rings=7)
    m.spikes(0, 0, 9, 5, 3.2, (220, 60, 60), n=18)
    m.box(4.3, 5.2, -2.2, -0.6, 10, 11.6, WHITE)
    m.box(4.3, 5.2, 0.6, 2.2, 10, 11.6, WHITE)
    m.box(5.0, 5.4, -1.8, -1.0, 10.4, 11.2, BLACK)
    m.box(5.0, 5.4, 1.0, 1.8, 10.4, 11.2, BLACK)
    m.cyl(0, 0, 0, 4, 0.6, (90, 160, 50), seg=6)
    m.save(root, ambient=40, scale=130)

    # Bug : scarabée à six pattes
    m = Model("pfmonster/bug")
    m.sphere(0, 0, 6, 6, (40, 40, 48), seg=10, rings=6, sz=0.7)
    m.box(-5.5, 5.5, -0.3, 0.3, 9.6, 10.4, RED)       # séparation des élytres
    m.sphere(6.5, 0, 6, 2.8, (30, 30, 34), seg=8, rings=5)
    m.box(8.6, 9.2, -1.6, -0.6, 6.6, 7.6, RED)        # yeux
    m.box(8.6, 9.2, 0.6, 1.6, 6.6, 7.6, RED)
    for side in (-1, 1):
        for k in (-3, 0, 3):
            m.box(k - 0.4, k + 0.4, side * 4, side * 8, 3.5, 4.3, BLACK)
            m.box(k - 0.4, k + 0.4, side * 7.6, side * 8.4, 0, 4.3, BLACK)
        m.box(8, 12, side * 0.8 - 0.2, side * 0.8 + 0.2, 8, 8.4, BLACK)   # antennes
    m.save(root, ambient=40, scale=130)

    # Glitch : amas de cubes corrompus (couleurs RVB)
    m = Model("pfmonster/glitch")
    rr = random.Random(7)
    cols = [(255, 0, 80), (0, 255, 200), (60, 80, 255), (255, 255, 255), (20, 20, 20)]
    for i in range(16):
        s = rr.uniform(1.4, 3.2)
        x, y, z = rr.uniform(-3, 3), rr.uniform(-3.5, 3.5), rr.uniform(1, 13)
        m.box(x - s, x + s, y - s, y + s, z - s * 0.6, z + s * 0.6, rr.choice(cols))
    m.box(3.4, 4.6, -2.5, 2.5, 11, 12.4, (0, 255, 120))  # « bandeau » lumineux
    m.save(root, ambient=60, scale=130)

# ---------------------------------------------------------------------------
# Objets ramassables, projectiles, débris
# ---------------------------------------------------------------------------


def items(root):
    def ammo(name, col, label_col):
        m = Model(name)
        m.box(-3, 3, -2.2, 2.2, 0, 3.2, col)
        m.box(-3.05, 3.05, -1.2, 1.2, 1, 2.2, label_col)
        m.box(-2.4, 2.4, -1.6, 1.6, 3.2, 3.6, DARK)
        m.save(root, ambient=60)
    ammo("ammo/shells", (180, 40, 40), YELLOW)
    ammo("ammo/bullets", (200, 170, 40), DARK)
    ammo("ammo/rockets", (70, 100, 60), RED)
    ammo("ammo/rrounds", (60, 80, 120), CYAN)
    ammo("ammo/grenades", (80, 110, 50), ORANGE)
    ammo("ammo/cartridges", (90, 90, 96), WHITE)

    m = Model("health")
    m.box(-1.2, 1.2, -4, 4, 1, 3.4, RED)
    m.box(-1.2, 1.2, -1.2, 1.2, -1.8, 6.2, RED)
    m.box(-1.3, 1.3, -4.2, 4.2, 1.6, 2.8, WHITE)
    m.save(root, ambient=70)
    m = Model("boost")
    m.sphere(0, 0, 3, 3.2, (255, 80, 80), seg=8, rings=5)
    m.box(-0.6, 0.6, -0.6, 0.6, 5.5, 8, WHITE)
    m.save(root, ambient=70)
    for name, col in (("armor/green", GREEN), ("armor/yellow", YELLOW)):
        m = Model(name)
        m.box(-1.5, 1.5, -4, 4, 0, 7, col)
        m.box(-1.6, 1.6, -1.2, 1.2, 1, 6, DARK)
        m.box(-1.5, 1.5, -5.4, -4, 4.5, 7, col)
        m.box(-1.5, 1.5, 4, 5.4, 4.5, 7, col)
        m.save(root, ambient=60)
    m = Model("quad")
    m.sphere(0, 0, 3, 3, PURPLE, seg=8, rings=5)
    m.save(root, ambient=80)

    m = Model("projectiles/rocket")
    m.hcyl(-3, 3, 0, 0, 0.7, (200, 200, 200), seg=8)
    m.hcyl(3, 4, 0, 0, 0.5, RED, seg=8)
    m.box(-3, -2, -1.4, 1.4, -0.15, 0.15, DARK)
    m.save(root, ambient=80, collide=False)
    m = Model("projectiles/grenade")
    m.sphere(0, 0, 0, 1.2, (80, 110, 50), seg=8, rings=5)
    m.box(-0.3, 0.3, -0.3, 0.3, 1, 1.8, ORANGE)
    m.save(root, ambient=80, collide=False)

    m = Model("teleporter")
    m.cyl(0, 0, 0, 1.5, 10, (60, 200, 255), seg=16)
    m.save(root, ambient=80, collide=False)

    # Armes vues dans la main des autres joueurs (vwep) : sans « tag », le modèle est
    # attaché à l'origine du joueur, on le place donc directement à hauteur de main.
    vcol = {"fist": ORANGE, "shotg": WOOD, "chaing": DARK, "rocket": (90, 110, 70),
            "rifle": (60, 80, 110), "gl": (70, 90, 60), "pistol": BLACK}
    for name, col in vcol.items():
        m = Model("vwep/" + name)
        length = 5 if name in ("pistol", "fist") else 9
        m.box(1, 1 + length, 3.6, 5.0, 8, 9.4, col)
        m.box(1, 2.4, 3.8, 4.8, 6.4, 8, BLACK)
        m.save(root, ambient=50, collide=False)

    for i in range(1, 5):   # débris : petits voxels
        m = Model("barreldebris/debris%02d" % i)
        s = 0.5 + 0.25 * i
        m.box(-s, s, -s, s, -s, s, BROWN)
        m.save(root, ambient=40, collide=False)

    for i in range(1, 5):   # débris : petits voxels
        m = Model("debris/debris%02d" % i)
        s = 0.6 + 0.3 * i
        m.box(-s, s, -s, s, -s, s, [GREY, DARK, BROWN, STEEL][i - 1])
        m.save(root, ambient=40, collide=False)
    for i in range(1, 4):   # « gibs » : octets lumineux (on reste tout public)
        m = Model("gibs/gib%02d" % i)
        s = 0.8
        m.box(-s, s, -s, s, -s, s, [CYAN, (0, 255, 120), PINK][i - 1])
        m.save(root, ambient=90, collide=False)

# ---------------------------------------------------------------------------
# Images des groupes texturés (écran, livres, diplôme...)
# ---------------------------------------------------------------------------


def img_desktop():
    W, H = 512, 288
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(119 * (1 - t) + 44 * t), int(41 * (1 - t)), int(83 * (1 - t) + 30 * t)))
    d.rectangle([0, 0, W, 16], fill=(20, 20, 20))
    d.text((W // 2, 8), "julesrogue.fr - Portfolio OS", font=_font(11), fill=(240, 240, 240), anchor="mm")
    d.rectangle([0, 16, 40, H], fill=(30, 20, 30))
    for k, c in enumerate([(233, 84, 32), (60, 150, 230), (90, 200, 90), (240, 200, 60), (190, 110, 255)]):
        d.rounded_rectangle([6, 26 + k * 42, 34, 54 + k * 42], radius=6, fill=c)
    for (x, y, w, h, title, col) in [(70, 40, 200, 130, "Curriculum Vitae", (60, 150, 230)),
                                     (230, 90, 220, 150, "Compétences BTS SIO", (90, 200, 90)),
                                     (120, 170, 170, 100, "Tux World", (240, 200, 60))]:
        d.rectangle([x, y, x + w, y + h], fill=(246, 246, 246), outline=(60, 60, 60))
        d.rectangle([x, y, x + w, y + 18], fill=col)
        d.text((x + 8, y + 9), title, font=_font(12), fill=(255, 255, 255), anchor="lm")
        for l in range(4):
            d.rectangle([x + 10, y + 30 + l * 18, x + w - 20 - l * 15, y + 38 + l * 18], fill=(200, 200, 205))
    return img


def img_rack():
    img = Image.new("RGB", (128, 256), (20, 22, 26))
    d = ImageDraw.Draw(img)
    rr = random.Random(3)
    for k in range(10):
        y = 8 + k * 24
        d.rectangle([8, y, 120, y + 20], fill=(44, 48, 56), outline=(70, 74, 82))
        for j in range(6):
            d.rectangle([16 + j * 12, y + 6, 24 + j * 12, y + 14], fill=(30, 30, 34))
        for j in range(3):
            c = rr.choice([(40, 255, 90), (40, 180, 255), (255, 170, 40), (40, 255, 90)])
            d.ellipse([92 + j * 9, y + 7, 98 + j * 9, y + 13], fill=c)
    return img


def img_books():
    import gen_assets
    return gen_assets.bookshelf_tex(seed=9).resize((128, 256))


def img_diploma():
    img = Image.new("RGB", (384, 272), (240, 230, 200))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 383, 271], outline=(170, 130, 40), width=14)
    d.rectangle([22, 22, 361, 249], outline=(200, 170, 90), width=2)
    d.text((192, 60), "CERTIFICAT", font=_font(30), fill=(120, 80, 20), anchor="mm")
    d.text((192, 110), "Cisco Networking Academy", font=_font(16, False), fill=(40, 40, 40), anchor="mm")
    d.text((192, 145), "Introduction to Cybersecurity", font=_font(20), fill=(20, 60, 120), anchor="mm")
    d.text((192, 182), "décerné à Jules ROGUE", font=_font(16, False), fill=(40, 40, 40), anchor="mm")
    d.ellipse([290, 190, 340, 240], fill=(190, 40, 40), outline=(120, 20, 20), width=3)
    return img


def img_poster(title, sub, col):
    img = Image.new("RGB", (256, 256), (20, 20, 28))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 255, 255], outline=col, width=10)
    d.text((128, 100), title, font=_font(30), fill=col, anchor="mm")
    d.text((128, 150), sub, font=_font(16, False), fill=(230, 230, 230), anchor="mm")
    return img


def img_car_plate():
    img = Image.new("RGB", (128, 32), (240, 240, 240))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 12, 31], fill=(30, 60, 170))
    d.text((70, 16), "LBC-2026", font=_font(18), fill=(20, 20, 20), anchor="mm")
    return img

# ---------------------------------------------------------------------------
# Décors des salles (mapmodels « pf/... »)
# ---------------------------------------------------------------------------


def props(root):
    P = {}

    def new(name):
        m = Model("pf/" + name)
        P[name] = m
        return m

    # --- Hall -------------------------------------------------------------
    m = new("reception")
    m.box(-6, 6, -20, 20, 0, 11, (90, 94, 104))
    m.box(-7, 7, -21, 21, 11, 12.5, (200, 200, 206))
    m.box(6, 6.3, -16, 16, 3, 8, YELLOW)
    m = new("plant")
    m.cyl(0, 0, 0, 6, 3, (180, 90, 60), seg=8, r1=3.6)
    for k in range(7):
        a = k * 0.9
        m.sphere(math.cos(a) * 2.2, math.sin(a) * 2.2, 9 + (k % 3) * 2.5, 2.8, (50, 140 + k * 8, 60), seg=6, rings=4)
    m = new("bench")
    m.box(-4, 4, -16, 16, 4, 5.5, WOODL)
    for y in (-13, 13):
        m.box(-3.5, 3.5, y - 1, y + 1, 0, 4, DARK)

    # --- Profil : bibliothèque / bureau ------------------------------------
    m = new("bookshelf")
    m.images["books"] = img_books()
    m.box(-5, 5, -16, 16, 0, 44, WOOD, img=("books", "X"))
    m.box(5, 5.6, -16, 16, 43, 45, WOODL)
    m = new("desk")
    m.box(-8, 8, -16, 16, 12, 13.5, WOODL)
    for x in (-7, 7):
        for y in (-15, 15):
            m.box(x - 0.8, x + 0.8, y - 0.8, y + 0.8, 0, 12, WOOD)
    m.images["screen"] = img_desktop()
    m.box(-4, -3, -7, 7, 14.5, 23, BLACK, img=("screen", "X"))
    m.box(-4, -3, -1, 1, 13.5, 14.5, DARK)
    m.box(1, 5, -5, 5, 13.5, 14.2, (40, 40, 44))         # clavier
    m.cyl(5, 12, 13.5, 15, 1.4, WHITE, seg=8)             # tasse
    m = new("chair")
    m.box(-4, 4, -4, 4, 7, 8.5, (40, 70, 140))
    m.box(-5, -4, -4, 4, 8.5, 17, (40, 70, 140))
    m.cyl(0, 0, 0, 7, 0.6, DARK, seg=6)
    m.box(-4, 4, -0.4, 0.4, 0, 0.8, DARK)
    m.box(-0.4, 0.4, -4, 4, 0, 0.8, DARK)
    m = new("lamp")
    m.cyl(0, 0, 0, 1, 3, DARK, seg=8)
    m.cyl(0, 0, 1, 26, 0.4, STEEL, seg=6)
    m.cyl(0, 0, 24, 30, 5, (250, 230, 170), seg=10, r1=2.5)
    m = new("badminton")
    m.box(-0.4, 0.4, -0.4, 0.4, 0, 9, WHITE)
    m.cyl(0, 0, 9, 9.5, 4, (40, 200, 120), seg=12)
    m.cyl(6, 0, 0, 1.2, 1, WHITE, seg=6)
    m.cyl(6, 0, 1.2, 3.5, 1, WHITE, seg=6, r1=2)

    # --- Compétences : salle serveur / labo --------------------------------
    m = new("rack")
    m.images["rack"] = img_rack()
    m.box(-9, 9, -8, 8, 0, 50, (30, 32, 38), img=("rack", "X"))
    m.box(9, 9.4, -8, 8, 48, 50, (40, 150, 255))
    m = new("labtable")
    m.box(-8, 8, -20, 20, 12, 13.5, (220, 222, 226))
    m.box(-7.5, 7.5, -19, 19, 0, 12, (90, 96, 110))
    m.images["screen"] = img_poster("SLAM", "dev  -  données  -  cyber", (90, 220, 130))
    m.box(-5, -4, -9, 9, 13.5, 26, BLACK, img=("screen", "X"))
    for k, c in enumerate([RED, CYAN, YELLOW]):
        m.cyl(3, -12 + k * 5, 13.5, 17, 1.2, c, seg=8, r1=0.6)
    m = new("cables")
    for k, c in enumerate([BLUE, YELLOW, RED, GREEN]):
        m.box(-1, 1, -40 + k * 2.5, -38.5 + k * 2.5, 0, 1.2, c)

    # --- Leboncoin : garage -------------------------------------------------
    m = new("car")
    m.images["plate"] = img_car_plate()
    m.box(-22, 22, -10, 10, 3, 11, (40, 110, 210))
    m.box(-10, 10, -9, 9, 11, 18, (40, 110, 210))
    m.box(10, 10.3, -8, 8, 11.5, 17, (150, 200, 230))        # pare-brise
    m.box(-10.3, -10, -8, 8, 11.5, 17, (150, 200, 230))
    m.box(-9, 9, 9, 9.3, 12, 17, (150, 200, 230))
    m.box(-9, 9, -9.3, -9, 12, 17, (150, 200, 230))
    m.box(22, 22.2, -3, 3, 4, 6, BLACK, img=("plate", "X"))
    m.box(21.8, 22.3, -8.5, -6, 7, 9, YELLOW)                # phares
    m.box(21.8, 22.3, 6, 8.5, 7, 9, YELLOW)
    m.box(-22.3, -21.8, -8.5, -6, 7, 9, RED)
    m.box(-22.3, -21.8, 6, 8.5, 7, 9, RED)
    for x in (-13, 13):
        for y0, y1 in ((-11, -8), (8, 11)):
            m.ycyl(x, y0, y1, 4, 4, BLACK, seg=10)
    m = new("tires")
    for k in range(4):
        m.cyl(0, 0, k * 3, k * 3 + 3, 5, BLACK, seg=12, top=DARK)
    m = new("toolbox")
    m.box(-6, 6, -10, 10, 0, 22, RED)
    for k in range(4):
        m.box(6, 6.3, -9, 9, 2 + k * 5, 6 + k * 5, (190, 30, 30))
        m.box(6.3, 6.6, -3, 3, 4 + k * 5, 4.8 + k * 5, STEEL)
    m = new("sale_sign")
    m.images["sign"] = img_poster("À VENDRE", "annonce n°1802", (255, 120, 30))
    m.box(-0.4, 0.4, -0.4, 0.4, 0, 22, STEEL)
    m.box(-0.6, 0.6, -9, 9, 22, 38, WHITE, img=("sign", "Xx"))

    # --- Magic Shape Generator : salle rythmique / néons -------------------
    m = new("planets")
    m.sphere(0, -9, 18, 6, (255, 90, 40), seg=12, rings=8)     # planète de feu
    m.sphere(0, 9, 18, 6, (60, 160, 255), seg=12, rings=8)     # planète de glace
    m.box(-0.5, 0.5, -9, 9, 17.5, 18.5, WHITE)
    m.cyl(0, 0, 0, 12, 1, (200, 80, 255), seg=8)
    m = new("neonring")
    for k in range(16):
        a0, a1 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
        c = PINK if k % 2 else CYAN
        y0, z0, y1, z1 = 18 * math.cos(a0), 22 + 18 * math.sin(a0), 18 * math.cos(a1), 22 + 18 * math.sin(a1)
        m.quad([(0, y0, z0), (0, y1, z1), (0, y1 * 0.85, 22 + (z1 - 22) * 0.85), (0, y0 * 0.85, 22 + (z0 - 22) * 0.85)], c)
        m.quad([(0, y0 * 0.85, 22 + (z0 - 22) * 0.85), (0, y1 * 0.85, 22 + (z1 - 22) * 0.85), (0, y1, z1), (0, y0, z0)], c)
    m = new("rhythmtile")
    for k in range(6):
        m.box(-4 + k * 1.2, 4 + k * 1.2, -4 + (k % 2) * 8, 4 + (k % 2) * 8, 0, 0.8, [PINK, CYAN, YELLOW][k % 3])

    # --- Mineport : voxels --------------------------------------------------
    m = new("voxeltree")
    m.box(-3, 3, -3, 3, 0, 24, (110, 80, 50))
    m.box(-12, 12, -12, 12, 24, 36, (50, 120, 40))
    m.box(-7, 7, -7, 7, 36, 44, (60, 140, 50))
    m = new("voxelblocks")
    for (x, y, z, c) in [(0, 0, 0, (86, 160, 60)), (12, 0, 0, (130, 90, 60)), (0, 12, 0, (128, 128, 128)),
                         (6, 6, 12, (86, 160, 60)), (12, 12, 0, (210, 190, 120))]:
        m.box(x - 6, x + 6, y - 6, y + 6, z, z + 12, c)
    m = new("voxelore")
    m.box(-6, 6, -6, 6, 0, 12, (128, 128, 128))
    for (y, z) in [(-3, 3), (2, 7), (-1, 9)]:
        m.box(6, 6.4, y - 1.2, y + 1.2, z - 1.2, z + 1.2, (80, 220, 230))

    # --- Cube 2 : arène -----------------------------------------------------
    m = new("crate")
    m.box(-8, 8, -8, 8, 0, 16, (150, 110, 60))
    for f in (-8.2, 8.2):
        m.box(f - 0.1 if f < 0 else f - 0.2, f + 0.2 if f < 0 else f + 0.1, -7, 7, 7, 9, (100, 70, 40))
    m = new("arenapillar")
    m.box(-6, 6, -6, 6, 0, 60, (70, 74, 84))
    m.box(-6.4, 6.4, -6.4, 6.4, 26, 30, (255, 80, 40))
    m = new("target")
    for k, c in enumerate([WHITE, RED, WHITE, RED]):
        r = 10 - k * 2.4
        m.cyl(0, 0, 14 + k * 0.3, 14.3 + k * 0.3, r, c, seg=16)
    m.cyl(0, 0, 0, 14, 0.6, DARK, seg=6)

    # --- Portfolio OS : bureau Ubuntu géant ---------------------------------
    m = new("monitor")
    m.images["screen"] = img_desktop()
    m.box(-3, 3, -48, 48, 18, 72, (30, 30, 34), img=("screen", "Xx"))
    m.box(-2, 2, -4, 4, 0, 18, (50, 50, 56))
    m.box(-10, 10, -16, 16, 0, 2, (50, 50, 56))
    m = new("keyboard")
    m.box(-8, 8, -30, 30, 0, 3, (40, 40, 44))
    for r in range(4):
        for k in range(14):
            m.box(-6 + r * 3.5, -4 + r * 3.5, -27 + k * 4, -24.5 + k * 4, 3, 4, (210, 210, 214))

    # --- Certificats : salle des trophées -----------------------------------
    m = new("trophy")
    m.box(-6, 6, -6, 6, 0, 14, (230, 228, 220))
    m.box(-4, 4, -4, 4, 14, 16, (60, 60, 64))
    m.cyl(0, 0, 16, 18, 1, GOLD, seg=8)
    m.cyl(0, 0, 18, 26, 1.8, GOLD, seg=10, r1=4)
    for side in (-1, 1):
        m.box(-0.5, 0.5, side * 4, side * 6, 21, 25, GOLD)
    m = new("diploma")
    m.images["diploma"] = img_diploma()
    m.box(-0.6, 0.6, -14, 14, 0, 20, (150, 110, 40), img=("diploma", "X"))
    m = new("medal")
    m.box(-0.4, 0.4, -1, 1, 8, 16, BLUE)
    m.cyl(0, 0, 4, 8, 0.1, GOLD, seg=4)
    m.ycyl(0, -0.4, 0.4, 6, 3, GOLD, seg=12)

    # --- Tux World : banquise -----------------------------------------------
    m = new("penguin")
    m.sphere(0, 0, 5, 5, BLACK, seg=10, rings=6, sz=1.2)
    m.sphere(1.6, 0, 5, 3.8, WHITE, seg=10, rings=6, sz=1.2)
    m.sphere(0, 0, 12.5, 3.2, BLACK, seg=10, rings=6)
    m.box(2.6, 3.4, -1.6, -0.6, 13, 14, WHITE)
    m.box(2.6, 3.4, 0.6, 1.6, 13, 14, WHITE)
    m.box(3.3, 3.6, -1.3, -0.9, 13.3, 13.8, BLACK)
    m.box(3.3, 3.6, 0.9, 1.3, 13.3, 13.8, BLACK)
    m.box(2.6, 5.5, -1, 1, 11.4, 12.4, (250, 180, 30))      # bec
    for y in (-2.5, 2.5):
        m.box(0, 4.5, y - 1.3, y + 1.3, 0, 0.8, (250, 180, 30))  # pattes
        m.box(-1.5, 1.5, y * 2 - 0.6, y * 2 + 0.6, 3, 8, BLACK)  # ailerons
    m = new("igloo")
    m.sphere(0, 0, 0, 22, (240, 246, 252), seg=14, rings=8)
    m.box(14, 26, -6, 6, 0, 11, (230, 238, 248))
    m.box(25.9, 26.2, -4, 4, 0, 9, (40, 50, 70))
    m = new("snowman")
    m.sphere(0, 0, 6, 6, WHITE, seg=10, rings=6)
    m.sphere(0, 0, 15, 4.2, WHITE, seg=10, rings=6)
    m.sphere(0, 0, 21.5, 3, WHITE, seg=10, rings=6)
    m.box(2.6, 6, -0.5, 0.5, 21, 22, ORANGE)
    m.cyl(0, 0, 24, 28, 2.2, BLACK, seg=8)
    m = new("iceblock")
    m.box(-8, 8, -8, 8, 0, 10, (180, 220, 245))

    # --- Contact : bureau de poste ------------------------------------------
    m = new("mailbox")
    m.box(-5, 5, -6, 6, 0, 26, (245, 205, 50))
    m.cyl(0, 0, 26, 27, 6, (245, 205, 50), seg=10)
    m.box(5, 5.3, -3.5, 3.5, 18, 20, BLACK)
    m.box(5, 5.3, -4, 4, 8, 14, (30, 70, 150))
    m = new("parcels")
    for (x, y, z, s) in [(0, 0, 0, 7), (0, 14, 0, 5), (2, 5, 14, 5), (-1, 18, 10, 3.5)]:
        m.box(x - s, x + s, y - s, y + s, z, z + 2 * s * 0.8, (190, 150, 100))
        m.box(x - s - 0.1, x + s + 0.1, y - 0.6, y + 0.6, z, z + 2 * s * 0.8 + 0.1, (150, 110, 70))
    m = new("counter")
    m.box(-6, 6, -28, 28, 0, 13, (30, 70, 150))
    m.box(-7, 7, -29, 29, 13, 14.5, (245, 205, 50))
    m.images["sign"] = img_poster("CONTACT", "jules.rogue@ploud.fr", (60, 120, 230))
    m.box(-1, 1, -12, 12, 14.5, 32, WHITE, img=("sign", "Xx"))
    m = new("phone")
    m.box(-3, 3, -4, 4, 0, 2.5, BLACK)
    m.box(-1, 1, -4.5, 4.5, 2.5, 3.6, BLACK)
    m.box(1.6, 3.1, -2, 2, 2.5, 2.8, RED)

    for name, mdl in P.items():
        mdl.save(root, ambient=30, spec=0)
    return sorted(P)


def main(root):
    avatar(root)
    monsters(root)
    items(root)
    return props(root)
