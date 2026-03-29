#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
#  Netlify Build — Hygiene Vending Machine
#  1. Installs Flask (for Jinja2 template rendering)
#  2. Renders all templates into static HTML  →  public/
#  3. Copies static assets (CSS, JS, images)  →  public/static/
# ══════════════════════════════════════════════════════════════════
set -e

echo "══════════════════════════════════════════"
echo "  Hygiene Vending — Netlify Build"
echo "══════════════════════════════════════════"

# ── 1. Install Flask (for Jinja2 rendering) ──────────────────────
echo ""
echo "→ Installing build dependencies..."
pip install --quiet flask

# ── 2. Render Jinja2 templates to static HTML ────────────────────
echo "→ Rendering templates to public/"
python build_static.py

# ── 3. Copy static assets to CDN directory ───────────────────────
echo "→ Copying static assets..."
mkdir -p public/static/css public/static/js public/static/images

cp WebPages/static/css/*  public/static/css/  2>/dev/null || true
cp WebPages/static/js/*   public/static/js/   2>/dev/null || true

if [ -d "WebPages/static/images" ]; then
    cp -r WebPages/static/images/* public/static/images/ 2>/dev/null || true
fi

# ── Done ─────────────────────────────────────────────────────────
echo ""
FILE_COUNT=$(find public -type f | wc -l)
echo "✔ Build complete — $FILE_COUNT files ready to deploy"
echo "══════════════════════════════════════════"
