#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DESKTOP_FILE="${HOME}/.local/share/applications/syscare.desktop"
mkdir -p "$(dirname "$DESKTOP_FILE")"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=SysCare
Comment=Limpieza, paquetes, rendimiento y archivos
Exec=${APP_DIR}/scripts/run.sh
Icon=${APP_DIR}/src/syscare_app/assets/app_icon.svg
Terminal=false
Categories=Utility;System;
EOF

chmod +x "$DESKTOP_FILE"
echo "Lanzador creado en $DESKTOP_FILE"
