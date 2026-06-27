#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

export CUDA_VISIBLE_DEVICES=5,7

PYTHON_BIN="${PYTHON_BIN:-python3}"
if [[ -x "$HOME/miniconda3/envs/py311/bin/python" ]]; then
  PYTHON_BIN="$HOME/miniconda3/envs/py311/bin/python"
elif [[ -x "$HOME/miniconda3/bin/python" ]]; then
  PYTHON_BIN="$HOME/miniconda3/bin/python"
fi

"$PYTHON_BIN" -m py_compile scripts/build_cep_onto_kg.py scripts/build_ax_epak_internal_kg.py
"$PYTHON_BIN" scripts/build_ax_epak_internal_kg.py

echo
echo "AX-EPAK internal KG build complete."
echo "Summary: outputs/run_summary.json"
echo "Final report: outputs/10_evaluation/final_build_report.md"
echo "Viewer: outputs/09_visualization/kg_viewer.html"
