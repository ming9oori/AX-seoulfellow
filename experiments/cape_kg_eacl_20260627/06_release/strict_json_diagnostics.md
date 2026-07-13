# Strict JSON Diagnostics

Generated: 2026-06-29T18:55:33.286920+00:00
Experiment: `experiments/cape_kg_eacl_20260627`
Source claim gate: `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.json`

## Status

- Strict JSON gate: PASS
- Recovery gate: PASS
- Conditions with full/smoke rows: 14
- Conditions over strict JSON warning threshold: 0
- Conditions over unrepaired error threshold: 0

Gate status is computed from the claim-gate-selected run for each condition. Historical strict-contract runs are retained separately for debugging and traceability.

Existing generated outputs and metrics are not modified by this diagnostic. The strict rate counts rows that did not parse as a clean JSON object before conservative partial-JSON recovery.

## Top Priority Conditions

- 1. B3_edc_style: strict=0.491667, repaired=0.491667, unrepaired=0.0 (monitor only)
- 2. P_minus_CQ: strict=0.4, repaired=0.4, unrepaired=0.0 (monitor only)
- 3. P_cape_kg_actual: strict=0.358333, repaired=0.358333, unrepaired=0.0 (monitor only)
- 4. P_minus_Validator: strict=0.358333, repaired=0.358333, unrepaired=0.0 (monitor only)
- 5. P_minus_Procedural_schema: strict=0.35, repaired=0.35, unrepaired=0.0 (monitor only)
- 6. B5_procedural_prompt: strict=0.325, repaired=0.325, unrepaired=0.0 (monitor only)
- 7. P_minus_Evidence: strict=0.325, repaired=0.325, unrepaired=0.0 (monitor only)
- 8. B4_taxonomy_rag: strict=0.291667, repaired=0.291667, unrepaired=0.0 (monitor only)
- 9. P_minus_Schema_retrieval: strict=0.258333, repaired=0.258333, unrepaired=0.0 (monitor only)
- 10. B2_current_project: strict=0.15, repaired=0.15, unrepaired=0.0 (monitor only)
- 11. B1_predicate_constrained: strict=0.141667, repaired=0.141667, unrepaired=0.0 (monitor only)
- 12. B0_plain_llm: strict=0.133333, repaired=0.133333, unrepaired=0.0 (monitor only)

## Strict Contract

Prompt contract file: `experiments/cape_kg_eacl_20260627/02_schema/prompts/strict_json_contract.txt`

```text
Strict JSON contract:
- Return exactly one JSON object and nothing else.
- The first non-whitespace character must be `{` and the last non-whitespace character must be `}`.
- Do not include markdown, code fences, comments, XML tags, `<think>` blocks, prose, or explanations.
- For Qwen/Qwen-style chat models, obey `/no_think`; do not emit hidden or visible reasoning.
- Output the JSON object immediately without a preamble.
- Use compact JSON without indentation or extra whitespace to reduce truncation risk.
- Use double-quoted JSON strings only.
- Use empty arrays for absent `nodes`, `edges`, `triples`, or `mappings` fields required by the requested shape.
```

## Smoke Rerun Template

```bash
CUDA_VISIBLE_DEVICES=0 /home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python scripts/run_cape_llm_condition_baselines.py --output-dir experiments/cape_kg_eacl_20260627 --chunk-file 01_data/evaluation_chunks.jsonl --conditions B0_plain_llm,P_cape_kg_actual --output-prefix qwen3_8b_strict_json_contract_smoke --max-chunks 4 --max-new-tokens 1200 --max-prompt-chars 3600 --strict-json-contract
```

Priority CSV: `experiments/cape_kg_eacl_20260627/05_review/strict_json_reprompt_priority.csv`

## Gate-Selected Row-Level Errors

Selected strict JSON run prefixes: qwen3_8b_strict_json_1200_full, qwen3_8b_strict_json_warn_top3_full_2400
Gate-selected error row CSV: `experiments/cape_kg_eacl_20260627/05_review/strict_json_gate_selected_error_rows.csv`
Gate-selected error rows: 661

Gate-selected issue class counts:

- invalid_numeric_literal: 1
- json_parse_error: 1
- malformed_json_delimiter: 2
- truncated_or_non_json_suffix: 657

## Historical Row-Level Error Worklist

Error row CSV: `experiments/cape_kg_eacl_20260627/05_review/strict_json_error_rows.csv`
Error rows across all strict-contract runs: 907

Issue class counts:

- invalid_numeric_literal: 1
- json_parse_error: 1
- malformed_json_delimiter: 3
- truncated_or_non_json_suffix: 902

## All Executed Strict-Contract Runs

