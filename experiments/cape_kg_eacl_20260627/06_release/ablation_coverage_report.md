# CAPE-KG Ablation Coverage Report

Generated: 2026-06-29T18:55:40.395631+00:00
Claim status: `ablation_coverage_ready_silver_diagnostic_not_human_gold`

## Purpose

이 문서는 revised plan에서 요구한 baseline/ablation 실험이 현재 산출물에서 어떤 조건과 파일로 구현되었는지 확인하는 release artifact입니다.

## Claim Boundary

- Silver diagnostic only: True
- Not human-gold performance evidence: True
- Safe interpretation: This report proves that planned baseline/ablation conditions were generated and evaluated with silver/proxy diagnostics. It does not prove final superiority or human-gold performance.
- Not claimable until: adjudicated human-gold labels, IAA, proposed-vs-ablation human-gold scoring, and active-review human effort returns are imported.

## Coverage Summary

| item | value |
| --- | --- |
| Baseline conditions | 7 |
| Baseline ready conditions | 7 |
| Planned LLM ablations | 6 |
| Completed LLM ablations | 6 |
| LLM ablation rows all >=100 | yes |
| Statistical comparison ablations | 6 |
| Active-review ablation present | yes |
| Active-review diagnostic rows | 24 |
| Minimum baseline requirement satisfied | yes |
| Minimum ablation requirement satisfied | yes |

## Baseline Coverage

| condition | valid_rows | metric_rows | edge_f1 | predicate_f1 | node_f1 | evidence_f1 |
| --- | --- | --- | --- | --- | --- | --- |
| B0_plain_llm | 120 | 120 | 0.000000 | 0.000000 | 0.034975 | 0.023925 |
| B1_predicate_constrained | 120 | 120 | 0.000000 | 0.141553 | 0.000000 | 0.029059 |
| B2_current_project | 120 | 120 | 0.000000 | 0.006839 | 0.021542 | 0.050274 |
| B3_edc_style | 120 | 120 | 0.000000 | 0.011893 | 0.019573 | 0.031098 |
| B4_taxonomy_rag | 120 | 120 | 0.000000 | 0.010511 | 0.029974 | 0.064055 |
| B5_procedural_prompt | 120 | 120 | 0.000960 | 0.009597 | 0.027420 | 0.060257 |
| B6_sac_kg_verifier_pruner | 120 | 120 | 0.001720 | 0.077386 | 0.056352 | 0.100771 |

## LLM Component Ablations

| condition | removed | valid_rows | metric_rows | nodes | edges | mappings | edge_f1 | predicate_f1 | evidence_f1 | stat_test |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P_minus_CQ | Competency-question anchoring | 120 | 120 | 586 | 391 | 233 | 0.000000 | 0.033793 | 0.068178 | yes |
| P_minus_Evidence | Evidence grounding requirement | 120 | 120 | 574 | 383 | 227 | 0.000899 | 0.054856 | 0.066594 | yes |
| P_minus_Procedural_schema | Procedural schema constraints | 120 | 120 | 558 | 353 | 212 | 0.003617 | 0.097649 | 0.068724 | yes |
| P_minus_Schema_retrieval | Chunk-specific CQ/schema/taxonomy retrieval | 120 | 120 | 568 | 417 | 216 | 0.000880 | 0.073031 | 0.059804 | yes |
| P_minus_Standard_bridge | NCS/PCF standard bridge output | 120 | 120 | 577 | 405 | 0 | 0.000868 | 0.071211 | 0.059004 | yes |
| P_minus_Validator | Validator rejection/pruning | 120 | 120 | 570 | 375 | 229 | 0.001789 | 0.045617 | 0.065932 | yes |

## Active-Review Ablation Diagnostic

Active-review rows are review-priority diagnostics only. They do not claim human review efficiency until timing/correction returns are imported.

