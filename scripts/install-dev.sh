#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"
export PIP_CACHE_DIR="$APP_DIR/.pip-cache"

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --disable-pip-version-check -r requirements.txt || true

install_fallback() {
  echo "No se pudo instalar como paquete editable. Creando enlace local de desarrollo..."
  SITE_PACKAGES="$(python - <<'PY'
import site
print(site.getsitepackages()[0])
PY
)"
  echo "$APP_DIR/src" > "$SITE_PACKAGES/syscare_app_dev.pth"
  cat > ".venv/bin/syscare" <<'EOF'
#!/usr/bin/env bash
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$APP_DIR"
exec "$APP_DIR/.venv/bin/python" -m syscare_app "$@"
EOF
  chmod +x ".venv/bin/syscare"
}

if python - <<'PY' 2>/dev/null
import setuptools  # noqa: F401
PY
then
  if ! python -m pip install --disable-pip-version-check --no-build-isolation -e .; then
    install_fallback
  fi
else
  install_fallback
fi

echo "Instalado en $APP_DIR"
echo "Lanza la app con: cd \"$APP_DIR\" && source .venv/bin/activate && syscare"
