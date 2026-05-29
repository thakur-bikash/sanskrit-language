#!/bin/bash
# install_shobhika.sh
# Installs Shobhika & Shobhika-Bold OpenType fonts as user fonts on Fedora.
# Run once from anywhere:  bash install_shobhika.sh

set -e

FONT_DIR="$HOME/.local/share/fonts/shobhika"
mkdir -p "$FONT_DIR"

echo "==> Downloading Shobhika from CTAN..."
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
cd "$WORK"

curl -L --fail \
  "https://mirrors.ctan.org/fonts/shobhika.zip" \
  -o shobhika.zip

echo "==> Extracting .otf files..."
# CTAN zip has path opentype/ inside; fall back to flat if layout differs
unzip -j shobhika.zip "*/opentype/*.otf" -d "$FONT_DIR/" 2>/dev/null \
  || unzip -j shobhika.zip "*.otf" -d "$FONT_DIR/"

echo ""
echo "==> Installed:"
ls -1 "$FONT_DIR/"

echo ""
echo "==> Refreshing font cache..."
fc-cache -fv "$FONT_DIR"

echo ""
echo "==> Registered names (should show Shobhika and Shobhika-Bold):"
fc-list | grep -i shobhika

echo ""
echo "Done. Re-run your build script."
