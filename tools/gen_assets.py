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
    for p in ("flare", "muzzleflash1", "muzzleflash2", "muzzleflash3"):
        save(Image.merge("RGB", (soft, soft, soft)), "packages/particles/%s.jpg" % p)

    nt = Image.new("RGB", (64, 64), (255, 0, 255))
    d = ImageDraw.Draw(nt)
    d.rectangle([0, 0, 31, 31], fill=(40, 40, 40))
    d.rectangle([32, 32, 63, 63], fill=(40, 40, 40))
    save(nt, "packages/textures/notexture.png")
    save(nt, "packages/textures/downloading.png")

# ---------------------------------------------------------------------------
# Textures de la carte (256 px, scale 2 -> 64 unités)
# ---------------------------------------------------------------------------


def noise_tex(base, var, size=256):
    img = Image.new("RGB", (size, size), base)
    px = img.load()
    for y in range(size):
        for x in range(size):
            n = rnd.randint(-var, var)
            px[x, y] = tuple(max(0, min(255, base[i] + n)) for i in range(3))
    return img


def tiles(base, line, n, size=256, bevel=True):
    img = noise_tex(base, 8, size)
    d = ImageDraw.Draw(img)
    step = size // n
    for i in range(n + 1):
        d.line([(i * step, 0), (i * step, size)], fill=line, width=3)
        d.line([(0, i * step), (size, i * step)], fill=line, width=3)
    if bevel:
        for i in range(n):
            for j in range(n):
                x, y = i * step, j * step
                d.line([(x + 3, y + 3), (x + step - 3, y + 3)], fill=tuple(min(255, c + 25) for c in base))
                d.line([(x + 3, y + 3), (x + 3, y + step - 3)], fill=tuple(min(255, c + 25) for c in base))
    return img


def wood(base):
    img = Image.new("RGB", (256, 256), base)
    d = ImageDraw.Draw(img)
    for i in range(8):
        y = i * 32
        shade = rnd.randint(-18, 18)
        col = tuple(max(0, min(255, c + shade)) for c in base)
        d.rectangle([0, y, 255, y + 31], fill=col)
        for k in range(6):
            yy = y + rnd.randint(4, 28)
            d.line([(0, yy), (255, yy)], fill=tuple(max(0, c - 14) for c in col))
        off = rnd.randint(0, 255)
        d.line([(off, y), (off, y + 31)], fill=tuple(max(0, c - 40) for c in base), width=2)
        d.line([(0, y), (255, y)], fill=tuple(max(0, c - 45) for c in base), width=2)
    return img


def panelwall(base, accent):
    img = noise_tex(base, 6)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 255, 255], outline=tuple(max(0, c - 30) for c in base), width=4)
    d.rectangle([0, 220, 255, 232], fill=accent)
    d.line([(128, 0), (128, 220)], fill=tuple(max(0, c - 18) for c in base), width=2)
    return img


def map_textures():
    save(gradient(64, 64, (40, 70, 110), (10, 20, 35)), "packages/pf/sky.jpg")
    save(tiles((150, 150, 158), (90, 90, 98), 4), "packages/pf/floor_hall.jpg")
    save(wood((140, 96, 58)), "packages/pf/floor_wood.jpg")
    save(tiles((200, 200, 205), (140, 140, 150), 8), "packages/pf/floor_tile.jpg")
    save(tiles((214, 236, 250), (170, 205, 230), 2), "packages/pf/floor_ice.jpg")
    save(tiles((44, 48, 58), (24, 26, 32), 4), "packages/pf/floor_dark.jpg")
    walls = {
        "wall_grey": ((112, 116, 124), (255, 192, 64)),
        "wall_blue": ((70, 98, 140), (64, 176, 255)),
        "wall_green": ((70, 120, 90), (90, 220, 130)),
        "wall_orange": ((150, 100, 64), (255, 140, 60)),
        "wall_purple": ((104, 80, 140), (190, 110, 255)),
        "wall_ice": ((170, 200, 225), (240, 250, 255)),
        "wall_gold": ((140, 120, 70), (240, 200, 70)),
        "wall_teal": ((50, 120, 125), (96, 255, 200)),
        "wall_red": ((130, 60, 60), (240, 90, 90)),
    }
    for name, (base, acc) in walls.items():
        save(panelwall(base, acc), "packages/pf/%s.jpg" % name)
    save(tiles((60, 64, 72), (40, 42, 48), 2, bevel=False), "packages/pf/ceiling.jpg")


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


