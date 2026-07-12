#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${HOME}/Applications/SysCare.app"
CONTENTS_DIR="${TARGET_DIR}/Contents"
MACOS_DIR="${CONTENTS_DIR}/MacOS"
RESOURCES_DIR="${CONTENTS_DIR}/Resources"
ICONSET_DIR="${RESOURCES_DIR}/SysCare.iconset"
ICNS_FILE="${RESOURCES_DIR}/SysCare.icns"

mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"

if [[ -x "${APP_DIR}/.venv/bin/python" ]]; then
  rm -rf "$ICONSET_DIR"
  mkdir -p "$ICONSET_DIR"
  "${APP_DIR}/.venv/bin/python" - <<PY || true
from pathlib import Path
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
import sys

app = QGuiApplication.instance() or QGuiApplication(sys.argv)
svg_path = Path("$APP_DIR/src/syscare_app/assets/app_icon.svg")
iconset = Path("$ICONSET_DIR")
sizes = [
    (16, "icon_16x16.png"),
    (32, "icon_16x16@2x.png"),
    (32, "icon_32x32.png"),
    (64, "icon_32x32@2x.png"),
    (128, "icon_128x128.png"),
    (256, "icon_128x128@2x.png"),
    (256, "icon_256x256.png"),
    (512, "icon_256x256@2x.png"),
    (512, "icon_512x512.png"),
    (1024, "icon_512x512@2x.png"),
]
renderer = QSvgRenderer(str(svg_path))
for size, name in sizes:
    image = QImage(QSize(size, size), QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    image.save(str(iconset / name))
PY
  if command -v iconutil >/dev/null 2>&1; then
    iconutil -c icns "$ICONSET_DIR" -o "$ICNS_FILE" || true
  fi
  rm -rf "$ICONSET_DIR"
fi

cat > "${CONTENTS_DIR}/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key>
  <string>SysCare</string>
  <key>CFBundleDisplayName</key>
  <string>SysCare</string>
  <key>CFBundleIdentifier</key>
  <string>local.syscare.app</string>
  <key>CFBundleVersion</key>
  <string>0.6.1</string>
  <key>CFBundleShortVersionString</key>
  <string>0.6.1</string>
  <key>CFBundleExecutable</key>
  <string>syscare</string>
  <key>CFBundleIconFile</key>
  <string>SysCare</string>
  <key>LSMinimumSystemVersion</key>
  <string>13.0</string>
  <key>LSUIElement</key>
  <false/>
</dict>
</plist>
EOF

cat > "${MACOS_DIR}/syscare" <<EOF
#!/usr/bin/env bash
cd "$APP_DIR"
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/opt/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:\$HOME/.local/bin:\$PATH"
export PYTHONPATH="$APP_DIR/src\${PYTHONPATH:+:\$PYTHONPATH}"
exec "$APP_DIR/.venv/bin/python" -m syscare_app
EOF

chmod +x "${MACOS_DIR}/syscare"
echo "Launcher creado en ${TARGET_DIR}"
