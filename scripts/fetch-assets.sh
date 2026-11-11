#!/usr/bin/env bash
# Télécharge (une seule fois) les sources externes du jeu, en vérifiant leur somme SHA-256 :
#  - l'archive officielle de Cube 2: Sauerbraten, édition 2020_12_29 (SourceForge) ;
#  - les musiques libres de droit (OpenGameArt, CC0).
# Puis extrait le sous-ensemble d'assets utilisé (tools/sauer_assets.txt) dans build/sauer.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE="${CACHE_DIR:-$ROOT/third_party/cache}"
mkdir -p "$CACHE/music"

SAUER_FILE="sauerbraten_2020_12_29_linux.tar.bz2"
SAUER_SHA256="cdba7c4a47cefd30d0afdd6a912199a1384319cf1619923cb7189e72e468be70"
SAUER_URLS=(
  "https://sourceforge.net/projects/sauerbraten/files/sauerbraten/2020_11_29/${SAUER_FILE}/download"
  "https://downloads.sourceforge.net/project/sauerbraten/sauerbraten/2020_11_29/${SAUER_FILE}"
)

# nom_local | sha256 | URL officielle (OpenGameArt, « 4 Chiptunes (Adventure) » de Juhani Junkala, CC0)
MUSIC=(
  "stage1.ogg|cd35b9cf8929352d60b79fdedbe43f7fab3e6e0c228b22970851c542a89f0531|https://opengameart.org/sites/default/files/Juhani%20Junkala%20%5BChiptune%20Adventures%5D%201.%20Stage%201.ogg"
  "stage2.ogg|68ec252839e1f227275fe46fca5e38ffab5086b39a6ab2650a752e4f2ef2a5a7|https://opengameart.org/sites/default/files/Juhani%20Junkala%20%5BChiptune%20Adventures%5D%202.%20Stage%202.ogg"
  "stageselect.ogg|8d5c0456107049b0d846b72eba722bea5f897e3b2c96a68512edb8f898170e7c|https://opengameart.org/sites/default/files/Juhani%20Junkala%20%5BChiptune%20Adventures%5D%204.%20Stage%20Select.ogg"
)

check() { echo "$2  $1" | sha256sum -c --status; }

fetch() { # fichier sha256 url...
  local f="$1" sum="$2"; shift 2
  if [ -f "$f" ] && check "$f" "$sum"; then return 0; fi
  for url in "$@"; do
    echo "==> téléchargement $(basename "$f")"
    if curl -fL --retry 3 -o "$f.part" "$url" && check "$f.part" "$sum"; then mv "$f.part" "$f"; return 0; fi
    echo "   (échec ou somme incorrecte, source suivante)"
  done
  rm -f "$f.part"; echo "ERREUR : impossible d'obtenir $(basename "$f")" >&2; exit 1
}

fetch "$CACHE/$SAUER_FILE" "$SAUER_SHA256" "${SAUER_URLS[@]}"
for m in "${MUSIC[@]}"; do
  IFS='|' read -r name sum url <<<"$m"
  fetch "$CACHE/music/$name" "$sum" "$url"
done

[ "${FETCH_ONLY:-0}" = 1 ] && exit 0

# Extraction du sous-ensemble (refaite seulement si la liste change)
OUT="$ROOT/build/sauer"
STAMP="$OUT/.stamp"
WANT="$(sha256sum "$ROOT/tools/sauer_assets.txt" "$ROOT/tools/prepare_sauer.py" | sha256sum | cut -c1-64)"
if [ ! -f "$STAMP" ] || [ "$(cat "$STAMP")" != "$WANT" ]; then
  rm -rf "$OUT"
  python3 "$ROOT/tools/prepare_sauer.py" "$CACHE/$SAUER_FILE" "$OUT"
  echo "$WANT" > "$STAMP"
fi