# ---------------------------------------------------------------------------
# Avatar des joueurs : petit robot en boîtes (OBJ, Y vers le haut)
# ---------------------------------------------------------------------------

# Palette de la skin (64x64, cases de 16 px)
PALETTE = {
    "body": (0, (60, 140, 230)),
    "dark": (1, (30, 40, 60)),
    "visor": (2, (120, 255, 220)),
    "light": (3, (235, 240, 245)),
    "accent": (4, (255, 192, 64)),
}


def avatar():
    skin = Image.new("RGB", (64, 64), (128, 128, 128))
    d = ImageDraw.Draw(skin)
    for _, (i, col) in PALETTE.items():
        x, y = (i % 4) * 16, (i // 4) * 16
        d.rectangle([x, y, x + 15, y + 15], fill=col)
    save(skin, "packages/models/pfavatar/skin.png")
    for team, col in (("blue", (60, 120, 255)), ("red", (230, 70, 70))):
        s2 = skin.copy()
        ImageDraw.Draw(s2).rectangle([0, 0, 15, 15], fill=col)
        save(s2, "packages/models/pfavatar/%s/skin.png" % team)

    verts, uvs, faces = [], [], []

    def uv_of(part):
        i = PALETTE[part][0]
        u = ((i % 4) * 16 + 8) / 64.0
        v = 1.0 - ((i // 4) * 16 + 8) / 64.0
        uvs.append((u, v))
        return len(uvs)

    def box(x0, x1, y0, y1, z0, z1, part, front=None):
        """Boîte en coordonnées OBJ (x droite, y haut, z avant)."""
        base = len(verts)
        for (x, y, z) in [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                          (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]:
            verts.append((x, y, z))
        quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (3, 7, 6, 2), (0, 4, 7, 3), (1, 2, 6, 5)]
        for qi, q in enumerate(quads):
            p = front if (front and qi == 1) else part
            t = uv_of(p)
            faces.append([(base + k + 1, t) for k in q])

    # Le joueur mesure ~15 unités, pieds en y=0, regard vers +z
    box(-2.6, -0.6, 0, 6, -1.2, 1.2, "dark")          # jambes
    box(0.6, 2.6, 0, 6, -1.2, 1.2, "dark")
    box(-3.4, 3.4, 6, 11.5, -2, 2, "body", "accent")  # torse
    box(-4.6, -3.4, 6.5, 11, -1, 1, "light")           # bras
    box(3.4, 4.6, 6.5, 11, -1, 1, "light")
    box(-2.6, 2.6, 11.5, 16, -2.4, 2.4, "light", "visor")  # tête + visière
    box(-0.3, 0.3, 16, 18, -0.3, 0.3, "accent")         # antenne

    lines = ["# Avatar du visiteur - généré par tools/gen_assets.py (domaine public)"]
    lines += ["v %.3f %.3f %.3f" % v for v in verts]
    lines += ["vt %.4f %.4f" % t for t in uvs]
    lines += ["f " + " ".join("%d/%d" % (vi, ti) for vi, ti in f) for f in faces]
    path = os.path.join(OUT, "packages/models/pfavatar/tris.obj")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    # Le modèle regarde vers +z en OBJ ; on l'oriente comme les modèles de Cube 2.
    with open(os.path.join(OUT, "packages/models/pfavatar/obj.cfg"), "w") as fh:
        fh.write('objload "tris.obj"\nobjskin * "skin.png"\nmdlyaw 0\nmdlspec 0\nmdlambient 40\n')


if __name__ == "__main__":
    ui_images()
    map_textures()
    panel_images()
    avatar()
    print("assets générés dans", OUT)
