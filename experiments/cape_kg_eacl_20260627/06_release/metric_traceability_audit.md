# CAPE-KG Metric Traceability Audit

Generated: 2026-06-29T18:56:33.462770+00:00
Plan file: `AX_EACL_submission_review_revised_plan.md`

This report maps the revised plan's evaluation metrics to evaluator scripts, output files, protocol definitions, claim gates, and paper tables. It is a traceability audit, not final human-gold performance evidence.

## Claim Boundary

- Claim status: `metric_traceability_ready_pending_human_gold_and_expert_returns`
- Metric definitions and implementation paths are traceable.
- Final values remain pending human-gold, expert-review, or active-review effort returns.

## Summary

| metric | value |
| --- | --- |
| metric_count | 10 |
| pending_metric_count | 10 |
| claimable_metric_count | 0 |
| metric_issue_count | 0 |
| metric_rows_with_issues | 0 |
| all_evaluator_scripts_present | yes |
| all_output_files_present | yes |
| all_paper_tables_present | yes |
| all_protocol_metrics_present | yes |
| all_required_gates_known | yes |
| claim_status | metric_traceability_ready_pending_human_gold_and_expert_returns |

## Metric Rows

| metric_id | metric_name | claim_status | required_gate_ids | protocol_groups | protocol_metrics | paper_tables | evaluator_scripts_present | output_files_present | issue_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M01_node_f1 | Node F1 | pending_human_returns | `gold.completed_chunks`, `gold.item_count`, `gold.iaa`, `llm.proposed_human_gold_score` | `human_gold_core` | `node_label_f1` | `T02_main_extraction_human_gold` | yes | yes | 0 |
| M02_edge_f1 | Edge F1 | pending_human_returns | `gold.completed_chunks`, `gold.item_count`, `gold.iaa`, `llm.proposed_human_gold_score` | `human_gold_core` | `edge_exact_f1`, `predicate_f1` | `T02_main_extraction_human_gold` | yes | yes | 0 |
| M03_evidence_exact_iou | Evidence Exact Match / IoU | pending_human_returns | `gold.completed_chunks`, `gold.item_count`, `gold.iaa`, `llm.proposed_human_gold_score` | `human_gold_core` | `evidence_exact_or_f1`, `component_span_exact_match`, `component_span_iou` | `T02_main_extraction_human_gold` | yes | yes | 0 |
| M04_unsupported_edge_rate | Unsupported Edge Rate | pending_human_returns | `gold.completed_chunks`, `gold.item_count`, `gold.iaa`, `llm.proposed_human_gold_score` | `human_gold_core` | `evidence_exact_or_f1` | `T02_main_extraction_human_gold` | yes | yes | 0 |
| M05_ontology_conformance | Ontology Conformance | pending_human_returns | `gold.completed_chunks`, `gold.item_count`, `llm.proposed_human_gold_score` | `structural` | `ontology_conformance` | `T03_cq_schema_ablation`, `T04_structural_cq_diagnostics` | yes | yes | 0 |
| M06_procedural_consistency | Procedural Consistency | pending_human_returns | `gold.completed_chunks`, `gold.item_count`, `llm.proposed_human_gold_score` | `structural` | `procedural_consistency` | `T04_structural_cq_diagnostics` | yes | yes | 0 |
| M07_cq_answerability | CQ Answerability | pending_human_returns | `gold.completed_chunks`, `gold.item_count`, `llm.proposed_human_gold_score` | `structural` | `cq_answerability` | `T03_cq_schema_ablation`, `T04_structural_cq_diagnostics` | yes | yes | 0 |
| M08_mapping_pk_mrr_ndcg | NCS/PCF Mapping P@K / MRR / nDCG | pending_human_returns | `mapping.expert_review` | `mapping_expert` | `hit_at_1`, `hit_at_5`, `precision_at_5`, `mrr`, `ndcg_at_10` | `T06_mapping_downstream` | yes | yes | 0 |
| M09_crosswalk_accept_utility | NCS-PCF Crosswalk Accept Rate / Utility | pending_human_returns | `crosswalk.expert_review` | `crosswalk_expert` | `expert_accept_rate`, `hit_at_1`, `hit_at_5`, `precision_at_10`, `mrr`, `ndcg_at_10`, `utility_grade_mean` | `T07_crosswalk_downstream` | yes | yes | 0 |
| M10_active_review_efficiency | Active Review Efficiency | pending_human_returns | `strong.active_review` | `active_review_effort` | `review_seconds`, `corrections_per_hour`, `high_impact_corrections_per_hour` | `T08_active_review_efficiency` | yes | yes | 0 |

## Source Artifacts

- `post_human_scoring_readiness`: `experiments/cape_kg_eacl_20260627/06_release/post_human_scoring_readiness.json`
- `evaluation_protocol_lock`: `experiments/cape_kg_eacl_20260627/06_release/evaluation_protocol_lock.json`
- `paper_table_blueprint`: `experiments/cape_kg_eacl_20260627/06_release/paper_table_blueprint.json`
- `claim_gate_report`: `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.json`
- `eacl_plan_compliance_matrix`: `experiments/cape_kg_eacl_20260627/06_release/eacl_plan_compliance_matrix.json`
