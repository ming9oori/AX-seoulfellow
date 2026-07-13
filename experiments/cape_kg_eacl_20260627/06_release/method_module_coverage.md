# CAPE-KG Method Module Coverage

Generated: 2026-06-29T18:55:40.195140+00:00

This file maps the revised EACL plan's M1-M11 modules to current executable artifacts. It distinguishes implementation evidence from paper-claim evidence.

## Summary

- Modules: 11
- Modules with required artifacts: 11
- Missing required artifacts: 0
- Human-dependent modules for final claims: 8
- Claim status: `all_m1_m11_artifacts_present_human_claims_pending`

## Module Table

| module | status | human-dependent claim | required artifacts | missing | remaining for paper claim |
|---|---|---:|---:|---:|---|
| M1 Document structure recovery | implemented_artifacts_present | no | 5 | 0 | No additional automatic step required; source-text release still requires rights review. |
| M2 CQ generation and selection | implemented_artifacts_present | no | 7 | 0 | Human-gold CQ answerability must be recomputed after adjudication. |
| M3 CQ-linked schema retrieval | implemented_artifacts_present_human_claim_pending | yes | 8 | 0 | Final claim requires human-gold comparison of P vs. schema-retrieval ablation. |
| M4 Procedural frame extraction | implemented_artifacts_present_human_claim_pending | yes | 6 | 0 | Human review should verify task/step correctness before final claims. |
| M5 Evidence-span constrained triple extraction | implemented_artifacts_present_human_claim_pending | yes | 28 | 0 | Component-level span diagnostics are present; character/span exactness must still be validated against adjudicated human gold. |
| M6 Span verifier | implemented_artifacts_present_human_claim_pending | yes | 15 | 0 | Current verifier evidence is silver/proxy; human-gold evidence metrics are pending. |
| M7 Ontology/SHACL validator | implemented_artifacts_present | no | 10 | 0 | No additional automatic step required; final conformance table should use human-gold predictions. |
| M8 Procedural consistency validator | implemented_artifacts_present_human_claim_pending | yes | 19 | 0 | Human-gold procedural consistency should be recomputed after adjudication. |
| M9 Alias/canonicalization module | implemented_artifacts_present_human_claim_pending | yes | 7 | 0 | Final node canonicalization quality requires human-gold node matching. |
| M10 Active review queue | implemented_artifacts_present_human_claim_pending | yes | 18 | 0 | Active-review ablation is represented with silver/proxy diagnostics; final efficiency claim requires human adjudication outcomes and reviewer effort/timing. |
| M11 NCS/PCF mapping evaluator | implemented_artifacts_present_human_claim_pending | yes | 13 | 0 | P@K/MRR/nDCG@10, explanation-quality, crosswalk accept-rate, and utility claims require completed expert review. |

## Artifact Evidence

### M1. Document structure recovery

- OK (required) `outputs/02_ocr/document_structure_reviewed.json` bytes=161394
- OK (required) `outputs/02_ocr/ocr_sentences_clean.jsonl` bytes=3198719, records=5009
- OK (required) `outputs/02_ocr/layer2_chunks.jsonl` bytes=1006690, records=214
- OK (required) `experiments/cape_kg_eacl_20260627/01_data/evaluation_chunks.jsonl` bytes=495269, records=120
- OK (required) `outputs/02_ocr/ocr_quality_report.md` bytes=1934

### M2. CQ generation and selection

- OK (required) `outputs/03_schema/competency_questions.json` bytes=2303
- OK (required) `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` bytes=2101
- OK (required) `outputs/10_evaluation/cq_answerability_report.md` bytes=1281
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/cq_answerability_by_condition.csv` bytes=12836, records=132
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/cq_query_sample_answers.csv` bytes=13328, records=60
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.json` bytes=53053
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md` bytes=29675

### M3. CQ-linked schema retrieval

