#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/opt/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin:$PATH"
export PYTHONPATH="$APP_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
if ! python - <<'PY' 2>/dev/null
import PySide6  # noqa: F401
PY
then
  "$APP_DIR/scripts/install-dev.sh"
fi
python -m syscare_app
