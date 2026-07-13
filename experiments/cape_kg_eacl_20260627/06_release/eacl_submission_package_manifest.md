# CAPE-KG EACL Submission Package Manifest

Generated: 2026-06-29T19:06:50.293061+00:00
Plan: `AX_EACL_submission_review_revised_plan.md`

이 문서는 EACL 제출 패키지 관점에서 현재 넣을 수 있는 산출물과 아직 넣으면 안 되는 산출물을 구분한 claim-safe manifest입니다. 최종 제출 승인 문서가 아니며, human-gold 및 expert-review 전 상태를 명시적으로 유지합니다.

## Summary

| Item | Value |
| --- | --- |
| Overall status | PASS |
| Claim status | eacl_submission_package_manifest_ready_not_submission_complete |
| Safe to use as submission | False |
| Submission ready | False |
| Package components | 22 |
| Ready/diagnostic components | 17 |
| Pending components | 5 |
| Missing evidence files | 0 |
| Paper section source map | PASS |
| Pre-human validation | PASS |
| Pre-human checks | 92 |
| Claim gate | FAIL |
| Required claim-gate failures | 4 |
| Optional claim-gate failures | 2 |
| Release stamp | return_preflight_sync02_20260629 |
| Anonymized prep | anonymized_submission_prep_ready_not_upload_ready |
| Anonymized upload ready | False |
| Responsible NLP checklist prep | responsible_nlp_checklist_prep_ready_not_final_answers |
| Responsible NLP final answers ready | False |
| Experiment reproduction card | experiment_reproduction_card_ready_not_human_gold_claim |
| Experiment reproduction conditions | 14 |
| Experiment reproduction final claim ready | False |

## Package Components

