#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
EXP_DIR="${EXP_DIR:-experiments/cape_kg_eacl_20260627}"
OUTPUT_PREFIX="${OUTPUT_PREFIX:-qwen3_8b_strict_json_1200_full}"
NUM_SHARDS="${NUM_SHARDS:-8}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-1200}"
MAX_PROMPT_CHARS="${MAX_PROMPT_CHARS:-3600}"
CONDITIONS="${CONDITIONS:-B0_plain_llm,B1_predicate_constrained,B2_current_project,B3_edc_style,B4_taxonomy_rag,B5_procedural_prompt,P_cape_kg_actual,P_minus_CQ,P_minus_Evidence,P_minus_Procedural_schema,P_minus_Validator,P_minus_Standard_bridge,P_minus_Schema_retrieval}"

"$PYTHON_BIN" -m py_compile scripts/run_cape_llm_condition_baselines.py

for shard in $(seq 0 $((NUM_SHARDS - 1))); do
  CUDA_VISIBLE_DEVICES="$shard" "$PYTHON_BIN" scripts/run_cape_llm_condition_baselines.py \
    --output-dir "$EXP_DIR" \
    --chunk-file 01_data/evaluation_chunks.jsonl \
    --conditions "$CONDITIONS" \
    --output-prefix "$OUTPUT_PREFIX" \
    --num-shards "$NUM_SHARDS" \
    --shard-index "$shard" \
    --max-new-tokens "$MAX_NEW_TOKENS" \
    --max-prompt-chars "$MAX_PROMPT_CHARS" \
    --strict-json-contract \
    --resume &
done

wait

"$PYTHON_BIN" scripts/run_cape_llm_condition_baselines.py \
  --output-dir "$EXP_DIR" \
  --chunk-file 01_data/evaluation_chunks.jsonl \
  --conditions "$CONDITIONS" \
  --output-prefix "$OUTPUT_PREFIX" \
  --num-shards "$NUM_SHARDS" \
  --merge-shards \
  --strict-json-contract
