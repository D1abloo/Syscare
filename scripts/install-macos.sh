#!/usr/bin/env bash
set -euo pipefail

if command -v brew >/dev/null 2>&1; then
  brew install python || true
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Instala Python 3.10+ desde https://www.python.org/downloads/macos/ y vuelve a ejecutar este script."
  exit 1
fi

"$(dirname "$0")/install-dev.sh"
