# CAPE-KG RQ-to-Evidence Matrix

Generated: 2026-06-29T18:55:48.142442+00:00
Plan: `AX_EACL_submission_review_revised_plan.md`
Experiment: `experiments/cape_kg_eacl_20260627`

이 문서는 revised EACL plan의 RQ1-RQ4가 현재 어떤 산출물과 평가 증거로 연결되는지 정리한 release artifact입니다.
자동 진단과 최종 논문 claim을 분리하기 위해, 각 RQ마다 현재 상태와 남은 human/expert 검수 단계를 같이 적었습니다.

## Summary

- rq_count: 4
- claim_ready_count: 0
- automatic_or_candidate_ready_count: 4
- human_or_expert_pending_count: 4
- missing_required_evidence_files: 0
- readiness_claim_status: pending_human_gold_iaa_and_human_gold_scoring

## RQ Matrix

| RQ | 연구질문 | 현재 상태 | 최종 claim 가능 여부 | 핵심 증거 | 남은 단계 |
| --- | --- | --- | --- | --- | --- |
| RQ1 | 한국어 장문 업무 문서에서 Task, ProcedureStep, DecisionGateway, GuardCondition, ArtifactFlow를 추출할 때 evidence-span grounding을 강제하면 unsupported triple과 hallucination을 줄일 수 있는가? | `automatic_diagnostic_ready_human_gold_pending` | no | `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json`, `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_evaluation_report.md`, `experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_metrics.json`, `experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_report.md`, +3 more | Complete two-annotator labeling and adjudication for at least 100 chunks.<br>Adjudicate enough nodes, edges, and evidence anchors to reach 500 gold items.<br>Import completed annotator A/B files and recompute IAA.<br>Score P_cape_kg_actual against adjudicated human gold after gold completion. |
| RQ2 | Competency Question을 schema selection, LLM extraction, validation, evaluation의 anchor로 사용할 때 ontology conformance와 CQ answerability가 향상되는가? | `structural_diagnostic_ready_human_gold_pending` | no | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json`, `outputs/03_schema/competency_questions.json`, `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_metrics.json`, `experiments/cape_kg_eacl_20260627/04_evaluation/ontology_conformance_metrics.json`, +4 more | Complete two-annotator labeling and adjudication for at least 100 chunks.<br>Adjudicate enough nodes, edges, and evidence anchors to reach 500 gold items.<br>Import completed annotator A/B files and recompute IAA.<br>Score P_cape_kg_actual against adjudicated human gold after gold completion. |
| RQ3 | Layer2 procedural KG가 NCS/PCF 표준 taxonomy mapping의 downstream 성능을 향상시키는가? | `candidate_pipeline_ready_expert_review_pending` | no | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl`, `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl`, `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_results.csv`, `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_arm_rerank_summary.json`, +5 more | Complete expert review for mapping candidates and crosswalk candidates before making P@K/MRR/nDCG@10, explanation-quality, accept-rate, or utility claims.<br>Complete NCS-PCF crosswalk expert review and recompute accept-rate, Hit@K, P@10, MRR, nDCG@10, utility, and explanation-quality metrics. |
| RQ4 | Evidence verifier와 active review queue가 전문가 검수 비용을 줄이면서 KG 품질을 높이는가? | `review_queue_ready_human_effort_pending` | no | `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_efficiency_metrics.json`, `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_efficiency_report.md`, `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_ablation_metrics.json`, `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_human_effort_metrics.json`, +7 more | Collect reviewed active-review human-effort CSV and validate efficiency against human adjudication outcomes. |

## RQ1. Evidence-grounded procedural KG extraction

- Question: 한국어 장문 업무 문서에서 Task, ProcedureStep, DecisionGateway, GuardCondition, ArtifactFlow를 추출할 때 evidence-span grounding을 강제하면 unsupported triple과 hallucination을 줄일 수 있는가?
- Current status: `automatic_diagnostic_ready_human_gold_pending`
- Claim ready: no
- Claim scope: Final extraction quality claims require adjudicated human-gold nodes, edges, and evidence spans.

### Plan Metrics

- Node F1
- Edge F1
- Evidence Exact Match
- Evidence IoU
- Unsupported Edge Rate

### Current Values

