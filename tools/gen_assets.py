#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère les SEULS visuels « maison » du client, ceux qui n'existent pas dans
Cube 2: Sauerbraten (tout le reste — armes, modèles, sons, textures, HUD — vient du
jeu de base, voir tools/sauer_assets.txt) :

- images d'interface de Cube 2 (fond, logo, réticule, skin des menus...) ;
- textures procédurales de la carte (sols, murs, plafond) ;
- panneaux muraux avec texte (contenu de tools/content.py) ;
- l'avatar des joueurs (modèle OBJ « robot » + skin) ;
- quelques textures de particules / HUD attendues par le moteur.

Usage : gen_assets.py <dossier_sortie>
Dépendance : Pillow ; police DejaVu Sans (paquet fonts-dejavu-core), ou
variable d'environnement PF_FONT / PF_FONT_BOLD.
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from content import PANELS  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "build/gamedata"


def find_font(bold):
    env = os.environ.get("PF_FONT_BOLD" if bold else "PF_FONT")
    cands = [env] if env else []
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    cands += ["/usr/share/fonts/truetype/dejavu/" + name, "/usr/share/fonts/dejavu/" + name,
              "/usr/share/fonts/TTF/" + name]
    for c in cands:
        if c and os.path.exists(c):
            return c
    raise SystemExit("Police DejaVu introuvable (installer fonts-dejavu-core ou définir PF_FONT)")


FONT = find_font(False)
FONTB = find_font(True)



def font(size, bold=False):
    return ImageFont.truetype(FONTB if bold else FONT, size)



def save(img, rel, **kw):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if rel.endswith(".jpg"):
        img.convert("RGB").save(path, quality=kw.get("quality", 85), optimize=True)
    else:
        img.save(path, optimize=True)


rnd = random.Random(42)


def gradient(w, h, top, bottom):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3)))
    return img



def noise_tex(base, var, size=256, seed=0):
    r = np.random.default_rng(seed)
    n = r.integers(-var, var + 1, size=(size, size, 1))
    arr = np.clip(np.array(base, dtype=np.int32)[None, None, :] + n, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB")



def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)



def tiles(base, line, n, size=256, bevel=True, seed=0):
    img = noise_tex(base, 8, size, seed)
    d = ImageDraw.Draw(img)
    step = size // n
    for i in range(n + 1):
        d.line([(i * step, 0), (i * step, size)], fill=line, width=3)
        d.line([(0, i * step), (size, i * step)], fill=line, width=3)
    if bevel:
        hi = shade(base, 1.15)
        for i in range(n):
            for j in range(n):
                x, y = i * step, j * step
                d.line([(x + 3, y + 3), (x + step - 3, y + 3)], fill=hi)
                d.line([(x + 3, y + 3), (x + 3, y + step - 3)], fill=hi)
    return img



def pixel_tex(kind, seed=5):
    """Textures façon voxels (16x16 agrandies) : herbe, terre, pierre, bois, feuilles."""
    rr = random.Random(seed)
    pal = {
        "grass": [(86, 160, 60), (70, 140, 50), (100, 176, 70), (60, 120, 44)],
        "dirt": [(130, 90, 60), (110, 76, 50), (146, 104, 70), (96, 66, 44)],
        "stone": [(128, 128, 128), (110, 110, 112), (146, 146, 146), (96, 96, 98)],
        "log": [(110, 80, 50), (90, 64, 40), (126, 92, 58)],
        "leaves": [(50, 120, 40), (40, 100, 34), (70, 140, 56), (30, 80, 28)],
    }[kind]
    small = Image.new("RGB", (16, 16))
    px = small.load()
    for y in range(16):
        for x in range(16):
            px[x, y] = rr.choice(pal)
    if kind == "log":
        for y in range(16):
            for x in (3, 8, 12):
                px[x, y] = (70, 50, 30)
    return small.resize((256, 256), Image.NEAREST)



