#!/usr/bin/env bash
# Construit le client web : assets d'origine (Sauerbraten) + assets maison + carte + WASM.
# Sortie : dist/cube2/ (index.html, portfolio.js/css, cube2.js, cube2.wasm, cube2.data,
#          cube2-data.js, music/*.ogg chargées à la demande)
# Prérequis : emsdk activé (emcc dans le PATH), python3 + Pillow + numpy, police DejaVu, curl.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

JOBS="${JOBS:-$(nproc)}"
OUT="$ROOT/dist/cube2"
FSROOT="$ROOT/build/fsroot"

echo "==> Assets d'origine de Cube 2 (archive officielle épinglée) et musiques"
./scripts/fetch-assets.sh

echo "==> Assets maison et carte"
rm -rf build/gamedata "$FSROOT"
python3 tools/gen_assets.py build/gamedata
python3 tools/gen_map.py build/gamedata build/sauer build/gamedata

echo "==> Assemblage du système de fichiers du jeu"
mkdir -p "$FSROOT"
cp -r build/sauer/. "$FSROOT/"
rm -f "$FSROOT/.stamp"
cp -r game/. "$FSROOT/"
cp -r build/gamedata/. "$FSROOT/"

echo "==> Paquet de données Emscripten"
mkdir -p "$OUT/music"
PACKAGER="$(dirname "$(command -v emcc)")/tools/file_packager.py"
[ -f "$PACKAGER" ] || PACKAGER="$(dirname "$(command -v emcc)")/tools/file_packager"
python3 "$PACKAGER" "$OUT/cube2.data" --preload "$FSROOT@/" --js-output="$OUT/cube2-data.js" --no-node

echo "==> Musiques (hors paquet, chargées à la demande)"
cp "${CACHE_DIR:-$ROOT/third_party/cache}"/music/*.ogg "$OUT/music/"

echo "==> Compilation du moteur (WebAssembly)"
make -C engine web -j"$JOBS" WEB_OUT="$OUT"

echo "==> Coquille web"
cp web/index.html web/portfolio.js web/portfolio.css "$OUT/"

ls -la "$OUT"