- final_layer2_nodes: `220`
- final_layer2_edges: `947`
- evidence_missing_edge_count: `0`
- dangling_edge_count: `0`
- component_span_claim_status: `automatic_component_span_diagnostic_not_human_gold`
- component_count: `2841`
- exact_component_span_rate: `0.261176`
- predicate_full_sentence_proxy_rate: `1.0`
- proposed_silver_edge_f1: `0.001786`
- proposed_silver_evidence_f1: `0.065527`
- human_gold_completed_chunks: `0`
- human_gold_items: `0`

### Evidence Files

| role | path | exists |
| --- | --- | --- |
| silver/proxy extraction diagnostics | `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json` | True |
| silver/proxy extraction report | `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_evaluation_report.md` | True |
| component span diagnostic | `experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_metrics.json` | True |
| component span report | `experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_report.md` | True |
| component span handoff | `outputs/06_triples/layer2_triples_component_spans.jsonl` | True |
| human-gold scoring placeholder | `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_metrics.json` | True |
| human-gold completion state | `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_validation_summary.json` | True |

### Remaining For Final Claim

- Complete two-annotator labeling and adjudication for at least 100 chunks.
- Adjudicate enough nodes, edges, and evidence anchors to reach 500 gold items.
- Import completed annotator A/B files and recompute IAA.
- Score P_cape_kg_actual against adjudicated human gold after gold completion.

## RQ2. CQ-anchored schema control

- Question: Competency Question을 schema selection, LLM extraction, validation, evaluation의 anchor로 사용할 때 ontology conformance와 CQ answerability가 향상되는가?
- Current status: `structural_diagnostic_ready_human_gold_pending`
- Claim ready: no
- Claim scope: Structural conformance can be reported as an automatic diagnostic; final quality improvements require human-gold scoring.

### Plan Metrics

- Ontology Conformance
- Procedural Consistency
- CQ Answerability
- Ablation: P - CQ
- Ablation: P - Schema retrieval
- Ablation: P - Validator

### Current Values

- cq_count: `12`
- ontology_conformance_rate: `1.0`
- domain_range_violation_count: `0`
- procedural_consistency_rate: `0.995283`
- procedural_consistency_issue_count: `4`
- cq_answerability_rate: `1.0`
- ablation_conditions_available: `['P_minus_CQ', 'P_minus_Procedural_schema', 'P_minus_Schema_retrieval', 'P_minus_Validator']`

### Evidence Files

