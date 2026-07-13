# CAPE-KG Paper Section Source Map

Generated: 2026-06-29T18:56:33.618368+00:00
Plan: `AX_EACL_submission_review_revised_plan.md`
Draft: `experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md`

이 문서는 EACL 논문 초안의 각 섹션이 어떤 현재 산출물로 뒷받침되는지 매핑한 release artifact입니다. 최종 제출 가능 선언이 아니라, 섹션별 근거와 claim boundary를 확인하기 위한 감사표입니다.

## Summary

| Item | Value |
| --- | --- |
| Overall status | PASS |
| Claim status | paper_section_source_map_ready_not_submission_complete |
| Safe to use as submission | False |
| Submission ready | False |
| Total sections | 16 |
| Present sections | 16 |
| Missing section anchors | 0 |
| Evidence file references | 53 |
| Missing evidence files | 0 |
| Human/expert blocked sections | 6 |
| Claim gate | FAIL |
| Required claim-gate failures | 4 |
| Optional claim-gate failures | 2 |

## Section Map

| section_id | planned_section | draft_anchor | present | claim_status | paper_use_now | evidence_files | blocking_gate_ids |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S01 | Abstract / contribution framing | ## Abstract Draft | True | claimable_setup_not_final_performance | yes_with_claim_safety | experiments/cape_kg_eacl_20260627/06_release/method_novelty_positioning.md, experiments/cape_kg_eacl_20260627/06_release/rq_evidence_matrix.md, experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md | gold.completed_chunks, gold.item_count, gold.iaa, llm.proposed_human_gold_score |
| S02 | Introduction | ## Introduction | True | claimable_setup_not_final_performance | yes_with_claim_safety | experiments/cape_kg_eacl_20260627/06_release/method_novelty_positioning.md, experiments/cape_kg_eacl_20260627/06_release/rq_evidence_matrix.md, experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md | gold.completed_chunks, gold.item_count, gold.iaa, llm.proposed_human_gold_score |
| S03 | Related Work | ## Related Work | True | claimable_positioning | yes | experiments/cape_kg_eacl_20260627/06_release/method_novelty_positioning.md, experiments/cape_kg_eacl_20260627/06_release/reviewer_risk_register.md |  |
| S04 | Task Definition | ## Task Definition | True | claimable_setup | yes | experiments/cape_kg_eacl_20260627/02_schema/cape_schema.json, experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md, experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md |  |
| S05 | Dataset and Annotation | ## Dataset and Annotation | True | pending_human_gold | setup_only | experiments/cape_kg_eacl_20260627/06_release/annotation_qc_report.md, experiments/cape_kg_eacl_20260627/06_release/gold_sampling_coverage_report.md, experiments/cape_kg_eacl_20260627/06_release/human_review_master_checklist_ko.md, experiments/cape_kg_eacl_20260627/06_release/human_review_packet_integrity.md | gold.completed_chunks, gold.item_count, gold.iaa |
| S06 | Method: CAPE-KG | ## Method: CAPE-KG | True | claimable_method_artifacts | yes | experiments/cape_kg_eacl_20260627/06_release/method_module_coverage.md, experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md, experiments/cape_kg_eacl_20260627/06_release/provenance_manifest.md |  |
| S07 | Experiments: baselines and ablations | ### Baselines and Ablations | True | diagnostic_only_until_human_gold | diagnostic_only | experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_evaluation_report.md, experiments/cape_kg_eacl_20260627/06_release/qwen3_model_scaling_report.md, experiments/cape_kg_eacl_20260627/06_release/paper_tables.md, experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md | llm.proposed_human_gold_score |
| S08 | Experiments: evidence span granularity | ### Evidence Span Granularity | True | diagnostic_only_until_human_gold | diagnostic_only | experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_report.md, experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_span_iou_report.md, experiments/cape_kg_eacl_20260627/06_release/paper_tables.md | gold.completed_chunks, gold.item_count |
| S09 | Experiments: KG structural diagnostics | ### KG Structural Diagnostics | True | structural_diagnostic_ready | yes_as_structural_diagnostic | experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md, experiments/cape_kg_eacl_20260627/04_evaluation/structural_gap_worklist_report.md, experiments/cape_kg_eacl_20260627/06_release/paper_tables.md |  |
| S10 | Experiments: public benchmark adapters | ### Public Benchmark Adapters | True | auxiliary_claimable_not_main_private_result | yes_as_auxiliary | experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_crosscheck_report.md, experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md, experiments/cape_kg_eacl_20260627/06_release/paper_tables.md |  |
| S11 | Downstream NCS/PCF mapping and crosswalk | ### Layer2-Bridged NCS-PCF Crosswalk Candidates | True | pending_expert_review | candidate_generation_only | experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_report.md, experiments/cape_kg_eacl_20260627/06_release/mapping_review_progress_report.md, experiments/cape_kg_eacl_20260627/04_evaluation/ncs_pcf_crosswalk_report.md, experiments/cape_kg_eacl_20260627/06_release/paper_tables.md | mapping.expert_review, crosswalk.expert_review |
| S12 | Analysis | ## Analysis | True | diagnostic_only_until_human_gold | diagnostic_only | experiments/cape_kg_eacl_20260627/07_reports/error_analysis.md, experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_report.md, experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md, experiments/cape_kg_eacl_20260627/06_release/reviewer_risk_register.md | gold.completed_chunks, gold.item_count |
| S13 | Release and reproducibility | ## Source Artifacts | True | claimable_setup | yes | experiments/cape_kg_eacl_20260627/06_release/release_bundle_manifest.json, experiments/cape_kg_eacl_20260627/06_release/release_bundle_safety_report.md, experiments/cape_kg_eacl_20260627/06_release/provenance_manifest.md, experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md, experiments/cape_kg_eacl_20260627/06_release/data_release_ethics_statement.md |  |
| S14 | Conclusion | ## Conclusion | True | not_submission_ready | claim_safe_summary_only | experiments/cape_kg_eacl_20260627/06_release/submission_completion_audit_ko.md, experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md, experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md | gold.completed_chunks, gold.item_count, gold.iaa, llm.proposed_human_gold_score |
| S15 | Limitations | ## Limitations | True | claimable_limitations | yes | experiments/cape_kg_eacl_20260627/06_release/limitations.md, experiments/cape_kg_eacl_20260627/06_release/reviewer_risk_register.md, experiments/cape_kg_eacl_20260627/06_release/data_release_ethics_statement.md |  |
| S16 | Ethical Considerations | ## Ethical Considerations | True | claimable_ethics | yes | experiments/cape_kg_eacl_20260627/06_release/data_release_ethics_statement.md, experiments/cape_kg_eacl_20260627/06_release/external_resource_license_report.md, experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md |  |

