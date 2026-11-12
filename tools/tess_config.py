#!/usr/bin/env python3
"""Scripts de jeu pour le portage Tesseract (branche tesseract).

Assemble, dans <fs>/config/, à partir des scripts d'origine de Sauerbraten et de
game/data/portfolio.cfg :
  - default.cfg : touches de Sauerbraten (noms de touches de Tesseract), sans éditeur ;
  - game.cfg    : sons du jeu (ordre d'origine), réglages du jeu, portfolio.cfg ;
  - sound.cfg   : vide (les sons sont ceux de Sauerbraten, enregistrés par game.cfg).
Les menus (newgui, propres à Sauerbraten) sont retirés : l'interface est celle de
config/ui.cfg (système d'interface de Tesseract).
"""
import re
import sys

sauerdata, portfolio, out = sys.argv[1], sys.argv[2], sys.argv[3]
KEYS = {"MOUSE1": "MOUSELEFT", "MOUSE2": "MOUSERIGHT", "MOUSE3": "MOUSEMIDDLE",
        "MOUSE4": "MOUSEWHEELUP", "MOUSE5": "MOUSEWHEELDOWN"}


def strip_blocks(text, starters):
    """Retire les blocs « starter nom [ ... ] » (crochets imbriqués)."""
    out, i = [], 0
    pat = re.compile(r"^(?:%s)\b[^\[\n]*\[" % "|".join(starters), re.M)
    while True:
        m = pat.search(text, i)
        if not m:
            out.append(text[i:])
            return "".join(out)
        out.append(text[i:m.start()])
        depth, j = 1, m.end()
        while j < len(text) and depth:
            if text[j] == "[":
                depth += 1
            elif text[j] == "]":
                depth -= 1
            j += 1
        # fin de ligne éventuelle (arguments après le bloc)
        k = text.find("\n", j)
        i = len(text) if k < 0 else k + 1


def rename_keys(line):
    for a, b in KEYS.items():
        line = re.sub(r"\b%s\b" % a, b, line)
    return line


# --- default.cfg : touches ---------------------------------------------------
lines = ["// default.cfg (Tesseract) - touches de Sauerbraten pour la visite (généré par tools/tess_config.py)"]
for l in open(f"{sauerdata}/defaults.cfg", encoding="latin-1"):
    l = l.rstrip("\n")
    w = l.split()
    if w and w[0] in ("editbind", "editbindmod", "editbindvar"):
        continue
    if w and w[0] in ("bind", "specbind", "bindvar", "bindvarquiet") and len(w) > 2 and "edit" in l and "editing" not in l:
        continue
    lines.append(rename_keys(l))
lines.append('bind ESCAPE [togglemainmenu]')
open(f"{out}/default.cfg", "w", encoding="utf-8").write("\n".join(lines) + "\n")

# --- game.cfg : sons, réglages du jeu, visite ------------------------------------
game = ["// game.cfg (Tesseract) - jeu de la visite (généré par tools/tess_config.py)", "soundreset"]
game += [l.rstrip("\n") for l in open(f"{sauerdata}/sounds.cfg", encoding="latin-1")]
fps = open(f"{sauerdata}/game_fps.cfg", encoding="latin-1").read()
fps = strip_blocks(fps, ["newgui"])
game += ["", "// --- data/game_fps.cfg d'origine ---", fps]
pf = open(portfolio, encoding="utf-8").read()
pf = strip_blocks(pf, ["newgui"])
pf = pf.replace("autograss", "texgrass")
open(f"{out}/portfolio.cfg", "w", encoding="utf-8").write("// portfolio.cfg (Tesseract) - réglages de la visite\n" + rename_keys(pf))
open(f"{out}/game.cfg", "w", encoding="utf-8").write("\n".join(game) + "\n")
open(f"{out}/sound.cfg", "w", encoding="utf-8").write("// sons : voir game.cfg (ordre de Sauerbraten)\n")
open(f"{out}/blendbrush.cfg", "w", encoding="utf-8").write("// pas d'édition de carte dans la visite\n")