- `experiments/cape_kg_eacl_20260627/48_qwen3_8b_strict_json_1200_full_raw.jsonl` gate-selected: raw_rows=1560, strict_error_rows=569, partial_json_repaired_rows=569, unrepaired_error_rows=0
  - B0_plain_llm: raw_rows=120, strict_error_rate=0.133333, repaired_rate=0.133333, unrepaired_rate=0.0
  - B1_predicate_constrained: raw_rows=120, strict_error_rate=0.141667, repaired_rate=0.141667, unrepaired_rate=0.0
  - B2_current_project: raw_rows=120, strict_error_rate=0.525, repaired_rate=0.525, unrepaired_rate=0.0
  - B3_edc_style: raw_rows=120, strict_error_rate=0.491667, repaired_rate=0.491667, unrepaired_rate=0.0
  - B4_taxonomy_rag: raw_rows=120, strict_error_rate=0.633333, repaired_rate=0.633333, unrepaired_rate=0.0
  - B5_procedural_prompt: raw_rows=120, strict_error_rate=0.633333, repaired_rate=0.633333, unrepaired_rate=0.0
  - P_cape_kg_actual: raw_rows=120, strict_error_rate=0.358333, repaired_rate=0.358333, unrepaired_rate=0.0
  - P_minus_CQ: raw_rows=120, strict_error_rate=0.4, repaired_rate=0.4, unrepaired_rate=0.0
  - P_minus_Evidence: raw_rows=120, strict_error_rate=0.325, repaired_rate=0.325, unrepaired_rate=0.0
  - P_minus_Procedural_schema: raw_rows=120, strict_error_rate=0.35, repaired_rate=0.35, unrepaired_rate=0.0
  - P_minus_Schema_retrieval: raw_rows=120, strict_error_rate=0.258333, repaired_rate=0.258333, unrepaired_rate=0.0
  - P_minus_Standard_bridge: raw_rows=120, strict_error_rate=0.133333, repaired_rate=0.133333, unrepaired_rate=0.0
  - P_minus_Validator: raw_rows=120, strict_error_rate=0.358333, repaired_rate=0.358333, unrepaired_rate=0.0
- `experiments/cape_kg_eacl_20260627/48_qwen3_8b_strict_json_contract_smoke_raw.jsonl`: raw_rows=16, strict_error_rows=15, partial_json_repaired_rows=15, unrepaired_error_rows=0
  - P_cape_kg_actual: raw_rows=4, strict_error_rate=1.0, repaired_rate=1.0, unrepaired_rate=0.0
  - P_minus_CQ: raw_rows=4, strict_error_rate=1.0, repaired_rate=1.0, unrepaired_rate=0.0
  - P_minus_Schema_retrieval: raw_rows=4, strict_error_rate=0.75, repaired_rate=0.75, unrepaired_rate=0.0
  - P_minus_Validator: raw_rows=4, strict_error_rate=1.0, repaired_rate=1.0, unrepaired_rate=0.0
- `experiments/cape_kg_eacl_20260627/48_qwen3_8b_strict_json_nothink_1200_smoke_raw.jsonl`: raw_rows=8, strict_error_rows=0, partial_json_repaired_rows=0, unrepaired_error_rows=0
  - P_cape_kg_actual: raw_rows=2, strict_error_rate=0.0, repaired_rate=0.0, unrepaired_rate=0.0
  - P_minus_CQ: raw_rows=2, strict_error_rate=0.0, repaired_rate=0.0, unrepaired_rate=0.0
  - P_minus_Schema_retrieval: raw_rows=2, strict_error_rate=0.0, repaired_rate=0.0, unrepaired_rate=0.0
  - P_minus_Validator: raw_rows=2, strict_error_rate=0.0, repaired_rate=0.0, unrepaired_rate=0.0
- `experiments/cape_kg_eacl_20260627/48_qwen3_8b_strict_json_nothink_smoke_raw.jsonl`: raw_rows=16, strict_error_rows=16, partial_json_repaired_rows=16, unrepaired_error_rows=0
  - P_cape_kg_actual: raw_rows=4, strict_error_rate=1.0, repaired_rate=1.0, unrepaired_rate=0.0
  - P_minus_CQ: raw_rows=4, strict_error_rate=1.0, repaired_rate=1.0, unrepaired_rate=0.0
  - P_minus_Schema_retrieval: raw_rows=4, strict_error_rate=1.0, repaired_rate=1.0, unrepaired_rate=0.0
  - P_minus_Validator: raw_rows=4, strict_error_rate=1.0, repaired_rate=1.0, unrepaired_rate=0.0
- `experiments/cape_kg_eacl_20260627/48_qwen3_8b_strict_json_warn_top3_full_1200_raw.jsonl`: raw_rows=360, strict_error_rows=215, partial_json_repaired_rows=215, unrepaired_error_rows=0
  - B2_current_project: raw_rows=120, strict_error_rate=0.525, repaired_rate=0.525, unrepaired_rate=0.0
  - B4_taxonomy_rag: raw_rows=120, strict_error_rate=0.633333, repaired_rate=0.633333, unrepaired_rate=0.0
  - B5_procedural_prompt: raw_rows=120, strict_error_rate=0.633333, repaired_rate=0.633333, unrepaired_rate=0.0
- `experiments/cape_kg_eacl_20260627/48_qwen3_8b_strict_json_warn_top3_full_2400_raw.jsonl` gate-selected: raw_rows=360, strict_error_rows=92, partial_json_repaired_rows=92, unrepaired_error_rows=0
  - B2_current_project: raw_rows=120, strict_error_rate=0.15, repaired_rate=0.15, unrepaired_rate=0.0
  - B4_taxonomy_rag: raw_rows=120, strict_error_rate=0.291667, repaired_rate=0.291667, unrepaired_rate=0.0
  - B5_procedural_prompt: raw_rows=120, strict_error_rate=0.325, repaired_rate=0.325, unrepaired_rate=0.0
- `experiments/cape_kg_eacl_20260627/48_qwen3_8b_strict_json_warn_top3_smoke_1200_raw.jsonl`: raw_rows=12, strict_error_rows=0, partial_json_repaired_rows=0, unrepaired_error_rows=0
  - B2_current_project: raw_rows=4, strict_error_rate=0.0, repaired_rate=0.0, unrepaired_rate=0.0
  - B4_taxonomy_rag: raw_rows=4, strict_error_rate=0.0, repaired_rate=0.0, unrepaired_rate=0.0
  - B5_procedural_prompt: raw_rows=4, strict_error_rate=0.0, repaired_rate=0.0, unrepaired_rate=0.0
