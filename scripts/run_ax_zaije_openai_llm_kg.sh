#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-/home/minjoo/miniconda3/envs/py311/bin/python}"
MODEL="${OPENAI_MODEL:-gpt-4o-mini}"
OUTPUT_DIR="${OUTPUT_DIR:-experiments/ax_zaije_layer2_kg_openai_20260707/layer2_kg}"

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "ERROR: OPENAI_API_KEY is not set." >&2
  echo "Set it in your shell, then rerun:" >&2
  echo "  export OPENAI_API_KEY='YOUR_NEW_KEY'" >&2
  echo "  bash scripts/run_ax_zaije_openai_llm_kg.sh" >&2
  exit 2
fi

"${PYTHON_BIN}" scripts/run_ax_zaije_openai_llm_kg.py \
  --model "${MODEL}" \
  --output-dir "${OUTPUT_DIR}" \
  --resume
