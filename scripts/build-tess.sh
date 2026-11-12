#!/usr/bin/env bash
# Portage Tesseract (branche tesseract) : construit le client web dans dist-tess/cube2/.
# Système de fichiers du jeu : config/ (scripts et shaders de Tesseract, zlib), media/
# (ressources : celles de Sauerbraten à licence vérifiée, rangées comme Tesseract les attend).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
JOBS="${JOBS:-$(nproc)}"
OUT="$ROOT/dist-tess/cube2"
FS="$ROOT/build/tessfs"
TESSMEDIA="${TESSMEDIA:-}"

echo "==> Assets Sauerbraten, carte"
./scripts/fetch-assets.sh
rm -rf build/gamedata "$FS"
python3 tools/gen_assets.py build/gamedata
python3 tools/gen_map.py build/gamedata build/sauer build/gamedata

echo "==> Système de fichiers"
mkdir -p "$FS/media/texture" "$FS/media/model/mapmodel" "$FS/media/map"
cp -r tesseract/config "$FS/config"
# textures (paquets Sauerbraten) et décors
for d in build/sauer/packages/*/; do n=$(basename "$d"); [ "$n" = models ] || cp -r "$d" "$FS/media/texture/$n"; done
cp -r build/gamedata/packages/. "$FS/media/texture/" 2>/dev/null || true
cp -r build/sauer/packages/models/. "$FS/media/model/mapmodel/"
cp build/gamedata/packages/base/portfolio.ogz "$FS/media/map/"
python3 tools/tess_mapcfg.py build/gamedata/packages/base/portfolio.cfg "$FS/media/map/portfolio.cfg"
# prototype : interface et modèles de jeu de Tesseract (remplacés aux étapes suivantes)
if [ -n "$TESSMEDIA" ]; then
  for d in interface particle texture/game model/player model/hudgun model/worldgun model/game sound; do
    mkdir -p "$FS/media/$(dirname $d)"; cp -r "$TESSMEDIA/$d" "$FS/media/$d"; done
fi

echo "==> Paquet de données"
mkdir -p "$OUT"
PACKAGER="$(dirname "$(command -v emcc)")/tools/file_packager.py"
[ -f "$PACKAGER" ] || PACKAGER="$(dirname "$(command -v emcc)")/tools/file_packager"
python3 "$PACKAGER" "$OUT/tess.data" --preload "$FS@/" --js-output="$OUT/tess-data.js" --no-node

echo "==> Moteur"
make -C tesseract web -j"$JOBS" WEB_OUT="$OUT"
cp web-tess/index.html "$OUT/" 2>/dev/null || true
ls -la "$OUT"
