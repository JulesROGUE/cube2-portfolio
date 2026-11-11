#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère tous les visuels du client (aucun asset tiers sous licence restrictive) :

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

# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------


def gradient(w, h, top, bottom):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3)))
    return img


def ui_images():
    bg = gradient(256, 256, (16, 28, 44), (6, 10, 18))
    d = ImageDraw.Draw(bg)
    for i in range(0, 256, 32):
        d.line([(i, 0), (i, 256)], fill=(30, 50, 76))
        d.line([(0, i), (256, i)], fill=(30, 50, 76))
    save(bg, "data/background.png")
    save(Image.new("RGBA", (256, 256), (0, 0, 0, 0)), "data/background_decal.png")
    det = Image.new("L", (256, 256), 128)
    save(det.convert("RGB"), "data/background_detail.png")

    # Logo
    logo = Image.new("RGBA", (512, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(logo)
    d.text((256, 100), "PORTFOLIO", font=font(72, True), fill=(255, 196, 64, 255), anchor="mm")
    d.text((256, 170), "Jules ROGUE - Cube 2 web", font=font(30), fill=(220, 230, 240, 255), anchor="mm")
    save(logo, "data/logo.png")
    # vignette de chargement de la carte (mapshot)
    shot = gradient(256, 256, (40, 60, 96), (10, 14, 24))
    ds = ImageDraw.Draw(shot)
    ds.text((128, 110), "PORTFOLIO", font=font(34, True), fill=(255, 196, 64), anchor="mm")
    ds.text((128, 150), "visite de Jules ROGUE", font=font(16), fill=(220, 230, 240), anchor="mm")
    save(shot, "packages/base/portfolio.jpg")
    save(logo.resize((1024, 512)), "data/logo_1024.png")

    # Réticule (blanc, teinté par le moteur)
    for name, col in (("crosshair", 255), ("teammate", 255), ("hit", 255)):
        c = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(c)
        d.ellipse([28, 28, 36, 36], fill=(col, col, col, 230))
        if name == "hit":
            for a, b in (((16, 16), (24, 24)), ((40, 40), (48, 48)), ((16, 48), (24, 40)), ((40, 24), (48, 16))):
                d.line([a, b], fill=(255, 255, 255, 230), width=3)
        save(c, "data/%s.png" % name)

    cur = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(cur)
    d.polygon([(0, 0), (0, 24), (7, 18), (12, 28), (16, 26), (11, 16), (20, 16)], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
    save(cur, "data/guicursor.png")

    # Skin des menus : aplat sombre uniforme (la découpe en tuiles du moteur
    # reste donc homogène) ; remplace guiskin/guioverlay (CC BY-NC-SA d'origine).
    save(Image.new("RGBA", (256, 128), (14, 24, 38, 235)), "data/guiskin.png")
    save(Image.new("RGBA", (256, 256), (64, 140, 220, 90)), "data/guioverlay.png")
    sl = Image.new("RGBA", (16, 64), (0, 0, 0, 0))
    ImageDraw.Draw(sl).rectangle([4, 0, 11, 63], fill=(120, 180, 240, 220))
    save(sl, "data/guislider.png")

    bar = Image.new("RGBA", (512, 64), (0, 0, 0, 0))
    ImageDraw.Draw(bar).rectangle([0, 16, 511, 47], fill=(64, 160, 255, 255))
    save(bar, "data/loading_bar.png")
    frame = Image.new("RGBA", (512, 256), (0, 0, 0, 0))
    ImageDraw.Draw(frame).rectangle([0, 96, 511, 159], outline=(200, 220, 240, 255), width=4)
    save(frame, "data/loading_frame.png")
    mf = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    ImageDraw.Draw(mf).rectangle([0, 0, 255, 255], outline=(200, 220, 240, 255), width=6)
    save(mf, "data/mapshot_frame.png")

    # HUD / particules minimales attendues par le moteur
    save(Image.new("RGBA", (256, 256), (0, 0, 0, 0)), "packages/hud/items.png")
    save(Image.new("RGBA", (64, 64), (255, 0, 0, 0)), "packages/hud/damage.png")
    for b in ("blip_blue_alive", "blip_blue_dead", "blip_red_alive", "blip_red_dead"):
        save(Image.new("RGBA", (16, 16), (0, 0, 0, 0)), "packages/hud/%s.png" % b)
    soft = Image.new("L", (64, 64), 0)
    ImageDraw.Draw(soft).ellipse([8, 8, 56, 56], fill=255)
    soft = soft.filter(ImageFilter.GaussianBlur(6))
    rgba = Image.merge("RGBA", (soft, soft, soft, soft))
    for p in ("ball1", "ball2", "ball3", "base", "spark"):
        save(rgba, "packages/particles/%s.png" % p)
    for p in ("flare", "muzzleflash1", "muzzleflash2", "muzzleflash3", "lightning"):
        save(Image.merge("RGB", (soft, soft, soft)), "packages/particles/%s.jpg" % p)
    # boules de feu des explosions (roquettes, grenades) : dégradé radial chaud / bleu
    for name, cols in (("explosion", ((255, 240, 180), (255, 120, 20), (90, 20, 0))),
                       ("plasma", ((220, 240, 255), (60, 140, 255), (10, 20, 90)))):
        ex = Image.new("RGB", (128, 128))
        px = ex.load()
        rr = random.Random(name)
        for y in range(128):
            for x in range(128):
                t = min(1.0, (abs(x - 64) + abs(y - 64) * 0.7) / 90 + rr.uniform(0, 0.15))
                a, b = (cols[0], cols[1]) if t < 0.5 else (cols[1], cols[2])
                k = (t * 2) % 1.0 if t < 1 else 1.0
                px[x, y] = tuple(int(a[i] * (1 - k) + b[i] * k) for i in range(3))
        save(ex, "packages/particles/%s.png" % name)
    save(rgba, "packages/particles/lensflares.png")
    # particules « <grey> » (teintées par le moteur) : fumée, flammes, impacts, neige...
    rr = random.Random(99)
    def splat(n, blur, size=64):
        im = Image.new("L", (size, size), 0)
        dd = ImageDraw.Draw(im)
        for _ in range(n):
            r = rr.randint(size // 10, size // 4)
            x, y = rr.randint(size // 4, 3 * size // 4), rr.randint(size // 4, 3 * size // 4)
            dd.ellipse([x - r, y - r, x + r, y + r], fill=rr.randint(160, 255))
        return im.filter(ImageFilter.GaussianBlur(blur))
    def white_alpha(a):
        w = Image.new("L", a.size, 255)
        return Image.merge("RGBA", (w, w, w, a))
    for name, img in (("smoke", splat(12, 6)), ("steam", splat(10, 7)), ("flames", splat(8, 3)),
                      ("blob", soft), ("snow", soft.resize((32, 32)))):
        save(white_alpha(img), "packages/particles/%s.png" % name)
    # décalcomanies (modulation inverse : clair = marque sombre)
    for name, img in (("blood", splat(6, 1.5)), ("scorch", splat(14, 4, 128)), ("bullet", soft.resize((32, 32)))):
        save(img, "packages/particles/%s.png" % name)

    nt = Image.new("RGB", (64, 64), (255, 0, 255))
    d = ImageDraw.Draw(nt)
    d.rectangle([0, 0, 31, 31], fill=(40, 40, 40))
    d.rectangle([32, 32, 63, 63], fill=(40, 40, 40))
    save(nt, "packages/textures/notexture.png")
    save(nt, "packages/textures/downloading.png")

# ---------------------------------------------------------------------------
# Icônes du HUD d'origine (packages/hud/items.png : grille 4x4)
# ---------------------------------------------------------------------------


def hud_icons():
    S = 128
    img = Image.new("RGBA", (S * 4, S * 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def cell(i):
        return (i % 4) * S, (i // 4) * S

    def shield(i, col):
        x, y = cell(i)
        d.polygon([(x + 24, y + 20), (x + 104, y + 20), (x + 104, y + 64), (x + 64, y + 112), (x + 24, y + 64)],
                  fill=col, outline=(20, 20, 20), width=5)
    shield(0, (70, 120, 255))
    shield(1, (80, 210, 90))
    shield(2, (240, 210, 60))
    x, y = cell(3)  # santé : croix
    d.rectangle([x + 48, y + 16, x + 80, y + 112], fill=(240, 60, 60), outline=(255, 255, 255), width=4)
    d.rectangle([x + 16, y + 48, x + 112, y + 80], fill=(240, 60, 60), outline=(255, 255, 255), width=4)
    d.rectangle([x + 50, y + 50, x + 78, y + 78], fill=(240, 60, 60))
    guns = {4: "SCIE", 5: "FUSIL", 6: "MITRA", 7: "ROQ.", 8: "PRÉC.", 9: "GREN.", 10: "PISTO"}
    for i, label in guns.items():
        x, y = cell(i)
        d.rounded_rectangle([x + 10, y + 34, x + 118, y + 94], radius=14, fill=(40, 52, 70), outline=(255, 192, 64), width=5)
        d.text((x + 64, y + 64), label, font=font(24, True), fill=(255, 230, 180), anchor="mm")
    x, y = cell(11)
    d.ellipse([x + 20, y + 20, x + 108, y + 108], fill=(150, 80, 255), outline=(255, 255, 255), width=5)
    d.text((x + 64, y + 64), "x4", font=font(40, True), fill=(255, 255, 255), anchor="mm")
    for i, col in ((12, (230, 60, 60)), (13, (60, 110, 240)), (14, (200, 200, 200))):
        x, y = cell(i)
        d.line([(x + 34, y + 16), (x + 34, y + 114)], fill=(230, 230, 230), width=8)
        d.polygon([(x + 38, y + 18), (x + 108, y + 40), (x + 38, y + 64)], fill=col)
    x, y = cell(15)
    d.ellipse([x + 30, y + 30, x + 98, y + 98], fill=(255, 210, 60), outline=(120, 80, 0), width=6)
    save(img, "packages/hud/items.png")

# ---------------------------------------------------------------------------
# Textures thématiques de la carte (256 px, scale 2 -> 64 unités du monde)
# ---------------------------------------------------------------------------


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


def wood(base, seed=1):
    rr = random.Random(seed)
    img = Image.new("RGB", (256, 256), base)
    d = ImageDraw.Draw(img)
    for i in range(8):
        y = i * 32
        col = shade(base, 1 + rr.uniform(-0.12, 0.12))
        d.rectangle([0, y, 255, y + 31], fill=col)
        for k in range(6):
            yy = y + rr.randint(4, 28)
            d.line([(0, yy), (255, yy)], fill=shade(col, 0.9))
        off = rr.randint(0, 255)
        d.line([(off, y), (off, y + 31)], fill=shade(base, 0.7), width=2)
        d.line([(0, y), (255, y)], fill=shade(base, 0.65), width=2)
    return img


def bookshelf_tex(seed=2):
    rr = random.Random(seed)
    img = Image.new("RGB", (256, 256), (70, 44, 26))
    d = ImageDraw.Draw(img)
    cols = [(150, 40, 40), (40, 80, 140), (40, 120, 70), (190, 150, 60), (110, 60, 130), (200, 200, 190), (30, 30, 30)]
    for row in range(4):
        y0 = row * 64 + 6
        x = 4
        while x < 250:
            w = rr.randint(7, 16)
            h = rr.randint(40, 54)
            c = rr.choice(cols)
            d.rectangle([x, y0 + 54 - h, x + w - 1, y0 + 54], fill=c)
            d.line([(x + 2, y0 + 58 - h), (x + w - 3, y0 + 58 - h)], fill=shade(c, 1.4))
            x += w + rr.randint(0, 2)
        d.rectangle([0, y0 + 55, 255, y0 + 63], fill=(96, 62, 36))
    return img


def server_wall(seed=3):
    rr = random.Random(seed)
    img = noise_tex((26, 32, 40), 4, seed=seed)
    d = ImageDraw.Draw(img)
    for k in range(18):  # pistes de circuit
        x, y = rr.randint(0, 255), rr.randint(0, 255)
        for _ in range(4):
            nx = x + rr.choice([-60, -30, 30, 60])
            d.line([(x, y), (nx, y)], fill=(30, 140, 120), width=2)
            ny = y + rr.choice([-40, 40])
            d.line([(nx, y), (nx, ny)], fill=(30, 140, 120), width=2)
            d.ellipse([nx - 3, ny - 3, nx + 3, ny + 3], fill=(60, 220, 180))
            x, y = nx, ny
    d.rectangle([0, 220, 255, 230], fill=(40, 150, 255))
    return img


def grating():
    img = Image.new("RGB", (256, 256), (60, 66, 74))
    d = ImageDraw.Draw(img)
    for i in range(0, 256, 16):
        d.line([(i, 0), (i, 256)], fill=(30, 34, 40), width=5)
        d.line([(0, i), (256, i)], fill=(90, 98, 108), width=2)
    return img


def concrete(base=(150, 150, 146), seed=4, stains=0, lines=False):
    img = noise_tex(base, 14, seed=seed).filter(ImageFilter.GaussianBlur(1.2))
    d = ImageDraw.Draw(img)
    rr = random.Random(seed)
    for _ in range(stains):
        x, y, r = rr.randint(0, 255), rr.randint(0, 255), rr.randint(10, 30)
        d.ellipse([x - r, y - r, x + r, y + r // 2], fill=shade(base, 0.55))
    if lines:
        d.rectangle([0, 120, 255, 136], fill=(230, 200, 40))
    return img


def corrugated(base):
    img = Image.new("RGB", (256, 256), base)
    d = ImageDraw.Draw(img)
    for x in range(0, 256, 16):
        d.rectangle([x, 0, x + 7, 255], fill=shade(base, 1.15))
        d.line([(x + 8, 0), (x + 8, 255)], fill=shade(base, 0.7), width=2)
    for y in range(0, 256, 128):
        d.line([(0, y), (256, y)], fill=shade(base, 0.5), width=3)
    return img


def neon(base, colors, n=4):
    img = Image.new("RGB", (256, 256), base)
    glow = Image.new("RGB", (256, 256), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    step = 256 // n
    for i in range(n + 1):
        c = colors[i % len(colors)]
        g.line([(i * step, 0), (i * step, 256)], fill=c, width=6)
        g.line([(0, i * step), (256, i * step)], fill=colors[(i + 1) % len(colors)], width=6)
    blur = glow.filter(ImageFilter.GaussianBlur(5))
    out = Image.fromarray(np.clip(np.array(img, np.int32) + np.array(blur, np.int32) + np.array(glow, np.int32) // 2, 0, 255).astype(np.uint8))
    return out


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


def hazard_floor():
    img = tiles((84, 88, 96), (50, 52, 58), 2, seed=8)
    d = ImageDraw.Draw(img)
    for k in range(-256, 512, 40):
        d.polygon([(k, 0), (k + 20, 0), (k + 20 - 32, 32), (k - 32, 32)], fill=(230, 190, 30))
        d.polygon([(k + 20, 0), (k + 40, 0), (k + 40 - 32, 32), (k - 12, 32)], fill=(30, 30, 30))
    return img


def arena_wall():
    img = tiles((54, 58, 66), (30, 32, 36), 2, seed=9)
    d = ImageDraw.Draw(img)
    for x in (64, 192):
        d.rectangle([x - 6, 40, x + 6, 90], fill=(255, 60, 40))
    d.rectangle([0, 220, 255, 230], fill=(255, 80, 40))
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


def carpet(base, seed=10):
    return noise_tex(base, 18, seed=seed).filter(ImageFilter.GaussianBlur(0.8))


def marble(base, vein, seed=11):
    rr = random.Random(seed)
    img = noise_tex(base, 6, seed=seed)
    d = ImageDraw.Draw(img)
    for _ in range(9):
        x, y = rr.randint(0, 255), 0
        pts = [(x, y)]
        while y < 256:
            x += rr.randint(-14, 14)
            y += rr.randint(10, 26)
            pts.append((x, y))
        d.line(pts, fill=vein, width=2)
    return img.filter(ImageFilter.GaussianBlur(0.6))


def gold_wall():
    img = marble((236, 230, 214), (200, 190, 170), seed=12)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 255, 255], outline=(200, 160, 50), width=6)
    d.rectangle([0, 214, 255, 232], fill=(214, 172, 56))
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


def post_wall():
    img = noise_tex((246, 206, 60), 6, seed=15)
    d = ImageDraw.Draw(img)
    for (x, y) in [(40, 40), (168, 104), (72, 168)]:
        d.rectangle([x, y, x + 56, y + 36], fill=(250, 250, 245), outline=(30, 70, 150), width=3)
        d.line([(x, y), (x + 28, y + 20), (x + 56, y)], fill=(30, 70, 150), width=3)
    d.rectangle([0, 220, 255, 232], fill=(30, 70, 150))
    return img


def gallery_wall():
    img = noise_tex((226, 224, 218), 4, seed=16)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 224, 255, 255], fill=(60, 60, 64))
    return img


def map_textures():
    T = {
        "sky": gradient(64, 64, (40, 70, 110), (10, 20, 35)),
        "ceiling": tiles((60, 64, 72), (40, 42, 48), 2, bevel=False, seed=20),
        "ceiling_wood": wood((96, 66, 40), seed=21),
        # Hall
        "floor_hall": marble((200, 200, 206), (150, 150, 160), seed=22),
        "wall_hall": tiles((112, 116, 124), (80, 84, 92), 2, seed=23),
        # Profil : bibliothèque
        "floor_wood": wood((140, 96, 58)),
        "wall_books": bookshelf_tex(),
        # Compétences : salle serveur
        "floor_grate": grating(),
        "wall_server": server_wall(),
        # Galerie
        "floor_concrete": concrete(),
        "wall_gallery": gallery_wall(),
        # Leboncoin : garage
        "floor_garage": concrete((120, 120, 118), seed=24, stains=6, lines=True),
        "wall_garage": corrugated((200, 110, 40)),
        # Magic Shape : salle rythmique néon
        "floor_neon": neon((10, 6, 20), [(255, 40, 200), (40, 220, 255)], 4),
        "wall_neon": neon((24, 10, 40), [(180, 60, 255), (255, 60, 150)], 2),
        # Mineport : voxels
        "floor_grass": pixel_tex("grass", 30),
        "wall_dirt": grass_side(),
        "wall_stone": pixel_tex("stone", 31),
        # Cube 2 : arène
        "floor_arena": hazard_floor(),
        "wall_arena": arena_wall(),
        # Portfolio OS : bureau Ubuntu géant
        "floor_carpet": carpet((70, 70, 76)),
        "wall_ubuntu": ubuntu_wall(),
        # Certificats : salle des trophées
        "floor_redcarpet": carpet((150, 20, 30), seed=32),
        "wall_gold": gold_wall(),
        # Tux World : banquise
        "floor_snow": snow(),
        "wall_ice": ice_wall(),
        # Contact : bureau de poste
        "floor_post": tiles((220, 220, 220), (60, 60, 70), 4, seed=33),
        "wall_post": post_wall(),
    }
    for name, img in T.items():
        save(img, "packages/pf/%s.jpg" % name)


# ---------------------------------------------------------------------------
# Panneaux à texte (512x256, couvrent 128x64 unités sur un mur)
# ---------------------------------------------------------------------------


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


if __name__ == "__main__":
    ui_images()
    hud_icons()
    map_textures()
    panel_images()
    import gen_models
    gen_models.main(OUT)
    print("assets générés dans", OUT)