- OK (required) `experiments/cape_kg_eacl_20260627/02_schema/cape_schema.json` bytes=3523
- OK (required) `experiments/cape_kg_eacl_20260627/02_schema/prompts/P_cape_kg.txt` bytes=206
- OK (required) `experiments/cape_kg_eacl_20260627/02_schema/prompts/P_minus_Schema_retrieval.txt` bytes=148
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/schema_retrieval_coverage_report.json` bytes=29213
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/schema_retrieval_coverage_report.md` bytes=5476
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/schema_retrieval_cq_support_by_condition.csv` bytes=6811, records=36
- OK (required) `experiments/cape_kg_eacl_20260627/49_qwen3_8b_cape_ablation_120_valid.jsonl` bytes=1021348, records=720
- OK (required) `experiments/cape_kg_eacl_20260627/50_qwen3_8b_cape_ablation_120_quality_report.md` bytes=1681

### M4. Procedural frame extraction

- OK (required) `outputs/04_task_frames/canonical_task_catalog.json` bytes=256506
- OK (required) `outputs/04_task_frames/task_frame_candidates_raw.jsonl` bytes=151608, records=22
- OK (required) `outputs/05_procedure/procedure_structures_clean.jsonl` bytes=37990, records=22
- OK (required) `outputs/05_procedure/procedure_edges.jsonl` bytes=96588, records=303
- OK (required) `outputs/04_task_frames/task_frame_quality_report.md` bytes=401
- OK (required) `outputs/05_procedure/procedure_quality_report.md` bytes=341

### M5. Evidence-span constrained triple extraction

- OK (required) `outputs/06_triples/layer2_triples_schema_valid.jsonl` bytes=1101975, records=947
- OK (required) `outputs/06_triples/layer2_triples_component_spans.jsonl` bytes=2684961, records=947
- OK (required) `outputs/06_triples/layer2_predicate_cue_spans.jsonl` bytes=572191, records=947
- OK (required) `outputs/06_triples/evidence_anchors.jsonl` bytes=1676699, records=5009
- OK (required) `outputs/13_evidence_graph/evidence_graph_projection_summary.json` bytes=1603
- OK (required) `outputs/13_evidence_graph/evidence_anchor_nodes.jsonl` bytes=225323, records=451
- OK (required) `outputs/13_evidence_graph/evidenced_by_edges.jsonl` bytes=2227213, records=3915
- OK (required) `outputs/13_evidence_graph/edge_component_span_links.jsonl` bytes=2278299, records=2841
- OK (required) `outputs/13_evidence_graph/edge_component_span_links.csv` bytes=1025037, records=2841
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_metrics.json` bytes=1822
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_report.md` bytes=1580
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/predicate_cue_span_metrics.json` bytes=5002
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/predicate_cue_span_report.md` bytes=1721
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/predicate_cue_span_rows.csv` bytes=255799, records=947
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/edge_component_span_traceability.json` bytes=2312
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/edge_component_span_traceability.md` bytes=1744
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_span_iou_metrics.json` bytes=1405
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_span_iou_components.csv` bytes=162, records=0
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_span_iou_report.md` bytes=1371
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/provenance_manifest.json` bytes=100278
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/provenance_manifest.md` bytes=55803
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/provenance_prov_o.ttl` bytes=183362
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/provenance_prov_o_summary.json` bytes=845
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/provenance_prov_o_report.md` bytes=1486
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/provenance_llm_run_index.csv` bytes=16241, records=23
- OK (required) `outputs/06_triples/triple_quality_report.md` bytes=374
- OK (required) `experiments/cape_kg_eacl_20260627/01_data/silver_reference_edges.jsonl` bytes=2028487, records=900
- OK (required) `experiments/cape_kg_eacl_20260627/03_predictions/P_cape_kg_silver.jsonl` bytes=2003259, records=900

### M6. Span verifier

- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json` bytes=15122
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_evaluation_report.md` bytes=3152
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_metrics.json` bytes=1822
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_report.md` bytes=1580
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/predicate_cue_span_metrics.json` bytes=5002
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/predicate_cue_span_report.md` bytes=1721
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/predicate_cue_span_rows.csv` bytes=255799, records=947
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/edge_component_span_traceability.json` bytes=2312
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/edge_component_span_traceability.md` bytes=1744
- OK (required) `outputs/13_evidence_graph/edge_component_span_links.jsonl` bytes=2278299, records=2841
- OK (required) `outputs/06_triples/layer2_predicate_cue_spans.jsonl` bytes=572191, records=947
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_32b_awq_core_silver_metrics.json` bytes=4398
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_metrics.json` bytes=1509
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_span_iou_metrics.json` bytes=1405
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_span_iou_report.md` bytes=1371

### M7. Ontology/SHACL validator

