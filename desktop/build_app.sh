#!/usr/bin/env bash
# Builds Fauve.app from webui.py (see fauve.spec) and puts it in ~/Applications,
# where Spotlight and Launchpad find it. Run from anywhere:
#   bash desktop/build_app.sh
# First launch: right-click Fauve.app > Open (it's signed ad hoc, not with an
# Apple Developer ID, so a plain double-click is blocked the first time).
#
# The build happens outside this folder on purpose: Documents is synced by
# iCloud Drive, which adds file attributes that codesign refuses.
set -euo pipefail
cd "$(dirname "$0")"
source ../.venv/bin/activate

export FAUVE_WORK="${FAUVE_WORK:-$HOME/Library/Caches/Fauve-build}"
DEST="${FAUVE_DEST:-$HOME/Applications}"
mkdir -p "$FAUVE_WORK/Fauve.iconset" "$DEST"

# App icon: the night cat, at every size macOS asks for.
for s in 16 32 128 256 512; do
  sips -z $s $s assets/icon-night.png --out "$FAUVE_WORK/Fauve.iconset/icon_${s}x${s}.png" >/dev/null
  sips -z $((s * 2)) $((s * 2)) assets/icon-night.png --out "$FAUVE_WORK/Fauve.iconset/icon_${s}x${s}@2x.png" >/dev/null
done
iconutil -c icns "$FAUVE_WORK/Fauve.iconset" -o "$FAUVE_WORK/Fauve.icns"

pyinstaller --noconfirm --clean --log-level ERROR \
  --workpath "$FAUVE_WORK/build" --distpath "$FAUVE_WORK/dist" fauve.spec

APP="$FAUVE_WORK/dist/Fauve.app"
xattr -cr "$APP"
codesign --force --deep --sign - "$APP"
codesign --verify --deep --strict "$APP"

rm -rf "$DEST/Fauve.app"
ditto "$APP" "$DEST/Fauve.app"            # ditto keeps the signature and symlinks intact
codesign --verify --deep --strict "$DEST/Fauve.app"
echo "Built $DEST/Fauve.app ($(du -sh "$DEST/Fauve.app" | cut -f1)), signature OK"