## Blocking Gate Alignment

| gate_id | status | required | evidence |
| --- | --- | --- | --- |
| gold.completed_chunks | FAIL | True | 0 completed chunks, validation_errors=0, file=experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_validation_summary.json |
| gold.item_count | FAIL | True | 0 items, validation_errors=0, file=experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_validation_summary.json |
| gold.iaa | FAIL | True | max_completed_pair_chunks=0, summaries=2 |
| llm.proposed_human_gold_score | FAIL | True | human_gold_scored_conditions=[] |
| mapping.expert_review | FAIL | False | complete_source_groups=0, pending_rows=220, file=experiments/cape_kg_eacl_20260627/04_evaluation/mapping_expert_metrics.json, progress_file=experiments/cape_kg_eacl_20260627/06_release/mapping_review_progress_summary.json, progress_pending_groups=44 |
| crosswalk.expert_review | FAIL | False | completed_rows=0, pending_rows=220, complete_source_groups=0, file=experiments/cape_kg_eacl_20260627/04_evaluation/crosswalk_expert_metrics.json, manifest_file=experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_manifest.json, candidate_rows=220 |

## Missing Evidence

- No missing draft anchors or evidence files.

## Use Guidance

- `claimable_setup`, `claimable_method_artifacts`, and related setup statuses can support method, resource, and reproducibility descriptions.
- `diagnostic_only_until_human_gold` must remain diagnostic until adjudicated labels are imported and scoring is refreshed.
- `pending_expert_review` sections can describe candidate generation but must not report mapping utility metrics as final.
- `safe_to_use_as_submission` is intentionally false because the paper still needs human-gold and expert-review returns.
