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
    if cmd == "texture" and len(w) >= 3 and w[1] in ("0", "c", "diffuse"):
        # Tesseract : TEX_SCALE de 16 (8 dans Sauerbraten) -> échelle doublée pour garder
        # la même taille de texture dans le monde
        code, _, comment = line.partition("//")
        parts = code.split()
        while len(parts) < 7:
            parts.append("0" if len(parts) < 6 else "1")
        try:
            parts[6] = "%g" % (float(parts[6]) * 2)
        except ValueError:
            pass
        # panneaux de texte : sens horizontal des faces inversé par rapport à Sauerbraten
        if "pf/sign_" in parts[2]:
            parts[3] = {"0": "4", "4": "0", "1": "7", "7": "1", "2": "5", "5": "2", "3": "6", "6": "3"}.get(parts[3], parts[3])
        out.append(" ".join(parts) + ("   //" + comment if comment else ""))
        continue
    if cmd == "autograss":
        out.append(line.replace("autograss", "texgrass", 1))
        continue
    if cmd == "skylight":
        out.append("skylight 0x8898B0")
        continue
    if cmd == "ambient":
        out.append("ambient 0x303438")
        continue
    if cmd == "sunlightscale":
        out.append("sunlightscale 1.5")
        continue
    out.append(line)
out += ["atmo 1", "atmobright 1", "atmohaze 0.1", "fog 4000"]
open(dst, "w", encoding="utf-8").write("\n".join(out) + "\n")