- OK (required) `experiments/cape_kg_eacl_20260627/02_schema/cape_shapes.shacl.ttl` bytes=340
- OK (required) `experiments/cape_kg_eacl_20260627/02_schema/cape_schema.json` bytes=3523
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_metrics.json` bytes=22053
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/ontology_conformance_metrics.json` bytes=983
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/ontology_conformance_report.md` bytes=2087
- OK (required) `outputs/12_rdf/cape_kg_layer2.ttl` bytes=870167
- OK (required) `outputs/12_rdf/cape_kg_runtime_shapes.shacl.ttl` bytes=6142
- OK (required) `outputs/12_rdf/cape_kg_shacl_validation_summary.json` bytes=1561
- OK (required) `outputs/12_rdf/cape_kg_shacl_validation_report.md` bytes=1327
- OK (required) `outputs/07_layer2_graph/layer2_graph_quality_report.md` bytes=373

### M8. Procedural consistency validator

- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_metrics.json` bytes=22053
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/procedural_consistency_metrics.json` bytes=15185
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/procedural_consistency_report.md` bytes=2087
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/cq_answerability_structural_metrics.json` bytes=3876
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/cq_answerability_structural.csv` bytes=1488, records=12
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/structural_gap_worklist_summary.json` bytes=916
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/structural_gap_worklist_report.md` bytes=8155
- OK (required) `experiments/cape_kg_eacl_20260627/05_review/structural_review_checkpoint_candidates.csv` bytes=23258, records=45
- OK (required) `experiments/cape_kg_eacl_20260627/05_review/structural_gateway_branch_gaps.csv` bytes=12566, records=4
- OK (required) `experiments/cape_kg_eacl_20260627/05_review/structural_review_optional_returns.csv` bytes=1019, records=2
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/structural_review_action_plan.md` bytes=3565
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/structural_review_action_plan.json` bytes=3753
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/structural_review_return_preflight.md` bytes=1088
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/structural_review_return_preflight.json` bytes=1736
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/structural_review_application_plan.md` bytes=2212
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/structural_review_application_plan.json` bytes=1571
- OK (required) `experiments/cape_kg_eacl_20260627/05_review/structural_review_application_actions.csv` bytes=189, records=0
- OK (required) `outputs/05_procedure/procedure_quality_report.md` bytes=341
- OK (required) `outputs/07_layer2_graph/layer2_edges.jsonl` bytes=331827, records=947

### M9. Alias/canonicalization module

- OK (required) `outputs/04_task_frames/canonical_task_catalog.json` bytes=256506
- OK (required) `outputs/07_layer2_graph/layer2_alias_dictionary.json` bytes=7599
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/alias_canonicalization_report.json` bytes=25200
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/alias_canonicalization_report.md` bytes=4439
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/alias_canonicalization_collision_groups.csv` bytes=3547, records=13
- OK (required) `experiments/cape_kg_eacl_20260627/02_schema/prompts/B3_edc_style_baseline.txt` bytes=111
- OK (required) `experiments/cape_kg_eacl_20260627/49_qwen3_8b_edc_schema_ablation_valid.jsonl` bytes=261060, records=240

### M10. Active review queue

- OK (required) `experiments/cape_kg_eacl_20260627/05_review/active_review_queue.jsonl` bytes=406118, records=900
- OK (required) `experiments/cape_kg_eacl_20260627/05_review/human_gold_annotation_priority_queue.csv` bytes=28819, records=120
- OK (required) `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_expansion_manifest.json` bytes=3903
- OK (required) `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_expansion_report.md` bytes=2513
- OK (required) `experiments/cape_kg_eacl_20260627/05_review/actual_llm_active_review_queue_P_cape_kg_actual.jsonl` bytes=174620, records=275
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_efficiency_metrics.json` bytes=12827
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_efficiency_report.md` bytes=4055
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_ablation_metrics.json` bytes=11236
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_ablation_report.md` bytes=4011
- OK (required) `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort_template.csv` bytes=47175, records=204
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_plan.md` bytes=2911
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_pool_overlap_summary.json` bytes=1861
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_pool_overlap_report.md` bytes=1650
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/human_review_master_checklist_ko.md` bytes=15446
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/human_review_master_checklist_ko.json` bytes=38205
- OK (required) `experiments/cape_kg_eacl_20260627/05_review/human_review_master_return_files.csv` bytes=8192, records=16
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_human_effort_metrics.json` bytes=6348
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_human_effort_report.md` bytes=2911

### M11. NCS/PCF mapping evaluator

- OK (required) `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` bytes=82404, records=110
- OK (required) `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` bytes=81856, records=110
- OK (required) `outputs/08_mapping/l2_ncs_pcf_crosswalk_candidates.jsonl` bytes=290609, records=220
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/ncs_pcf_crosswalk_summary.json` bytes=893
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/ncs_pcf_crosswalk_report.md` bytes=4308
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_results.csv` bytes=300, records=2
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_arm_diagnostics.csv` bytes=2135, records=8
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_arm_rerank_details.csv` bytes=73343, records=176
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_arm_rerank_summary.json` bytes=1744
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_report.md` bytes=2824
- OK (required) `experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.jsonl` bytes=205773, records=220
- OK (required) `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_expert_metrics.json` bytes=1675
- OK (required) `experiments/cape_kg_eacl_20260627/06_release/mapping_review_progress_summary.json` bytes=19472