| component_id | component_type | item | status | paper_use | next_gate | evidence_files |
| --- | --- | --- | --- | --- | --- | --- |
| PKG01 | manuscript | Claim-safe EACL paper draft skeleton | ready_internal_not_submission_ready | Use as internal draft only; final manuscript requires human-gold results. | human gold and final scoring | experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md, experiments/cape_kg_eacl_20260627/06_release/eacl_paper_draft_status.json, experiments/cape_kg_eacl_20260627/06_release/paper_section_source_map.md |
| PKG02 | manuscript | Long-paper section source map | ready | Use to verify section evidence coverage and claim boundaries. | keep synchronized after new results | experiments/cape_kg_eacl_20260627/06_release/paper_section_source_map.md, experiments/cape_kg_eacl_20260627/06_release/paper_section_source_map.json |
| PKG03 | tables | Claimable setup and diagnostic tables | ready_diagnostic_only | Use setup/diagnostic rows only; do not present silver/proxy rows as final main results. | human-gold scoring | experiments/cape_kg_eacl_20260627/06_release/paper_tables.md, experiments/cape_kg_eacl_20260627/06_release/paper_tables.tex, experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md |
| PKG04 | method_artifacts | CAPE-KG method, schema, prompt, and provenance artifacts | ready | Use in method/reproducibility sections. | none before human return | experiments/cape_kg_eacl_20260627/06_release/method_module_coverage.md, experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md, experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md, experiments/cape_kg_eacl_20260627/06_release/neo4j_evidence_query_pack.md, experiments/cape_kg_eacl_20260627/06_release/provenance_manifest.md, outputs/13_evidence_graph/evidence_graph_projection_report.md, outputs/11_neo4j_import_flat/neo4j_evidence_queries.cypher |
| PKG05 | experiments | LLM baseline, ablation, and model-scaling diagnostics | ready_diagnostic_only | Use as generation coverage and diagnostic evidence only. | human-gold scoring | experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_evaluation_report.md, experiments/cape_kg_eacl_20260627/06_release/qwen3_model_scaling_report.md, experiments/cape_kg_eacl_20260627/06_release/strict_json_diagnostics.md, experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md |
| PKG06 | experiments | Public benchmark adapter diagnostics | ready_auxiliary | Use as auxiliary generalization evidence, not as main private-corpus result. | none before human return | experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_crosscheck_report.md, experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_crosscheck_summary.json, experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md |
| PKG07 | downstream | NCS/PCF mapping and crosswalk candidate evidence | candidate_only_pending_expert_review | Describe candidate generation only; do not claim P@K/MRR/utility yet. | mapping and crosswalk expert review | experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_report.md, experiments/cape_kg_eacl_20260627/06_release/mapping_review_progress_report.md, experiments/cape_kg_eacl_20260627/04_evaluation/ncs_pcf_crosswalk_report.md |
| PKG08 | analysis | Error analysis and reviewer risk controls | ready_diagnostic_only | Use as silver/proxy and risk-control analysis. | refresh after human-gold scoring | experiments/cape_kg_eacl_20260627/07_reports/error_analysis.md, experiments/cape_kg_eacl_20260627/06_release/reviewer_risk_register.md, experiments/cape_kg_eacl_20260627/06_release/rq_evidence_matrix.md |
| PKG09 | release | Public-safe and internal reproducibility bundles | ready_not_submission_complete | Use for reproducibility statement and artifact handoff. | rights review before any external source-text release | experiments/cape_kg_eacl_20260627/06_release/release_bundle_manifest.json, experiments/cape_kg_eacl_20260627/06_release/release_bundle_safety_report.md, experiments/cape_kg_eacl_20260627/06_release/latest_release_bundle_index.md, experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256 |
| PKG10 | release | Ethics, limitations, licensing, and synthetic public examples | ready | Use in Limitations, Ethics, and reproducibility mitigation sections. | keep synchronized with final claims | experiments/cape_kg_eacl_20260627/06_release/limitations.md, experiments/cape_kg_eacl_20260627/06_release/data_release_ethics_statement.md, experiments/cape_kg_eacl_20260627/06_release/external_resource_license_report.md, experiments/cape_kg_eacl_20260627/06_release/public_synthetic_examples/README.md, experiments/cape_kg_eacl_20260627/06_release/public_synthetic_examples/synthetic_evaluation_summary.json |
| PKG11 | human_gate | Human-gold annotation, IAA, adjudication, and proposed scoring | pending_human_returns | Do not claim final extraction performance until these returns are imported. | minimum paper-gate human returns | experiments/cape_kg_eacl_20260627/06_release/human_review_launch_checklist_ko.md, experiments/cape_kg_eacl_20260627/06_release/human_review_return_preflight.md, experiments/cape_kg_eacl_20260627/06_release/human_gate_action_plan.md, experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.md |
| PKG12 | active_review | Active-review human effort evidence | pending_human_effort | Do not claim review-efficiency improvements yet. | timing/correction evidence | experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_plan.md, experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_briefing.md, experiments/cape_kg_eacl_20260627/04_evaluation/active_review_human_effort_report.md |
| PKG13 | gate | Submission completion and pre-human validation audit | ready_not_complete | Use as internal go/no-go evidence. | human-gold and expert-review blockers | experiments/cape_kg_eacl_20260627/06_release/submission_completion_audit_ko.md, experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md, experiments/cape_kg_eacl_20260627/06_release/eacl_plan_compliance_matrix.md, experiments/cape_kg_eacl_20260627/06_release/paper_readiness_checklist.md |
| PKG14 | scoring_gate | Post-human metric scoring readiness map | ready_pending_human_returns | Use to connect returned human/expert files to metric-level paper tables after refresh. | human-gold and expert-review returns | experiments/cape_kg_eacl_20260627/06_release/post_human_scoring_readiness.md, experiments/cape_kg_eacl_20260627/06_release/post_human_scoring_readiness.json, experiments/cape_kg_eacl_20260627/06_release/paper_tables.md |
| PKG15 | claim_language | Claim-language guardrails for paper and presentation wording | ready_not_submission_complete | Use to keep paper, slides, and reports from overclaiming before human/expert returns. | human-gold and expert-review returns | experiments/cape_kg_eacl_20260627/06_release/claim_language_guardrails.md, experiments/cape_kg_eacl_20260627/06_release/claim_language_guardrails.json, experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md, experiments/cape_kg_eacl_20260627/06_release/reviewer_risk_register.md |
| PKG16 | reviewer_response | Reviewer-question response preparation map | ready_not_submission_complete | Use to keep paper framing and reviewer-facing answers aligned with current evidence and claim gates. | human-gold and expert-review returns | experiments/cape_kg_eacl_20260627/06_release/reviewer_response_prep.md, experiments/cape_kg_eacl_20260627/06_release/reviewer_response_prep.json, experiments/cape_kg_eacl_20260627/06_release/reviewer_risk_register.md, experiments/cape_kg_eacl_20260627/06_release/claim_language_guardrails.md |
| PKG17 | timeline | Submission timeline and critical-path action board | ready_not_submission_complete | Use to track dated critical-path actions against the revised EACL plan schedule. | minimum human-gold returns and final scoring | experiments/cape_kg_eacl_20260627/06_release/submission_timeline_action_board.md, experiments/cape_kg_eacl_20260627/06_release/submission_timeline_action_board.json, experiments/cape_kg_eacl_20260627/06_release/eacl_plan_compliance_matrix.md, experiments/cape_kg_eacl_20260627/06_release/human_review_launch_checklist_ko.md |
| PKG18 | paper_tables | Paper table blueprint and promotion gates | ready_not_submission_complete | Use to decide which tables can be main results, diagnostics, appendix material, or pending placeholders. | human-gold and expert-review scoring gates | experiments/cape_kg_eacl_20260627/06_release/paper_table_blueprint.md, experiments/cape_kg_eacl_20260627/06_release/paper_table_blueprint.json, experiments/cape_kg_eacl_20260627/06_release/paper_tables.md, experiments/cape_kg_eacl_20260627/06_release/post_human_scoring_readiness.md |
| PKG19 | submission_policy | ARR/EACL submission policy checklist | ready_not_submission_complete | Use to track ARR/EACL formatting, limitations, ethics, anonymization, supplement, and final PDF policy gates. | author anonymization, final ACL PDF, and human-gold claim gates | experiments/cape_kg_eacl_20260627/06_release/arr_submission_policy_checklist.md, experiments/cape_kg_eacl_20260627/06_release/arr_submission_policy_checklist.json, experiments/cape_kg_eacl_20260627/06_release/eacl_paper_draft_status.json, experiments/cape_kg_eacl_20260627/06_release/data_release_ethics_statement.md |
| PKG20 | anonymization | Anonymized submission prep and public-safe upload risk scan | ready_not_upload_ready | Use as internal ARR/EACL anonymization and supplement-prep evidence only. | final ACL PDF, author anonymization, public-safe supplement rewrite, and human-gold claim gates | experiments/cape_kg_eacl_20260627/06_release/anonymized_submission_prep.md, experiments/cape_kg_eacl_20260627/06_release/anonymized_submission_prep.json, experiments/cape_kg_eacl_20260627/06_release/anonymized_submission_risk_scan.csv, experiments/cape_kg_eacl_20260627/06_release/arr_submission_policy_checklist.md |
| PKG21 | responsible_nlp | Responsible NLP checklist prep and evidence map | ready_final_answers_pending | Use as draft support for ARR/EACL Responsible NLP, ethics, societal-impact, and reproducibility checklist answers. | official checklist final answers, author confirmation, and human-gold claim gates | experiments/cape_kg_eacl_20260627/06_release/responsible_nlp_checklist_prep.md, experiments/cape_kg_eacl_20260627/06_release/responsible_nlp_checklist_prep.json, experiments/cape_kg_eacl_20260627/06_release/responsible_nlp_checklist_items.csv, experiments/cape_kg_eacl_20260627/06_release/data_release_ethics_statement.md, experiments/cape_kg_eacl_20260627/06_release/arr_submission_policy_checklist.md |
| PKG22 | reproducibility | Experiment reproduction card for baselines, ablations, commands, and outputs | ready_not_human_gold_claim | Use to describe exact diagnostic conditions, source outputs, and reproduction commands; do not use silver metrics as final main results. | human-gold scoring and expert-review returns | experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_card.md, experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_card.json, experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_conditions.csv, experiments/cape_kg_eacl_20260627/06_release/evaluation_protocol_lock.md, experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md |

## Submission Blockers

- human-gold annotation and adjudication
- inter-annotator agreement
- proposed-method human-gold scoring
- mapping and crosswalk expert review
- active-review human-effort evidence
- final anonymized ACL PDF and upload-safe supplement rewrite
- official Responsible NLP checklist final answers and author confirmations
- adjudicated human-gold scoring before promoting reproduction-card diagnostics to main results

## Missing Evidence

- No missing evidence files.

## Use Guidance

- 이 manifest가 `PASS`여도 최종 EACL 제출 가능 상태라는 뜻은 아닙니다.
- `ready_diagnostic_only` 항목은 paper의 setup, diagnostic, analysis framing에는 사용할 수 있지만 최종 성능 claim으로 쓰면 안 됩니다.
- `pending_human_returns`, `pending_human_effort`, `candidate_only_pending_expert_review` 항목은 사람이 반환한 검수 결과가 들어오기 전까지 final table에 넣지 않습니다.
- public-safe bundle과 synthetic examples는 재현성 완화책이며, 원문 corpus 공개를 대체하는 최종 승인 근거는 아닙니다.
