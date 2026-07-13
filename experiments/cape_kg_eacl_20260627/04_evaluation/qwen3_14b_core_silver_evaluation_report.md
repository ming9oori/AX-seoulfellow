# Actual LLM Silver Evaluation

Generated: 2026-06-27T23:03:10.294917+00:00

This report scores actual LLM generations against the silver reference derived from the current KG.
It is useful for debugging and relative sanity checks, but it is not a substitute for human-gold evaluation.

## Summary

| source file | condition | rows | edges | exact F1 | predicate F1 | node F1 | evidence F1 | repair rows | parse/error rows |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 49_qwen3_14b_core_conditions_120_valid.jsonl | B0_plain_llm | 120 | 0 | 0.0 | 0.0 | 0.032902 | 0.025904 | 68 | 68 |
| 49_qwen3_14b_core_conditions_120_valid.jsonl | B1_predicate_constrained | 120 | 641 | 0.000767 | 0.110514 | 0.0 | 0.024581 | 75 | 75 |
| 49_qwen3_14b_core_conditions_120_valid.jsonl | B2_current_project | 120 | 60 | 0.0 | 0.007901 | 0.019772 | 0.039356 | 102 | 102 |
| 49_qwen3_14b_core_conditions_120_valid.jsonl | P_cape_kg_actual | 120 | 332 | 0.001741 | 0.060078 | 0.029751 | 0.060955 | 113 | 113 |

## Interpretation Notes

- `edge_exact_f1` requires exact normalized subject label, predicate, and object label match within the same chunk.
- `predicate_f1` ignores subject/object labels and measures whether the same CAPE predicate types appear in each chunk.
- `node_label_f1` compares predicted node/triple labels with reference source/target labels within each chunk.
- `evidence_f1` compares sentence/evidence IDs used by the model with reference evidence IDs in the same chunk.
- High `partial_json_repaired_rows` means the raw generation was truncated or malformed but complete arrays were salvaged for audit.

- CSV: `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_14b_core_silver_metrics.csv`
- JSON: `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_14b_core_silver_metrics.json`
