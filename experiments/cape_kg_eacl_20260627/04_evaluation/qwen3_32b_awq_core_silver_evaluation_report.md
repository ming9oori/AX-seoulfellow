# Actual LLM Silver Evaluation

Generated: 2026-06-28T08:33:25.976067+00:00

This report scores actual LLM generations against the silver reference derived from the current KG.
It is useful for debugging and relative sanity checks, but it is not a substitute for human-gold evaluation.

## Summary

| source file | condition | rows | edges | exact F1 | predicate F1 | node F1 | evidence F1 | repair rows | parse/error rows |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 49_qwen3_32b_awq_core_120_valid.jsonl | B0_plain_llm | 120 | 0 | 0.0 | 0.0 | 0.037736 | 0.027304 | 59 | 59 |
| 49_qwen3_32b_awq_core_120_valid.jsonl | B1_predicate_constrained | 120 | 585 | 0.001569 | 0.116078 | 0.0 | 0.022435 | 63 | 63 |
| 49_qwen3_32b_awq_core_120_valid.jsonl | B2_current_project | 120 | 56 | 0.0 | 0.009896 | 0.019359 | 0.03871 | 100 | 100 |
| 49_qwen3_32b_awq_core_120_valid.jsonl | P_cape_kg_actual | 120 | 360 | 0.003441 | 0.066237 | 0.02835 | 0.054153 | 113 | 113 |

## Interpretation Notes

- `edge_exact_f1` requires exact normalized subject label, predicate, and object label match within the same chunk.
- `predicate_f1` ignores subject/object labels and measures whether the same CAPE predicate types appear in each chunk.
- `node_label_f1` compares predicted node/triple labels with reference source/target labels within each chunk.
- `evidence_f1` compares sentence/evidence IDs used by the model with reference evidence IDs in the same chunk.
- High `partial_json_repaired_rows` means the raw generation was truncated or malformed but complete arrays were salvaged for audit.

- CSV: `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_32b_awq_core_silver_metrics.csv`
- JSON: `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_32b_awq_core_silver_metrics.json`
