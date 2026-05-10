#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$ROOT_DIR/venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "[ERR] Virtualenv python not found at: $VENV_PYTHON"
    exit 1
fi

cd "$ROOT_DIR"
export PYTHONNOUSERSITE=1

"$VENV_PYTHON" gpio_toggle_single.py 6

echo ""
echo "Press Enter to close..."
read -r
