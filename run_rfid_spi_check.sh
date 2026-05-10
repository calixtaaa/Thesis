#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$ROOT_DIR/venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "[ERR] Virtualenv python not found at: $VENV_PYTHON"
    echo "Create the venv first, then rerun this script."
    exit 1
fi

cd "$ROOT_DIR"

export PYTHONNOUSERSITE=1

echo "Checking RFID SPI link..."

output="$($VENV_PYTHON rfid_single_reader_test.py --probe-spi 2>&1)" || {
    printf '%s\n' "$output"
    echo "SPI FAIL"
    exit 1
}

printf '%s\n' "$output"
if printf '%s\n' "$output" | grep -qi 'PASS'; then
    echo "SPI PASS"
else
    echo "SPI FAIL"
    exit 1
fi