def grass_side():
    img = pixel_tex("dirt", 6)
    top = pixel_tex("grass", 7).crop((0, 0, 256, 64))
    img.paste(top, (0, 0))
    return img



def ubuntu_wall():
    img = gradient(256, 256, (119, 41, 83), (44, 0, 30))
    d = ImageDraw.Draw(img)
    for i, (x, y) in enumerate([(60, 70), (190, 150), (120, 210)]):
        d.ellipse([x - 22, y - 22, x + 22, y + 22], outline=(233, 84, 32), width=6)
        for a in range(3):
            ang = a * 2.094 + 0.5
            cx, cy = x + 26 * math.cos(ang), y + 26 * math.sin(ang)
            d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=(233, 84, 32))
    d.rectangle([0, 220, 255, 230], fill=(233, 84, 32))
    return img



def snow(seed=13):
    img = noise_tex((236, 242, 250), 10, seed=seed).filter(ImageFilter.GaussianBlur(1.5))
    return img



def ice_wall():
    img = noise_tex((170, 210, 236), 10, seed=14)
    d = ImageDraw.Draw(img)
    rr = random.Random(14)
    for _ in range(14):
        x, y = rr.randint(0, 255), rr.randint(0, 255)
        d.line([(x, y), (x + rr.randint(-50, 50), y + rr.randint(-50, 50))], fill=(235, 248, 255), width=2)
    return img.filter(ImageFilter.GaussianBlur(0.7))



