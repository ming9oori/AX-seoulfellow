#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PORT="${PORT:-8765}"
HOST="${HOST:-127.0.0.1}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ ! -f outputs/09_visualization/kg_viewer.html ]]; then
  echo "KG viewer not found: outputs/09_visualization/kg_viewer.html" >&2
  echo "Run scripts/build_ax_epak_internal_kg.py first." >&2
  exit 1
fi

echo "Serving AX KG viewer from: $(pwd)"
echo "URL: http://${HOST}:${PORT}/outputs/09_visualization/kg_viewer.html"
echo
echo "In VS Code Remote SSH:"
echo "  1. Forward port ${PORT} in the Ports panel."
echo "  2. Open Command Palette -> Simple Browser: Show."
echo "  3. Enter http://localhost:${PORT}/outputs/09_visualization/kg_viewer.html"
echo
echo "Press Ctrl-C to stop the server."

"$PYTHON_BIN" -m http.server "$PORT" --bind "$HOST"