| condition | strategy | budget | reviewed | errors_found | precision | recall | lift |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P_cape_kg_actual_with_active_review | active_priority | 10 | 10 | 10.000000 | 1.000000 | 0.036630 | 1.007326 |
| P_minus_Active_review_random_expected | random_expected | 10 | 10 | 9.927273 | 0.992727 | 0.036364 | 1.000000 |
| P_minus_Active_review_uncertainty_only | uncertainty_only | 10 | 10 | 10.000000 | 1.000000 | 0.036630 | 1.007326 |
| P_cape_kg_actual_with_active_review | active_priority | 25 | 25 | 25.000000 | 1.000000 | 0.091575 | 1.007326 |
| P_minus_Active_review_random_expected | random_expected | 25 | 25 | 24.818182 | 0.992727 | 0.090909 | 1.000000 |
| P_minus_Active_review_uncertainty_only | uncertainty_only | 25 | 25 | 25.000000 | 1.000000 | 0.091575 | 1.007326 |
| P_cape_kg_actual_with_active_review | active_priority | 55 | 55 | 55.000000 | 1.000000 | 0.201465 | 1.007326 |
| P_minus_Active_review_random_expected | random_expected | 55 | 55 | 54.600000 | 0.992727 | 0.200000 | 1.000000 |
| P_minus_Active_review_uncertainty_only | uncertainty_only | 55 | 55 | 55.000000 | 1.000000 | 0.201465 | 1.007326 |
| P_cape_kg_actual_with_active_review | active_priority | 100 | 100 | 100.000000 | 1.000000 | 0.366300 | 1.007326 |
| P_minus_Active_review_random_expected | random_expected | 100 | 100 | 99.272727 | 0.992727 | 0.363636 | 1.000000 |
| P_minus_Active_review_uncertainty_only | uncertainty_only | 100 | 100 | 100.000000 | 1.000000 | 0.366300 | 1.007326 |
| P_cape_kg_actual_with_active_review | active_priority | 10 | 10 | 6.000000 | 0.600000 | 0.034682 | 0.953757 |
| P_minus_Active_review_random_expected | random_expected | 10 | 10 | 6.290909 | 0.629091 | 0.036364 | 1.000000 |
| P_minus_Active_review_uncertainty_only | uncertainty_only | 10 | 10 | 6.000000 | 0.600000 | 0.034682 | 0.953757 |
| P_cape_kg_actual_with_active_review | active_priority | 25 | 25 | 16.000000 | 0.640000 | 0.092486 | 1.017341 |
| P_minus_Active_review_random_expected | random_expected | 25 | 25 | 15.727273 | 0.629091 | 0.090909 | 1.000000 |
| P_minus_Active_review_uncertainty_only | uncertainty_only | 25 | 25 | 15.000000 | 0.600000 | 0.086705 | 0.953757 |
| P_cape_kg_actual_with_active_review | active_priority | 55 | 55 | 36.000000 | 0.654545 | 0.208092 | 1.040462 |
| P_minus_Active_review_random_expected | random_expected | 55 | 55 | 34.600000 | 0.629091 | 0.200000 | 1.000000 |
| P_minus_Active_review_uncertainty_only | uncertainty_only | 55 | 55 | 38.000000 | 0.690909 | 0.219653 | 1.098266 |
| P_cape_kg_actual_with_active_review | active_priority | 100 | 100 | 56.000000 | 0.560000 | 0.323699 | 0.890173 |
| P_minus_Active_review_random_expected | random_expected | 100 | 100 | 62.909091 | 0.629091 | 0.363636 | 1.000000 |
| P_minus_Active_review_uncertainty_only | uncertainty_only | 100 | 100 | 72.000000 | 0.720000 | 0.416185 | 1.144509 |

## Input Files

- prompt_node_edge_traceability: `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.json`
- actual_llm_silver_metrics: `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json`
- statistical_analysis_metrics: `experiments/cape_kg_eacl_20260627/04_evaluation/statistical_analysis_metrics.json`
- active_review_ablation_metrics: `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_ablation_metrics.json`
- schema_retrieval_coverage_report: `experiments/cape_kg_eacl_20260627/06_release/schema_retrieval_coverage_report.json`

## Output Files

- JSON: `experiments/cape_kg_eacl_20260627/06_release/ablation_coverage_report.json`
- Markdown: `experiments/cape_kg_eacl_20260627/06_release/ablation_coverage_report.md`
- CSV: `experiments/cape_kg_eacl_20260627/04_evaluation/ablation_coverage_by_condition.csv`
