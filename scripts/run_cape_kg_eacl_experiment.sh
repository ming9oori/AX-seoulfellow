#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0,1,2,3,4,5,6,7}"

PY311="${PYTHON_BIN:-python3}"
if [[ -x "$HOME/miniconda3/envs/py311/bin/python" ]]; then
  PY311="$HOME/miniconda3/envs/py311/bin/python"
elif [[ -x "$HOME/miniconda3/bin/python" ]]; then
  PY311="$HOME/miniconda3/bin/python"
fi

LLM_PYTHON="${LLM_PYTHON:-python3}"
EXP_DIR="${EXP_DIR:-experiments/cape_kg_eacl_20260627}"
SAMPLE_SIZE="${SAMPLE_SIZE:-120}"
LLM_SMOKE_CHUNKS="${LLM_SMOKE_CHUNKS:-10}"

"$PY311" -m py_compile scripts/build_ax_epak_internal_kg.py scripts/build_cape_kg_eacl_experiment.py

bash scripts/run_ax_epak_preprocessed.sh

rm -rf "$EXP_DIR"
"$PY311" scripts/build_cape_kg_eacl_experiment.py \
  --kg-dir outputs \
  --experiment-dir "$EXP_DIR" \
  --sample-size "$SAMPLE_SIZE"

if [[ -x "$LLM_PYTHON" && "$LLM_SMOKE_CHUNKS" != "0" ]]; then
  CUDA_VISIBLE_DEVICES="${LLM_CUDA_VISIBLE_DEVICES:-0}" "$LLM_PYTHON" scripts/run_cep_onto_llm_extraction.py \
    --output-dir "$EXP_DIR" \
    --chunk-file 01_data/evaluation_chunks.jsonl \
    --max-chunks "$LLM_SMOKE_CHUNKS" \
    --max-new-tokens 800 \
    --max-prompt-chars 4500 \
    --progress-every 2

  "$PY311" scripts/build_cape_kg_eacl_experiment.py \
    --kg-dir outputs \
    --experiment-dir "$EXP_DIR" \
    --sample-size "$SAMPLE_SIZE"
else
  echo "Skipping LLM smoke run; LLM_PYTHON is not executable or LLM_SMOKE_CHUNKS=0."
fi

echo
echo "CAPE-KG EACL experiment package complete."
echo "Summary: $EXP_DIR/run_summary.json"
echo "Final report: $EXP_DIR/07_reports/final_eacl_experiment_report.md"
