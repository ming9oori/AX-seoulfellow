# Actual LLM Silver Evaluation

Generated: 2026-06-27T23:33:26.572518+00:00

This report scores actual LLM generations against the silver reference derived from the current KG.
It is useful for debugging and relative sanity checks, but it is not a substitute for human-gold evaluation.

## Summary

| source file | condition | rows | edges | exact F1 | predicate F1 | node F1 | evidence F1 | repair rows | parse/error rows |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 49_qwen3_8b_b2_b4_condition_baselines_120_valid.jsonl | B2_current_project | 120 | 82 | 0.0 | 0.006839 | 0.021542 | 0.050274 | 97 | 97 |
| 49_qwen3_8b_b2_b4_condition_baselines_120_valid.jsonl | B4_taxonomy_rag | 120 | 128 | 0.0 | 0.010511 | 0.029974 | 0.064055 | 102 | 102 |
| 49_qwen3_8b_cape_ablation_120_valid.jsonl | P_cape_kg_actual | 120 | 275 | 0.001786 | 0.048214 | 0.032597 | 0.065527 | 113 | 113 |
| 49_qwen3_8b_cape_ablation_120_valid.jsonl | P_minus_CQ | 120 | 284 | 0.0 | 0.033793 | 0.028546 | 0.068178 | 117 | 117 |
| 49_qwen3_8b_cape_ablation_120_valid.jsonl | P_minus_Evidence | 120 | 259 | 0.000899 | 0.054856 | 0.029703 | 0.066594 | 103 | 103 |
| 49_qwen3_8b_cape_ablation_120_valid.jsonl | P_minus_Procedural_schema | 120 | 247 | 0.003617 | 0.097649 | 0.030058 | 0.068724 | 107 | 107 |
| 49_qwen3_8b_cape_ablation_120_valid.jsonl | P_minus_Standard_bridge | 120 | 338 | 0.000868 | 0.071211 | 0.021324 | 0.059004 | 59 | 59 |
| 49_qwen3_8b_cape_ablation_120_valid.jsonl | P_minus_Validator | 120 | 271 | 0.001789 | 0.045617 | 0.029864 | 0.065932 | 110 | 110 |
| 49_qwen3_8b_condition_baselines_120_valid.jsonl | B0_plain_llm | 120 | 0 | 0.0 | 0.0 | 0.034975 | 0.023925 | 63 | 63 |
| 49_qwen3_8b_condition_baselines_120_valid.jsonl | B1_predicate_constrained | 120 | 663 | 0.0 | 0.141553 | 0.0 | 0.029059 | 63 | 63 |
| 49_qwen3_8b_condition_baselines_120_valid.jsonl | B5_procedural_prompt | 120 | 119 | 0.00096 | 0.009597 | 0.02742 | 0.060257 | 96 | 96 |
| 49_qwen3_8b_edc_schema_ablation_valid.jsonl | B3_edc_style | 120 | 53 | 0.0 | 0.011893 | 0.019573 | 0.031098 | 98 | 99 |
| 49_qwen3_8b_edc_schema_ablation_valid.jsonl | P_minus_Schema_retrieval | 120 | 308 | 0.00088 | 0.073031 | 0.021797 | 0.059804 | 109 | 109 |
| 49_sac_kg_verifier_pruner_baseline_valid.jsonl | B6_sac_kg_verifier_pruner | 120 | 361 | 0.00172 | 0.077386 | 0.056352 | 0.100771 | 0 | 0 |

## Interpretation Notes

- `edge_exact_f1` requires exact normalized subject label, predicate, and object label match within the same chunk.
- `predicate_f1` ignores subject/object labels and measures whether the same CAPE predicate types appear in each chunk.
- `node_label_f1` compares predicted node/triple labels with reference source/target labels within each chunk.
- `evidence_f1` compares sentence/evidence IDs used by the model with reference evidence IDs in the same chunk.
- High `partial_json_repaired_rows` means the raw generation was truncated or malformed but complete arrays were salvaged for audit.

- CSV: `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.csv`
- JSON: `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json`
