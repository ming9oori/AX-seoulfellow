# CAPE-KG CQ-Linked Schema Retrieval Coverage

Generated: 2026-06-29T18:55:34.330653+00:00
Claim status: `schema_retrieval_coverage_ready_silver_diagnostic_not_human_gold`

## Purpose

이 문서는 revised plan의 M3 `CQ-linked schema retrieval`가 실험 산출물 안에서 어떻게 구현/제거/비교되었는지를 독립적으로 점검하는 release artifact입니다.

## Claim Boundary

- Silver diagnostic only: True
- Not human-gold performance evidence: True
- Safe interpretation: This report checks method coverage, output shape, and silver proxy diagnostics for schema retrieval. It does not claim final precision, recall, F1, or human-gold CQ answerability.
- Not claimable until: adjudicated human-gold annotations, IAA, and human-gold scoring are imported for the proposed and ablation conditions.

## Schema and CQ Inventory

| item | value |
| --- | --- |
| CQ count | 12 |
| All CQs have target predicates | yes |
| Node types | 14 |
| Edge types | 17 |
| Domain-range rules | 17 |
| Evidence span required | yes |

## Condition Policy

| condition | role | CQ | chunk_schema | taxonomy | full_schema | validator | output | prompt_file |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P_cape_kg_actual | proposed | yes | yes | yes | yes | yes | `nodes`, `edges`, `mappings` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/P_cape_kg.txt` |
| P_minus_Schema_retrieval | ablation | yes | no | no | yes | yes | `nodes`, `edges`, `mappings` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/P_minus_Schema_retrieval.txt` |
| B4_taxonomy_rag | baseline | no | yes | yes | no | no | `nodes`, `edges`, `mappings` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B4_taxonomy_rag_baseline.txt` |

## LLM Output Quantity From Traceability Files

| condition | valid_rows | nodes | edges | mappings |
| --- | --- | --- | --- | --- |
| P_cape_kg_actual | 120 | 576 | 373 | 227 |
| P_minus_Schema_retrieval | 120 | 568 | 417 | 216 |
| B4_taxonomy_rag | 120 | 719 | 323 | 126 |

## CQ Support Proxy

CQ support는 LLM valid JSONL의 edge predicate, mapping standard, evidence anchor 존재 여부를 기준으로 계산한 proxy입니다. 이는 human-gold answerability가 아닙니다.

| condition | cq_count | supported_cq_count | unsupported_cq_count | support_count_total | supporting_chunks_total |
| --- | --- | --- | --- | --- | --- |
| P_cape_kg_actual | 12 | 11 | 1 | 1770 | 430 |
| P_minus_Schema_retrieval | 12 | 11 | 1 | 1804 | 501 |
| B4_taxonomy_rag | 12 | 8 | 4 | 1607 | 335 |

Detailed CQ support CSV: `experiments/cape_kg_eacl_20260627/04_evaluation/schema_retrieval_cq_support_by_condition.csv`

## Silver Metric Diagnostic

아래 silver metric은 자동 reference와의 proxy 비교입니다. 최종 main table 수치가 아니며, adjudicated human-gold scoring 이후 재계산해야 합니다.

| condition | source_file | pred_nodes | pred_edges | pred_mappings | edge_exact_f1 | predicate_f1 | node_label_f1 | evidence_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B4_taxonomy_rag | 49_qwen3_8b_b2_b4_condition_baselines_120_valid.jsonl | 674 | 128 | 41 | 0.000000 | 0.010511 | 0.029974 | 0.064055 |
| P_minus_Schema_retrieval | 49_qwen3_8b_edc_schema_ablation_valid.jsonl | 566 | 308 | 25 | 0.000880 | 0.073031 | 0.021797 | 0.059804 |
| P_cape_kg_actual | 49_qwen3_8b_cape_ablation_120_valid.jsonl | 549 | 275 | 52 | 0.001786 | 0.048214 | 0.032597 | 0.065527 |

## P vs P_minus_Schema_retrieval Diagnostic Delta

| metric | left_condition | left_value | right_condition | right_value | delta_left_minus_right |
| --- | --- | --- | --- | --- | --- |
| pred_nodes | P_cape_kg_actual | 549.000000 | P_minus_Schema_retrieval | 566.000000 | -17.000000 |
| pred_edges | P_cape_kg_actual | 275.000000 | P_minus_Schema_retrieval | 308.000000 | -33.000000 |
| pred_mappings | P_cape_kg_actual | 52.000000 | P_minus_Schema_retrieval | 25.000000 | 27.000000 |
| edge_exact_f1 | P_cape_kg_actual | 0.001786 | P_minus_Schema_retrieval | 0.000880 | 0.000906 |
| predicate_f1 | P_cape_kg_actual | 0.048214 | P_minus_Schema_retrieval | 0.073031 | -0.024817 |
| node_label_f1 | P_cape_kg_actual | 0.032597 | P_minus_Schema_retrieval | 0.021797 | 0.010800 |
| evidence_f1 | P_cape_kg_actual | 0.065527 | P_minus_Schema_retrieval | 0.059804 | 0.005723 |
| schema_edge_rate | P_cape_kg_actual | 1.000000 | P_minus_Schema_retrieval | 1.000000 | 0.000000 |
| mapping_evidence_attachment_rate | P_cape_kg_actual | 1.000000 | P_minus_Schema_retrieval | 1.000000 | 0.000000 |

## Input Files

- prompt_node_edge_traceability: `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.json`
- competency_questions: `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json`
- cape_schema: `experiments/cape_kg_eacl_20260627/02_schema/cape_schema.json`
- actual_llm_silver_metrics: `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json`
- valid_output_file: `experiments/cape_kg_eacl_20260627/49_qwen3_8b_strict_json_1200_full_valid.jsonl`
- valid_output_file: `experiments/cape_kg_eacl_20260627/49_sac_kg_verifier_pruner_baseline_valid.jsonl`

## Output Files

- JSON: `experiments/cape_kg_eacl_20260627/06_release/schema_retrieval_coverage_report.json`
- Markdown: `experiments/cape_kg_eacl_20260627/06_release/schema_retrieval_coverage_report.md`
- CQ support CSV: `experiments/cape_kg_eacl_20260627/04_evaluation/schema_retrieval_cq_support_by_condition.csv`