| role | path | exists |
| --- | --- | --- |
| experiment CQ inventory | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` | True |
| internal build CQ inventory | `outputs/03_schema/competency_questions.json` | True |
| combined structural metrics | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_metrics.json` | True |
| ontology conformance metrics | `experiments/cape_kg_eacl_20260627/04_evaluation/ontology_conformance_metrics.json` | True |
| procedural consistency metrics | `experiments/cape_kg_eacl_20260627/04_evaluation/procedural_consistency_metrics.json` | True |
| CQ answerability metrics | `experiments/cape_kg_eacl_20260627/04_evaluation/cq_answerability_structural_metrics.json` | True |
| CQ answerability by LLM condition | `experiments/cape_kg_eacl_20260627/04_evaluation/cq_answerability_by_condition.csv` | True |
| prompt/CQ/node-edge traceability | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.json` | True |

### Remaining For Final Claim

- Complete two-annotator labeling and adjudication for at least 100 chunks.
- Adjudicate enough nodes, edges, and evidence anchors to reach 500 gold items.
- Import completed annotator A/B files and recompute IAA.
- Score P_cape_kg_actual against adjudicated human gold after gold completion.

## RQ3. Standard taxonomy bridge

- Question: Layer2 procedural KG가 NCS/PCF 표준 taxonomy mapping의 downstream 성능을 향상시키는가?
- Current status: `candidate_pipeline_ready_expert_review_pending`
- Claim ready: no
- Claim scope: Candidate generation and rerank diagnostics are ready; downstream mapping performance claims require expert review.

### Plan Metrics

- NCS/PCF Mapping P@K
- P@1
- P@5
- MRR
- nDCG@10
- Expert accept rate
- Explanation quality score

### Current Values

- ncs_mapping_candidates: `110`
- pcf_mapping_candidates: `110`
- mapping_completed_rows: `0`
- mapping_pending_rows: `220`
- mapping_claim_status: `pending_or_partial_expert_review`
- crosswalk_candidate_rows: `220`
- crosswalk_source_task_count: `22`
- crosswalk_completed_rows: `0`
- crosswalk_pending_rows: `220`
- crosswalk_claim_status: `pending_crosswalk_expert_review`

### Evidence Files

| role | path | exists |
| --- | --- | --- |
| Layer2-to-NCS mapping candidates | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` | True |
| Layer2-to-PCF mapping candidates | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` | True |
| mapping downstream arm diagnostics | `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_results.csv` | True |
| mapping rerank summary | `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_arm_rerank_summary.json` | True |
| Layer2-bridged crosswalk candidates | `experiments/cape_kg_eacl_20260627/04_evaluation/ncs_pcf_crosswalk_summary.json` | True |
| expert-review metric placeholder | `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_expert_metrics.json` | True |
| NCS-PCF crosswalk expert-review metric placeholder | `experiments/cape_kg_eacl_20260627/04_evaluation/crosswalk_expert_metrics.json` | True |
| NCS-PCF crosswalk expert-review manifest | `experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_manifest.json` | True |
| expert review progress | `experiments/cape_kg_eacl_20260627/06_release/mapping_review_progress_summary.json` | True |

### Remaining For Final Claim

- Complete expert review for mapping candidates and crosswalk candidates before making P@K/MRR/nDCG@10, explanation-quality, accept-rate, or utility claims.
- Complete NCS-PCF crosswalk expert review and recompute accept-rate, Hit@K, P@10, MRR, nDCG@10, utility, and explanation-quality metrics.

## RQ4. Human review efficiency

- Question: Evidence verifier와 active review queue가 전문가 검수 비용을 줄이면서 KG 품질을 높이는가?
- Current status: `review_queue_ready_human_effort_pending`
- Claim ready: no
- Claim scope: Silver/proxy prioritization and human-effort templates are ready; review-cost claims require completed human timing/correction returns.

### Plan Metrics

- Active Review Efficiency
- Corrected high-impact errors per hour
- Precision@K
- Recall@K
- Lift vs random review
- Ablation: P - Active review

### Current Values

- active_review_claim_status: `silver_proxy_not_human_review_efficiency`
- candidate_count: `275`
- silver_proxy_high_impact_error_count: `173`
- human_effort_claim_status: `ready_for_human_effort_collection`
- human_effort_reviewed_file_present: `False`
- human_effort_pooled_rows: `204`
- human_effort_arm_counts: `{'active_priority': 100, 'uncertainty_only': 100, 'random_control': 100}`
- human_effort_briefing_claim_status: `review_navigation_only_pending_human_effort`
- human_effort_briefing_rows: `204`

### Evidence Files

| role | path | exists |
| --- | --- | --- |
| silver/proxy active review diagnostic | `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_efficiency_metrics.json` | True |
| silver/proxy active review report | `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_efficiency_report.md` | True |
| active-review ablation diagnostic | `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_ablation_metrics.json` | True |
| human-effort collection state | `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_human_effort_metrics.json` | True |
| human-effort report | `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_human_effort_report.md` | True |
| human-effort briefing summary | `experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_briefing.json` | True |
| human-effort briefing | `experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_briefing.md` | True |
| active review queue | `experiments/cape_kg_eacl_20260627/05_review/actual_llm_active_review_queue_P_cape_kg_actual.csv` | True |
| human-effort return template | `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort_template.csv` | True |
| human-effort review navigation CSV | `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort_briefing.csv` | True |
| human-effort protocol | `experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_plan.md` | True |

### Remaining For Final Claim

- Collect reviewed active-review human-effort CSV and validate efficiency against human adjudication outcomes.

## Missing Required Evidence Files

- None

## Interpretation

- RQ1/RQ2는 자동 구조 진단과 silver/proxy LLM 진단이 준비된 상태입니다.
- RQ3는 NCS/PCF mapping 후보와 downstream scaffold가 준비되었지만 expert review 전입니다.
- RQ4는 active review queue와 human-effort template이 준비되었지만 실제 human timing/correction 결과 전입니다.
- 네 RQ 모두 최종 성능 claim은 human-gold, IAA, adjudication 또는 expert review 이후에만 가능합니다.
