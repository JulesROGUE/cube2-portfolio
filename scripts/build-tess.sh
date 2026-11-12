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

echo "==> Assets Sauerbraten, carte"
./scripts/fetch-assets.sh
rm -rf build/gamedata "$FS"
python3 tools/gen_assets.py build/gamedata
python3 tools/gen_map.py build/gamedata build/sauer build/gamedata

echo "==> Système de fichiers"
mkdir -p "$FS/media/texture" "$FS/media/model" "$FS/media/map" "$FS/media/sound" "$FS/media/particle" "$FS/media/interface"
cp -r tesseract/config "$FS/config"
python3 tools/tess_config.py build/sauer/data game/data/portfolio.cfg "$FS/config"
cp tesseract/webconfig/ui.cfg "$FS/config/ui.cfg"
rm -f "$FS/config/ui/fkey.cfg" "$FS/config/ui/edithud.cfg" "$FS/config/ui/serverbrowser.cfg" "$FS/config/ui/stats.cfg" "$FS/config/ui/scoreboard.cfg"
# textures (paquets Sauerbraten, dont textures maison) ; décors, joueurs, armes, monstres
for d in build/sauer/packages/*/; do n=$(basename "$d"); case "$n" in models|sounds|particles) ;; *) cp -r "$d" "$FS/media/texture/$n";; esac; done
cp -r build/gamedata/packages/. "$FS/media/texture/"
cp -r build/sauer/packages/models/. "$FS/media/model/"
# chemins des scripts de modèles (Sauerbraten : packages/models/...) -> media/model/
find "$FS/media/model" -name '*.cfg' -exec sed -i 's#packages/models/#media/model/#g' {} +
cp -r build/sauer/packages/sounds/. "$FS/media/sound/"
cp -r build/sauer/packages/particles/. "$FS/media/particle/"
# interface : police DejaVu de Tesseract (licence Bitstream Vera / DejaVu), icônes de Sauerbraten
mkdir -p "$FS/media/interface/font" "$FS/media/interface/hud" "$FS/media/interface/crosshair"
cp tesseract/media/interface/font/*.cfg tesseract/media/interface/font/*.png tesseract/media/interface/font/*.txt "$FS/media/interface/font/"
cp build/sauer/packages/hud/* "$FS/media/interface/hud/"
cp build/sauer/packages/crosshairs/* "$FS/media/interface/crosshair/"
cp build/sauer/data/crosshair.png build/sauer/data/hit.png build/sauer/data/teammate.png "$FS/media/interface/crosshair/"
cp build/sauer/data/crosshair.png "$FS/media/interface/crosshair/default.png"
cp build/sauer/data/hit.png "$FS/media/interface/crosshair/default_hit.png"
# images d'interface de Sauerbraten (data/, voir data/license.txt) aux emplacements attendus par Tesseract
for f in background logo loading_bar loading_frame mapshot_frame cube; do cp "build/sauer/data/$f.png" "$FS/media/interface/$f.png"; done
cp build/sauer/data/guicursor.png "$FS/media/interface/cursor.png"
mkdir -p "$FS/media/texture/game"
cp build/sauer/packages/textures/notexture.png "$FS/media/texture/game/notexture.png"
cp build/gamedata/packages/base/portfolio.ogz build/gamedata/packages/base/portfolio.wpt "$FS/media/map/"
python3 -c "from PIL import Image; Image.open('build/gamedata/packages/base/portfolio.jpg').save('$FS/media/map/portfolio.png')"
# ombre du fond de chargement : image vide (transparente)
python3 -c "from PIL import Image; Image.new('RGBA', (4, 4), (0, 0, 0, 0)).save('$FS/media/interface/shadow.png')"
cp "$FS/media/interface/logo.png" "$FS/media/interface/logo_1024.png"
# réglages de carte par défaut : ceux de la visite (pas de textures de Tesseract)
printf '%s\n' '// réglages par défaut : la carte de la visite fournit les siens' 'materialreset' 'texturereset' 'mapmodelreset' > "$FS/config/default_map_settings.cfg"
printf '%s\n' '// pas de décors par défaut' > "$FS/config/default_map_models.cfg"
python3 tools/tess_mapcfg.py build/gamedata/packages/base/portfolio.cfg "$FS/media/map/portfolio.cfg"

echo "==> Paquet de données"
mkdir -p "$OUT"
PACKAGER="$(dirname "$(command -v emcc)")/tools/file_packager.py"
[ -f "$PACKAGER" ] || PACKAGER="$(dirname "$(command -v emcc)")/tools/file_packager"
python3 "$PACKAGER" "$OUT/cube2.data" --preload "$FS@/" --js-output="$OUT/cube2-data.js" --no-node

echo "==> Moteur"
make -C tesseract web -j"$JOBS" WEB_OUT="$OUT"
mkdir -p "$OUT/music"
cp "${CACHE_DIR:-$ROOT/third_party/cache}"/music/*.ogg "$OUT/music/"
cp web/index.html web/portfolio.js web/portfolio.css "$OUT/"
BUILD="$(cat "$OUT/cube2.js" "$OUT/cube2.wasm" "$OUT/cube2-data.js" "$OUT/portfolio.js" "$OUT/portfolio.css" | sha1sum | cut -c1-12)"
sed -i "s/__BUILD__/$BUILD/g" "$OUT/index.html"
echo "==> Build $BUILD"
ls -la "$OUT"
