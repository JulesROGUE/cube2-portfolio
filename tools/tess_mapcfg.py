#!/usr/bin/env python3
"""Adapte le .cfg de carte généré pour Sauerbraten (gen_map.py) au moteur Tesseract.

Tesseract charge la carte .ogz telle quelle (format OCTA 33 converti au chargement) ;
seul le fichier de réglages diffère (éclairage dynamique, ciel, noms de commandes).
"""
import sys

src, dst = sys.argv[1], sys.argv[2]
out = ["// portfolio.cfg (Tesseract) - adapté de la carte Sauerbraten par tools/tess_mapcfg.py"]
for line in open(src, encoding="utf-8"):
    line = line.rstrip("\n")
    w = line.split()
    if not w:
        out.append(line)
        continue
    cmd = w[0]
    if cmd in ("skybox", "lightprecision", "watercolour"):
        continue                       # ciel procédural de Tesseract (atmo) ; pas de lightmaps
    if cmd == "skylight":
        out.append("skylight 0x404850")
        continue
    if cmd == "sunlightscale":
        out.append("sunlightscale 1.5")
        continue
    out.append(line)
out += ["atmo 1", "atmobright 1", "atmohaze 0.1", "fog 4000"]
open(dst, "w", encoding="utf-8").write("\n".join(out) + "\n")
