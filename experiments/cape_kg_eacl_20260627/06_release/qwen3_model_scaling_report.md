# CAPE-KG Qwen3 Model Scaling Report

Generated: 2026-06-29T18:56:35.511914+00:00
Experiment: `experiments/cape_kg_eacl_20260627`

This report consolidates the completed Qwen3-8B, Qwen3-14B, and Qwen3-32B-AWQ core diagnostics.
It is explicitly claim-safe: these are silver/proxy diagnostics and must not be presented as final human-gold performance.

## Summary

- Claim status: `qwen3_model_scaling_diagnostic_ready_not_human_gold`
- Models: Qwen3-8B, Qwen3-14B, Qwen3-32B-AWQ
- Core conditions: B0_plain_llm, B1_predicate_constrained, B2_current_project, P_cape_kg_actual
- Qwen3-32B-AWQ core run complete: `True`
- Qwen3-32B-AWQ raw/valid rows: 480 / 480
- Recommended next action: Qwen3-32B-AWQ core 120-chunk run is complete; use human-gold scoring before paper claims.

## Proposed-Method Model Scaling

| model | role | rows | pred edges | exact F1 | predicate F1 | node F1 | evidence F1 | parse/error rows | claim status |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3-8B | main local paper-package diagnostic | 120 | 275 | 0.0018 | 0.0482 | 0.0326 | 0.0655 | 113 | `silver_proxy_not_human_gold` |
| Qwen3-14B | stronger local core diagnostic | 120 | 332 | 0.0017 | 0.0601 | 0.0298 | 0.0610 | 113 | `silver_proxy_not_human_gold` |
| Qwen3-32B-AWQ | largest completed local core diagnostic | 120 | 360 | 0.0034 | 0.0662 | 0.0284 | 0.0542 | 113 | `silver_proxy_not_human_gold` |

## Core Condition Matrix

| model | condition | rows | pred edges | exact F1 | predicate F1 | node F1 | evidence F1 | parse/error rows |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen3-8B | `B0_plain_llm` | 120 | 0 | 0.0000 | 0.0000 | 0.0350 | 0.0239 | 63 |
| Qwen3-8B | `B1_predicate_constrained` | 120 | 663 | 0.0000 | 0.1416 | 0.0000 | 0.0291 | 63 |
| Qwen3-8B | `B2_current_project` | 120 | 82 | 0.0000 | 0.0068 | 0.0215 | 0.0503 | 97 |
| Qwen3-8B | `P_cape_kg_actual` | 120 | 275 | 0.0018 | 0.0482 | 0.0326 | 0.0655 | 113 |
| Qwen3-14B | `B0_plain_llm` | 120 | 0 | 0.0000 | 0.0000 | 0.0329 | 0.0259 | 68 |
| Qwen3-14B | `B1_predicate_constrained` | 120 | 641 | 0.0008 | 0.1105 | 0.0000 | 0.0246 | 75 |
| Qwen3-14B | `B2_current_project` | 120 | 60 | 0.0000 | 0.0079 | 0.0198 | 0.0394 | 102 |
| Qwen3-14B | `P_cape_kg_actual` | 120 | 332 | 0.0017 | 0.0601 | 0.0298 | 0.0610 | 113 |
| Qwen3-32B-AWQ | `B0_plain_llm` | 120 | 0 | 0.0000 | 0.0000 | 0.0377 | 0.0273 | 59 |
| Qwen3-32B-AWQ | `B1_predicate_constrained` | 120 | 585 | 0.0016 | 0.1161 | 0.0000 | 0.0224 | 63 |
| Qwen3-32B-AWQ | `B2_current_project` | 120 | 56 | 0.0000 | 0.0099 | 0.0194 | 0.0387 | 100 |
| Qwen3-32B-AWQ | `P_cape_kg_actual` | 120 | 360 | 0.0034 | 0.0662 | 0.0284 | 0.0542 | 113 |

## Interpretation

- All model-scaling scores are silver/proxy diagnostics, not human-gold performance evidence.
- Qwen3-32B-AWQ is the largest completed local core run and is already available for B0/B1/B2/P over 120 chunks.
- The 32B-AWQ run improves proposed-method silver predicate F1 and exact edge F1 over the 8B core diagnostic, but evidence F1 is lower than the 8B proposed diagnostic; do not overclaim monotonic model scaling.
- The next paper-level step is not another automatic GPU run; it is adjudicated human-gold scoring of the existing model outputs.

## Source Files

| role | path | exists | bytes |
| --- | --- | ---: | ---: |
| Qwen3-8B metrics | `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json` | True | 15122 |
| Qwen3-8B report | `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_evaluation_report.md` | True | 3152 |
| Qwen3-8B validated outputs | `experiments/cape_kg_eacl_20260627/49_qwen3_8b_strict_json_1200_full_valid.jsonl` | True | 2917290 |
| Qwen3-14B metrics | `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_14b_core_silver_metrics.json` | True | 4435 |
| Qwen3-14B report | `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_14b_core_silver_evaluation_report.md` | True | 1801 |
| Qwen3-14B validated outputs | `experiments/cape_kg_eacl_20260627/49_qwen3_14b_core_conditions_120_valid.jsonl` | True | 611457 |
| Qwen3-32B-AWQ metrics | `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_32b_awq_core_silver_metrics.json` | True | 4398 |
| Qwen3-32B-AWQ report | `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_32b_awq_core_silver_evaluation_report.md` | True | 1779 |
| Qwen3-32B-AWQ validated outputs | `experiments/cape_kg_eacl_20260627/49_qwen3_32b_awq_core_120_valid.jsonl` | True | 598007 |
| Qwen3-32B-AWQ readiness JSON | `experiments/cape_kg_eacl_20260627/06_release/qwen3_32b_awq_readiness.json` | True | 4010 |
| Qwen3-32B-AWQ readiness report | `experiments/cape_kg_eacl_20260627/06_release/qwen3_32b_awq_readiness.md` | True | 1916 |
