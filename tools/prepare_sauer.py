#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extrait de l'archive officielle de Cube 2: Sauerbraten (édition 2020) le
sous-ensemble d'assets utilisé par la visite (liste : tools/sauer_assets.txt),
avec les fichiers de licence / readme de chaque dossier.

Optimisations pour le web (les fichiers d'origine ne sont pas modifiés autrement) :
  - les textures compressées .dds (doublons des .png/.jpg) sont ignorées ;
  - les images des modèles sont réduites (512 px pour le joueur, ses armes et les
    monstres, 256 px pour le reste et pour les cartes de normales) ; les PNG sans
    transparence deviennent des JPEG et les .cfg des modèles sont mis à jour ;
  - les reflets d'environnement (envmap) des modèles sont retirés (les skyboxes
    correspondantes ne sont pas embarquées).

Usage : prepare_sauer.py <archive.tar.bz2> <dossier_sortie> [liste]
"""
import fnmatch
import io
import os
import sys
import tarfile

from PIL import Image

LICENSE_HINTS = ("licen", "readme", "copying", ".txt", "authors", "permission")


def load_list(path):
    pats = []
    for line in open(path, encoding="utf-8"):
        line = line.split("#", 1)[0].strip()
        if line:
            pats.append(line)
    return pats


def wanted(rel, pats):
    if rel.lower().endswith(".dds"):
        return False
    for p in pats:
        if p.endswith("/"):
            if rel.startswith(p):
                return True
        elif fnmatch.fnmatch(rel, p):
            return True
    # licences / readme des dossiers dont on reprend au moins un fichier
    base = os.path.basename(rel).lower()
    if any(h in base for h in LICENSE_HINTS) and not base.endswith((".cfg", ".png", ".jpg", ".ogg", ".wav")):
        d = os.path.dirname(rel) + "/"
        for p in pats:
            if p.startswith(d) or (p.endswith("/") and d.startswith(p)):
                return True
    return False


def extract(archive, out, pats):
    n = 0
    with tarfile.open(archive, "r:*") as tar:
        for m in tar:
            if not m.isfile():
                continue
            parts = m.name.split("/", 1)
            if len(parts) < 2:
                continue
            rel = parts[1]                      # retire « sauerbraten/ »
            if not wanted(rel, pats):
                continue
            dst = os.path.join(out, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with tar.extractfile(m) as src, open(dst, "wb") as f:
                f.write(src.read())
            n += 1
    return n


def optimize_models(out):
    root = os.path.join(out, "packages", "models")
    renamed = {}
    for dirpath, _, files in os.walk(root):
        for fn in files:
            low = fn.lower()
            if not low.endswith((".png", ".jpg")):
                continue
            path = os.path.join(dirpath, fn)
            im = Image.open(path)
            normal = any(k in low for k in ("norm", "_nrm", "normals"))
            rel = os.path.relpath(path, root)
            big = rel.startswith(("mrfixit", "hudguns", "monster"))
            limit = 256 if (normal or not big) else 512
            changed = False
            if max(im.size) > limit:
                k = limit / max(im.size)
                im = im.resize((max(1, int(im.size[0] * k)), max(1, int(im.size[1] * k))), Image.LANCZOS)
                changed = True
            has_alpha = im.mode in ("RGBA", "LA") or "transparency" in im.info
            if has_alpha and im.mode in ("RGBA", "LA"):
                has_alpha = im.getchannel("A").getextrema()[0] < 255
            if low.endswith(".png") and not has_alpha:
                newfn = fn[:-4] + ".jpg"
                im.convert("RGB").save(os.path.join(dirpath, newfn), quality=88, optimize=True)
                os.remove(path)
                renamed[fn] = newfn
            elif changed:
                if low.endswith(".jpg"):
                    im.convert("RGB").save(path, quality=88, optimize=True)
                else:
                    im.save(path, optimize=True)
    # met à jour les références dans les .cfg des modèles
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".cfg"):
                continue
            p = os.path.join(dirpath, fn)
            s = open(p, encoding="latin-1").read()
            # reflets d'environnement (envmap) retirés : skyboxes non embarquées
            t = "\n".join(l for l in s.split("\n") if "envmap" not in l)
            for a, b in renamed.items():
                t = t.replace('"' + a, '"' + b).replace('>' + a, '>' + b).replace(' ' + a, ' ' + b)
            if t != s:
                open(p, "w", encoding="latin-1").write(t)
    return len(renamed)


def main():
    archive, out = sys.argv[1], sys.argv[2]
    lst = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "sauer_assets.txt")
    pats = load_list(lst)
    os.makedirs(out, exist_ok=True)
    n = extract(archive, out, pats)
    r = optimize_models(out)
    print("Sauerbraten : %d fichiers extraits, %d images de modèles converties en JPEG" % (n, r))


if __name__ == "__main__":
    main()
