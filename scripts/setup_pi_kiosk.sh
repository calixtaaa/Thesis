#!/usr/bin/env bash
# Configure Raspberry Pi to skip the login prompt and auto-start the vending app.
#
# Run ON THE PI (once), from the project folder:
#   chmod +x scripts/setup_pi_kiosk.sh
#   ./scripts/setup_pi_kiosk.sh
#
# What this does:
#   1. Desktop auto-login (boot straight into the graphical OS)
#   2. Autostart main.py on login (fullscreen vending UI)
#   3. Optional larger console font (for tty messages before the GUI loads)
#   4. Disable screen blanking on the graphical session

set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Re-run with sudo:  sudo ./scripts/setup_pi_kiosk.sh"
  exit 1
fi

TARGET_USER="${SUDO_USER:-${USER:-pi}}"
TARGET_HOME="$(eval echo "~${TARGET_USER}")"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AUTOSTART_DIR="${TARGET_HOME}/.config/autostart"
DESKTOP_FILE="${AUTOSTART_DIR}/hygiene-vending.desktop"
VENV_PY="${PROJECT_DIR}/venv/bin/python"
MAIN_PY="${PROJECT_DIR}/main.py"

echo "Project:  ${PROJECT_DIR}"
echo "User:     ${TARGET_USER}"

if [[ ! -x "${VENV_PY}" ]]; then
  echo "Warning: ${VENV_PY} not found. Create the venv first:"
  echo "  cd ${PROJECT_DIR} && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
fi

# B3 = boot to desktop with auto-login (skips the tty 'login:' screen).
if command -v raspi-config >/dev/null 2>&1; then
  echo "Enabling desktop auto-login (raspi-config)..."
  raspi-config nonint do_boot_behaviour B3 || true
else
  echo "raspi-config not found; configure auto-login manually in Pi Configuration."
fi

# Graphical autostart (.desktop is the standard way on Pi OS Bookworm).
install -d -o "${TARGET_USER}" -g "${TARGET_USER}" "${AUTOSTART_DIR}"
cat >"${DESKTOP_FILE}" <<EOF
[Desktop Entry]
Type=Application
Name=Hygiene Vending Machine
Comment=Auto-start vending UI on boot
Exec=/bin/bash -lc 'cd "${PROJECT_DIR}" && source venv/bin/activate && export DISPLAY=:0 && export PYTHONNOUSERSITE=1 && export MCP23017_ADDRESSES=0x20,0x21,0x22 && export UI_LCD_SCALE=1.6 && exec venv/bin/python main.py'
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
chown "${TARGET_USER}:${TARGET_USER}" "${DESKTOP_FILE}"
chmod 644 "${DESKTOP_FILE}"
echo "Wrote ${DESKTOP_FILE}"

# Keep the display awake during operation.
if command -v raspi-config >/dev/null 2>&1; then
  raspi-config nonint do_blanking 1 || true
fi

# Slightly larger text on the boot console (optional; re-run setupcon after reboot).
if [[ -f /etc/default/console-setup ]]; then
  if grep -q '^FONTSIZE=' /etc/default/console-setup; then
    sed -i 's/^FONTSIZE=.*/FONTSIZE="14x28"/' /etc/default/console-setup
  else
    echo 'FONTSIZE="14x28"' >>/etc/default/console-setup
  fi
  setupcon 2>/dev/null || true
fi

echo ""
echo "Done. Reboot to apply:"
echo "  sudo reboot"
echo ""
echo "After reboot you should land on the desktop and the vending app should open."
echo "To stop auto-start temporarily, remove or rename:"
echo "  ${DESKTOP_FILE}"
