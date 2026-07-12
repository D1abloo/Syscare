#!/usr/bin/env bash
set -euo pipefail

if command -v apt >/dev/null 2>&1; then
  sudo apt update
  sudo apt install -y python3 python3-venv python3-pip pkexec
elif command -v dnf >/dev/null 2>&1; then
  sudo dnf install -y python3 python3-pip python3-virtualenv polkit
elif command -v pacman >/dev/null 2>&1; then
  sudo pacman -S --needed python python-pip python-virtualenv polkit
elif command -v zypper >/dev/null 2>&1; then
  sudo zypper install -y python3 python3-pip python3-virtualenv polkit
else
  echo "No se detecto apt, dnf, pacman ni zypper. Instala Python 3.10+, venv y pip manualmente."
fi

"$(dirname "$0")/install-dev.sh"
"$(dirname "$0")/create-linux-launcher.sh"
