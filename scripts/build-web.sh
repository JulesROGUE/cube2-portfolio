#!/usr/bin/env bash
# Construit le client web : assets générés + carte + paquet de données + WASM.
# Sortie : dist/cube2/ (index.html, portfolio.js/css, cube2.js, cube2.wasm, cube2.data, cube2-data.js)
# Prérequis : emsdk activé (emcc dans le PATH), python3 + Pillow, police DejaVu.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

JOBS="${JOBS:-$(nproc)}"
OUT="$ROOT/dist/cube2"
FSROOT="$ROOT/build/fsroot"

echo "==> Génération des assets et de la carte"
rm -rf build/gamedata "$FSROOT"
python3 tools/gen_assets.py build/gamedata
python3 tools/gen_map.py build/gamedata

echo "==> Assemblage du système de fichiers du jeu"
mkdir -p "$FSROOT"
cp -r game/. "$FSROOT/"
cp -r build/gamedata/. "$FSROOT/"

echo "==> Paquet de données Emscripten"
mkdir -p "$OUT"
PACKAGER="$(dirname "$(command -v emcc)")/tools/file_packager.py"
[ -f "$PACKAGER" ] || PACKAGER="$(dirname "$(command -v emcc)")/tools/file_packager"
python3 "$PACKAGER" "$OUT/cube2.data" --preload "$FSROOT@/" --js-output="$OUT/cube2-data.js" --no-node

echo "==> Compilation du moteur (WebAssembly)"
make -C engine web -j"$JOBS" WEB_OUT="$OUT"

echo "==> Coquille web"
cp web/index.html web/portfolio.js web/portfolio.css "$OUT/"

ls -la "$OUT"
