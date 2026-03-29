#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
#  Netlify Build Script — Hygiene Vending Machine
#  Copies static assets to CDN dir + bundles Flask into the
#  serverless function directory.
# ══════════════════════════════════════════════════════════════════
set -e

echo "══════════════════════════════════════════"
echo "  Hygiene Vending — Netlify Build"
echo "══════════════════════════════════════════"

# ── 1. CDN-served static assets ──────────────────────────────────
echo ""
echo "→ Copying static assets to public/"
mkdir -p public/static/css public/static/js public/static/images

cp WebPages/static/css/*    public/static/css/    2>/dev/null || true
cp WebPages/static/js/*     public/static/js/     2>/dev/null || true
[ -d WebPages/static/images ] && cp -r WebPages/static/images/* public/static/images/ || true

# ── 2. Bundle Python files into the function directory ───────────
FDIR="netlify/functions/app"
echo "→ Bundling Flask app → $FDIR/"

# Flask app + Jinja2 templates
mkdir -p "$FDIR/WebPages/templates" "$FDIR/WebPages/static"
cp    WebPages/server.py          "$FDIR/WebPages/"
cp -r WebPages/templates/*        "$FDIR/WebPages/templates/"
cp -r WebPages/static/*           "$FDIR/WebPages/static/"

# Core Python modules
cp database.py             "$FDIR/"
cp prediction_runtime.py   "$FDIR/"  2>/dev/null || true

# Admin package
mkdir -p "$FDIR/admin"
cp -r admin/* "$FDIR/admin/"

# Prediction analysis package
mkdir -p "$FDIR/predictionAnalysis"
cp -r predictionAnalysis/* "$FDIR/predictionAnalysis/" 2>/dev/null || true

# Database + salt (if present)
cp vending.db    "$FDIR/"  2>/dev/null || echo "  ⚠ vending.db not found — will create empty DB"
cp .secret_salt  "$FDIR/"  2>/dev/null || echo "  ⚠ .secret_salt not found — will generate at runtime"

# ── 3. Done ──────────────────────────────────────────────────────
echo ""
echo "✔ Build complete — ready to deploy"
echo "══════════════════════════════════════════"