def panel_images():
    W, H = 512, 256
    for name, (accent, title, lines) in PANELS.items():
        img = Image.new("RGB", (W, H), (14, 20, 30))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, W - 1, H - 1], outline=accent, width=8)
        d.rectangle([8, 8, W - 9, 58], fill=tuple(int(c * 0.35) for c in accent))
        size = 34
        while size > 18 and d.textlength(title, font=font(size, True)) > W - 40:
            size -= 2
        d.text((W // 2, 34), title, font=font(size, True), fill=accent, anchor="mm")
        y = 76
        fsize = 22
        f = font(fsize)
        for line in lines:
            while d.textlength(line, font=f) > W - 44 and fsize > 14:
                fsize -= 1
                f = font(fsize)
        for line in lines:
            d.text((24, y), line, font=f, fill=(232, 236, 242))
            y += fsize + 12
        save(img, "packages/pf/%s.jpg" % name, quality=90)


def books():
    """Bibliothèque : étagères tous les 8 unités (64 px), dos de livres colorés."""
    rr = random.Random(21)
    img = noise_tex((70, 46, 28), 6, 256, 21)
    d = ImageDraw.Draw(img)
    pal = [(150, 40, 36), (40, 70, 130), (36, 110, 60), (170, 130, 50), (90, 50, 110), (190, 180, 160),
           (120, 70, 40), (30, 30, 34), (60, 120, 130), (160, 80, 30)]
    for row in range(4):
        y0 = row * 64
        d.rectangle([0, y0 + 56, 255, y0 + 63], fill=(96, 64, 38))          # planche
        d.line([(0, y0 + 56), (255, y0 + 56)], fill=(130, 92, 58), width=2)
        x = 2
        while x < 250:
            w = rr.randint(7, 15)
            h = rr.randint(36, 52)
            c = rr.choice(pal)
            if rr.random() < 0.08:                                            # livre penché / vide
                x += w
                continue
            d.rectangle([x, y0 + 56 - h, x + w - 2, y0 + 55], fill=c)
            d.line([(x + 1, y0 + 60 - h), (x + w - 3, y0 + 60 - h)], fill=shade(c, 1.5), width=2)
            d.line([(x + 1, y0 + 48), (x + w - 3, y0 + 48)], fill=shade(c, 1.5), width=2)
            d.line([(x + w - 2, y0 + 56 - h), (x + w - 2, y0 + 55)], fill=shade(c, 0.5))
            x += w
    return img


def rack():
    """Baie de serveurs : unités 2U (32 px = 2 unités) avec voyants et grilles."""
    rr = random.Random(7)
    img = Image.new("RGB", (256, 256), (22, 24, 28))
    d = ImageDraw.Draw(img)
    for row in range(8):
        y0 = row * 32
        d.rectangle([6, y0 + 2, 249, y0 + 29], fill=(44, 47, 54), outline=(70, 74, 82))
        for gx in range(40, 200, 6):                                            # grille d'aération
            d.line([(gx, y0 + 8), (gx, y0 + 23)], fill=(28, 30, 34), width=2)
        for k in range(rr.randint(2, 5)):
            c = rr.choice([(60, 255, 120), (60, 255, 120), (80, 160, 255), (255, 180, 40)])
            d.ellipse([212 + k * 8, y0 + 12, 217 + k * 8, y0 + 17], fill=c)
        d.rectangle([12, y0 + 9, 30, y0 + 21], fill=(120, 124, 130))           # poignée
    d.rectangle([0, 0, 5, 255], fill=(90, 94, 100))
    d.rectangle([250, 0, 255, 255], fill=(90, 94, 100))
    return img


def screen():
    """Écran allumé : code coloré sur fond sombre."""
    rr = random.Random(3)
    img = gradient(256, 256, (18, 30, 56), (10, 16, 32))
    d = ImageDraw.Draw(img)
    for i in range(16):
        y = 10 + i * 15
        x = 12 + rr.randint(0, 3) * 14
        while x < 230 and rr.random() < 0.85:
            w = rr.randint(14, 54)
            d.rectangle([x, y, min(244, x + w), y + 6],
                        fill=rr.choice([(120, 200, 255), (250, 200, 90), (130, 230, 140), (230, 120, 200), (200, 210, 225)]))
            x += w + 8
    return img


def pigeonholes():
    """Casiers de tri postal : grille 4 x 4 en bois avec lettres."""
    rr = random.Random(11)
    img = Image.new("RGB", (256, 256), (110, 76, 44))
    d = ImageDraw.Draw(img)
    for j in range(4):
        for i in range(4):
            x0, y0 = i * 64 + 6, j * 64 + 6
            d.rectangle([x0, y0, x0 + 51, y0 + 51], fill=(40, 28, 18))
            for k in range(rr.randint(0, 3)):
                c = rr.choice([(235, 230, 215), (220, 200, 160), (250, 250, 245), (200, 220, 240)])
                yy = y0 + 51 - 8 - k * 9
                d.rectangle([x0 + 4 + k * 2, yy, x0 + 47, yy + 7], fill=c)
    return img


def map_textures():
    T = {
        # Mobilier en géométrie (aucune texture équivalente dans le jeu de base)
        "books": books(),
        "rack": rack(),
        "screen": screen(),
        "pigeonholes": pigeonholes(),
        # Mineport : blocs façon voxels (aucun équivalent dans le jeu de base)
        "floor_grass": pixel_tex("grass", 30),
        "wall_dirt": grass_side(),
        "wall_stone": pixel_tex("stone", 31),
        # Portfolio OS : fond d'écran du bureau (visuel propre au projet)
        "wall_ubuntu": ubuntu_wall(),
        # Tux World : banquise (pas de neige / glace dans les textures de base)
        "floor_snow": snow(),
        "wall_ice": ice_wall(),
    }
    for name, img in T.items():
        save(img, "packages/pf/%s.jpg" % name)
    # vignette de chargement de la carte
    shot = gradient(256, 256, (40, 60, 96), (10, 14, 24))
    d = ImageDraw.Draw(shot)
    d.text((128, 110), "PORTFOLIO", font=font(34, True), fill=(255, 196, 64), anchor="mm")
    d.text((128, 150), "visite de Jules ROGUE", font=font(16), fill=(220, 230, 240), anchor="mm")
    save(shot, "packages/base/portfolio.jpg")


if __name__ == "__main__":
    map_textures()
    panel_images()
    print("assets maison générés dans", OUT)
