# Actual LLM Silver Evaluation

Generated: 2026-06-28T06:03:20.304429+00:00

This report scores actual LLM generations against the silver reference derived from the current KG.
It is useful for debugging and relative sanity checks, but it is not a substitute for human-gold evaluation.

## Summary

| source file | condition | rows | edges | exact F1 | predicate F1 | node F1 | evidence F1 | repair rows | parse/error rows |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 49_qwen3_32b_awq_smoke_valid.jsonl | B0_plain_llm | 4 | 0 | 0.0 | 0.0 | 0.037037 | 0.062176 | 0 | 0 |
| 49_qwen3_32b_awq_smoke_valid.jsonl | P_cape_kg_actual | 4 | 17 | 0.0 | 0.111111 | 0.103448 | 0.169643 | 4 | 4 |

## Interpretation Notes

- `edge_exact_f1` requires exact normalized subject label, predicate, and object label match within the same chunk.
- `predicate_f1` ignores subject/object labels and measures whether the same CAPE predicate types appear in each chunk.
- `node_label_f1` compares predicted node/triple labels with reference source/target labels within each chunk.
- `evidence_f1` compares sentence/evidence IDs used by the model with reference evidence IDs in the same chunk.
- High `partial_json_repaired_rows` means the raw generation was truncated or malformed but complete arrays were salvaged for audit.

- CSV: `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_32b_awq_smoke_silver_metrics.csv`
- JSON: `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_32b_awq_smoke_silver_metrics.json`
