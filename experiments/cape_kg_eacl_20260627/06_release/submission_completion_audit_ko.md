# CAPE-KG EACL 제출 완료 감사표

Generated: 2026-06-29T18:56:33.257649+00:00
Plan: `AX_EACL_submission_review_revised_plan.md`
Experiment: `experiments/cape_kg_eacl_20260627`

## 결론

**현재 목표는 아직 완료가 아닙니다.** 자동 KG 구축, LLM 실행, baseline/ablation, release bundle, pre-human validation은 준비되었지만, 계획서의 최소 제출 요건 중 human-gold annotation, IAA, adjudication, proposed human-gold scoring이 남아 있습니다.

| 항목 | 현재 값 |
|---|---:|
| Submission claim status | `pending_human_gold_iaa_and_human_gold_scoring` |
| Claim gate | `FAIL` |
| Required claim-gate failures | 4 |
| Optional claim-gate failures | 2 |
| Pre-human validation | `PASS` |
| Pre-human checks | 92 |
| Method missing artifacts | 0 |
| Minimum paper-gate return files | 0/11 |
| Optional/strong claim return files | 0/3 |
| Required claim/human return files | 0/14 |
| Optional structural review files | 0/2 |
| All master return files | 0/16 |
| Adjudicated chunks | 0 |
| Gold item count | 0 |
| Mapping pending rows | 220 |
| Optional all-available chunks | 214 |
| Optional remaining chunks | 94 |
| Strong 300-chunk gap without resegmentation | 86 |
| Strong resegmented package | `strong_resegmented_342_max18` |
| Strong resegmented chunks | 342 |
| Strong resegmented max sentences | 18 |
| Strong 300-chunk gap after resegmentation | 0 |
| Strong resegmented claim status | `ready_pending_human_review` |
| Priority-100 selected chunks | 100 |
| Priority-100 candidate-edge coverage | 0.954735 |
| Priority-100 active-review chunk coverage | 0.967033 |
| Priority-100 high-impact chunk coverage | 1.0 |
| Priority-100 candidate edges | 1371/1436 |
| Gold sampling claim status | `gold_sampling_coverage_ready_pending_human_review` |

## Minimum-Accept 요구사항 상태

| id | status | claimable | requirement | next_step |
| --- | --- | --- | --- | --- |
| min.gold_chunks | pending_human | no | 100+ adjudicated gold chunks | Complete two-annotator labeling and adjudication for at least 100 chunks. |
| min.gold_items | pending_human | no | 500+ adjudicated gold node/edge/evidence items | Adjudicate enough nodes, edges, and evidence anchors to reach 500 gold items. |
| min.iaa | pending_human | no | 2+ annotators and agreement for 100+ chunks | Import completed annotator A/B files and recompute IAA. |
| min.gold_sampling_ready | pass | yes | Priority-100 gold subset sampling ready | No additional automatic step required; priority-100 sampling covers 1371/1436 full-120 candidate edges (0.9547), active-review coverage=0.9670, high-impact coverage=1.0000. Human annotation/adjudication still required. |
| min.baselines | pass | yes | B0/B1/B2 actual LLM baselines completed | No additional automatic step required; keep baseline artifacts synchronized. |
| min.proposed | partial | no | CAPE-KG proposed result completed and scored | Score P_cape_kg_actual against adjudicated human gold after gold completion. |
| min.ablations | pass | yes | 3+ actual ablations completed | No additional automatic step required; ablation coverage satisfies the minimum gate. |
| min.error_analysis | pass | yes | Structured error analysis table and taxonomy | No additional automatic step required; update only if new diagnostics change. |
| min.public_subset | pass | yes | Public benchmark or public subset experiment | No additional automatic step required; public subset evidence is present. |
| min.release_plan | pass | yes | Code, prompt, schema, and reproducibility release package | No additional automatic step required; regenerate only after source artifacts change. |
| min.limitations | pass | yes | Limitations section | No additional automatic step required; keep limitations synchronized with future human results. |
| min.public_synthetic_examples | pass | yes | Public-safe synthetic examples for reproducibility mitigation | No additional automatic step required; synthetic public-safe examples are ready. |

## Strong-Accept 요구사항 상태

| id | status | claimable | requirement | next_step |
| --- | --- | --- | --- | --- |
| strong.gold_chunks | pending_human | no | 300-500 adjudicated gold chunks | Use `strong_resegmented_342_max18` for optional 300+ two-annotator review and adjudication; do not claim 300+ adjudicated chunks until reviewed returns are imported. |
| strong.gold_items | pending_human | no | 1,500+ adjudicated gold edge/evidence items | Complete optional 300+ two-annotator review and adjudication until at least 1,500 gold edge/evidence items are available. |
| strong.public_cross | pass | yes | PAGED/Text2KGBench cross experiment | No additional automatic step required; cross-check includes PAGED >= 100 and Text2KG >= 200 in a single run. |
| strong.edc_taxonomy_baselines | pass | yes | EDC/SAC-KG/Taxonomy-RAG family baselines or reproductions | No additional automatic step required; B3/B4/B6 family baseline artifacts are present. |
| strong.mapping_downstream | partial | no | NCS/PCF mapping downstream evaluation | Complete expert review for mapping candidates and crosswalk candidates before making P@K/MRR/nDCG@10, explanation-quality, accept-rate, or utility claims. |
| strong.active_review | partial | no | Active review efficiency evaluation | Collect reviewed active-review human-effort CSV and validate efficiency against human adjudication outcomes. |
| strong.visualization | pass | yes | Visualization/demo provided | No additional automatic step required; keep the viewer synchronized with future graph updates. |

## 현재 Blocking Items

| id | status | claimable | requirement | next_step |
| --- | --- | --- | --- | --- |
| min.gold_chunks | pending_human | no | 100+ adjudicated gold chunks | Complete two-annotator labeling and adjudication for at least 100 chunks. |
| min.gold_items | pending_human | no | 500+ adjudicated gold node/edge/evidence items | Adjudicate enough nodes, edges, and evidence anchors to reach 500 gold items. |
| min.iaa | pending_human | no | 2+ annotators and agreement for 100+ chunks | Import completed annotator A/B files and recompute IAA. |
| min.proposed | partial | no | CAPE-KG proposed result completed and scored | Score P_cape_kg_actual against adjudicated human gold after gold completion. |

## Human Return 상태

| 항목 | 값 |
|---|---:|
| annotation_expected_files | 10 |
| annotation_present_files | 0 |
| annotation_valid_files | 0 |
| adjudication_present | no |
| mapping_present | no |
| mapping_expected_priority_groups | 20 |
| crosswalk_present | no |
| crosswalk_expected_source_tasks | 22 |
| crosswalk_expected_rows | 220 |
| active_review_effort_present | no |
| active_review_effort_expected_rows | 204 |
| optional_structural_return_files | 2 |
| optional_structural_return_files_present | 0 |
| master_return_files | 16 |
| master_return_files_present | 0 |

## Optional Annotation Expansion 해석

- 현재 minimum paper-gate는 기존 priority 100 chunk의 annotation/adjudication 반환 11개 파일 기준입니다.
- mapping expert review, NCS-PCF crosswalk expert review, active-review effort 3개 파일은 optional/strong claim용이며, minimum 11개와 합쳐 required claim/human return 14개로 추적합니다.
- structural review 2개 파일은 절차 구조 보강용 선택 검수이며, master manifest 전체에서는 16개 반환 파일로 함께 추적합니다.
- `all_available_214`는 current corpus 전체를 검수하기 위한 선택 패키지입니다.
- `remaining_94_text_only`는 기존 120개에 포함되지 않은 나머지 chunk입니다.
- `priority_100`은 full-120 안에서 candidate edge, active-review, high-impact 항목을 우선 덮도록 선정한 최소 검수 subset입니다.
- priority-100 sampling coverage는 subset 선정 근거일 뿐이며, gold result claim은 아닙니다.
- `strong_resegmented_342_max18`는 같은 원본 corpus를 최대 18개 source sentence 단위로 재분할한 300+ 검수 후보 패키지입니다.
- 이 재분할 패키지도 사람 검수 전 준비물입니다. 300+ adjudicated chunk claim은 두 annotator 검수와 adjudication이 완료된 뒤에만 가능합니다.

## 증거 파일

| 산출물 | 존재 | bytes | 경로 |
|---|---:|---:|---|
| submission_readiness_audit | yes | 6172 | `experiments/cape_kg_eacl_20260627/06_release/submission_readiness_audit.md` |
| arr_submission_policy_checklist | yes | 12933 | `experiments/cape_kg_eacl_20260627/06_release/arr_submission_policy_checklist.md` |
| arr_submission_policy_checklist_json | yes | 13239 | `experiments/cape_kg_eacl_20260627/06_release/arr_submission_policy_checklist.json` |
| anonymized_submission_prep | yes | 17046 | `experiments/cape_kg_eacl_20260627/06_release/anonymized_submission_prep.md` |
| anonymized_submission_prep_json | yes | 85790 | `experiments/cape_kg_eacl_20260627/06_release/anonymized_submission_prep.json` |
| anonymized_submission_risk_scan | yes | 57075 | `experiments/cape_kg_eacl_20260627/06_release/anonymized_submission_risk_scan.csv` |
| paper_readiness_checklist_json | yes | 3104 | `experiments/cape_kg_eacl_20260627/06_release/paper_readiness_checklist.json` |
| paper_readiness_checklist_md | yes | 3974 | `experiments/cape_kg_eacl_20260627/06_release/paper_readiness_checklist.md` |
| claim_gate_report | yes | 4370 | `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md` |
| human_gate_action_plan | yes | 18799 | `experiments/cape_kg_eacl_20260627/06_release/human_gate_action_plan.md` |
| annotation_batch_review_preview | yes | 2121 | `experiments/cape_kg_eacl_20260627/06_release/annotation_batch_review_preview_summary.md` |
| annotation_batch_review_preview_json | yes | 4684 | `experiments/cape_kg_eacl_20260627/06_release/annotation_batch_review_preview_summary.json` |
| gold_sampling_coverage_report | yes | 4889 | `experiments/cape_kg_eacl_20260627/06_release/gold_sampling_coverage_report.md` |
| gold_sampling_coverage_report_json | yes | 67903 | `experiments/cape_kg_eacl_20260627/06_release/gold_sampling_coverage_report.json` |
| gold_sampling_coverage_by_chapter | yes | 357 | `experiments/cape_kg_eacl_20260627/05_review/gold_sampling_coverage_by_chapter.csv` |
| gold_sampling_priority100_selected_chunks | yes | 12535 | `experiments/cape_kg_eacl_20260627/05_review/gold_sampling_priority100_selected_chunks.csv` |
| strong_resegmented_review_preview | yes | 1370 | `experiments/cape_kg_eacl_20260627/06_release/strong_resegmented_review_preview_summary.md` |
| strong_resegmented_review_preview_json | yes | 2043 | `experiments/cape_kg_eacl_20260627/06_release/strong_resegmented_review_preview_summary.json` |
| human_review_master_checklist | yes | 15446 | `experiments/cape_kg_eacl_20260627/06_release/human_review_master_checklist_ko.md` |
| human_review_first_batch_execution_card | yes | 5593 | `experiments/cape_kg_eacl_20260627/05_review/human_review_first_batch_execution_card_ko.md` |
| human_review_first_batch_execution_card_json | yes | 10518 | `experiments/cape_kg_eacl_20260627/05_review/human_review_first_batch_execution_card.json` |
| human_review_role_quickstart | yes | 19591 | `experiments/cape_kg_eacl_20260627/05_review/human_review_role_quickstart_cards_ko.md` |
| human_review_role_quickstart_json | yes | 28002 | `experiments/cape_kg_eacl_20260627/05_review/human_review_role_quickstart_cards.json` |
| human_review_role_quickstart_csv | yes | 4609 | `experiments/cape_kg_eacl_20260627/05_review/human_review_role_quickstart_cards.csv` |
| human_review_status_dashboard | yes | 12146 | `experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.md` |
| human_review_status_dashboard_json | yes | 36382 | `experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.json` |
| human_review_launch_checklist | yes | 12049 | `experiments/cape_kg_eacl_20260627/06_release/human_review_launch_checklist_ko.md` |
| human_review_launch_checklist_json | yes | 26208 | `experiments/cape_kg_eacl_20260627/06_release/human_review_launch_checklist_ko.json` |
| human_review_packet_integrity | yes | 2505 | `experiments/cape_kg_eacl_20260627/06_release/human_review_packet_integrity.md` |
| human_review_packet_integrity_json | yes | 14261 | `experiments/cape_kg_eacl_20260627/06_release/human_review_packet_integrity.json` |
| human_review_packet_integrity_issues | yes | 53 | `experiments/cape_kg_eacl_20260627/05_review/human_review_packet_integrity_issues.csv` |
| human_review_status_next_actions | yes | 3578 | `experiments/cape_kg_eacl_20260627/05_review/human_review_status_next_actions.csv` |
| human_review_master_return_files | yes | 8192 | `experiments/cape_kg_eacl_20260627/05_review/human_review_master_return_files.csv` |
| human_review_minimum_gate_launch_tasks | yes | 8698 | `experiments/cape_kg_eacl_20260627/05_review/human_review_minimum_gate_launch_tasks.csv` |
| active_review_human_effort_briefing | yes | 15523 | `experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_briefing.md` |
| active_review_human_effort_briefing_json | yes | 1880 | `experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_briefing.json` |
| active_review_human_effort_briefing_csv | yes | 98684 | `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort_briefing.csv` |
| mapping_review_group_briefing | yes | 29653 | `experiments/cape_kg_eacl_20260627/06_release/mapping_review_group_briefing.md` |
| mapping_review_group_briefing_json | yes | 119714 | `experiments/cape_kg_eacl_20260627/06_release/mapping_review_group_briefing.json` |
| mapping_review_group_briefing_csv | yes | 56828 | `experiments/cape_kg_eacl_20260627/05_review/mapping_review_group_briefing_top20.csv` |
| human_review_return_preflight | yes | 2259 | `experiments/cape_kg_eacl_20260627/06_release/human_review_return_preflight.md` |
| strong_review_return_preflight | yes | 2116 | `experiments/cape_kg_eacl_20260627/06_release/strong_review_return_preflight.md` |
| strong_return_apply_last_run | yes | 1429 | `experiments/cape_kg_eacl_20260627/06_release/strong_return_apply_last_run.md` |
| strong_return_apply_last_run_json | yes | 1539 | `experiments/cape_kg_eacl_20260627/06_release/strong_return_apply_last_run.json` |
| strong_return_apply_refusal_last_run | yes | 877 | `experiments/cape_kg_eacl_20260627/06_release/strong_return_apply_refusal_last_run.md` |
| strong_return_apply_refusal_last_run_json | yes | 891 | `experiments/cape_kg_eacl_20260627/06_release/strong_return_apply_refusal_last_run.json` |
| pre_human_validation | yes | 14535 | `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md` |
| provenance_manifest | yes | 55803 | `experiments/cape_kg_eacl_20260627/06_release/provenance_manifest.md` |
| provenance_prov_o | yes | 183362 | `experiments/cape_kg_eacl_20260627/06_release/provenance_prov_o.ttl` |
| provenance_prov_o_report | yes | 1486 | `experiments/cape_kg_eacl_20260627/06_release/provenance_prov_o_report.md` |
| provenance_llm_run_index | yes | 16241 | `experiments/cape_kg_eacl_20260627/04_evaluation/provenance_llm_run_index.csv` |
| public_reproducibility_manifest | yes | 19910 | `experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md` |
| public_reproducibility_manifest_json | yes | 36569 | `experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.json` |
| public_reproducibility_manifest_csv | yes | 17173 | `experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.csv` |
| responsible_nlp_checklist_prep | yes | 14584 | `experiments/cape_kg_eacl_20260627/06_release/responsible_nlp_checklist_prep.md` |
| responsible_nlp_checklist_prep_json | yes | 17320 | `experiments/cape_kg_eacl_20260627/06_release/responsible_nlp_checklist_prep.json` |
| responsible_nlp_checklist_items_csv | yes | 8934 | `experiments/cape_kg_eacl_20260627/06_release/responsible_nlp_checklist_items.csv` |
| experiment_reproduction_card | yes | 13855 | `experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_card.md` |
| experiment_reproduction_card_json | yes | 25386 | `experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_card.json` |
| experiment_reproduction_conditions_csv | yes | 6136 | `experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_conditions.csv` |
| claim_language_guardrails | yes | 19281 | `experiments/cape_kg_eacl_20260627/06_release/claim_language_guardrails.md` |
| claim_language_guardrails_json | yes | 24674 | `experiments/cape_kg_eacl_20260627/06_release/claim_language_guardrails.json` |
| reviewer_response_prep | yes | 14814 | `experiments/cape_kg_eacl_20260627/06_release/reviewer_response_prep.md` |
| reviewer_response_prep_json | yes | 16864 | `experiments/cape_kg_eacl_20260627/06_release/reviewer_response_prep.json` |
| submission_timeline_action_board | yes | 6133 | `experiments/cape_kg_eacl_20260627/06_release/submission_timeline_action_board.md` |
| submission_timeline_action_board_json | yes | 20171 | `experiments/cape_kg_eacl_20260627/06_release/submission_timeline_action_board.json` |
| claimable_main_table | yes | 6429 | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |
| reviewer_risk_register | yes | 17456 | `experiments/cape_kg_eacl_20260627/06_release/reviewer_risk_register.md` |
| reviewer_risk_register_json | yes | 23051 | `experiments/cape_kg_eacl_20260627/06_release/reviewer_risk_register.json` |
| method_novelty_positioning | yes | 10144 | `experiments/cape_kg_eacl_20260627/06_release/method_novelty_positioning.md` |
| method_novelty_positioning_json | yes | 12832 | `experiments/cape_kg_eacl_20260627/06_release/method_novelty_positioning.json` |
| qwen3_model_scaling_report | yes | 4752 | `experiments/cape_kg_eacl_20260627/06_release/qwen3_model_scaling_report.md` |
| qwen3_model_scaling_report_json | yes | 11209 | `experiments/cape_kg_eacl_20260627/06_release/qwen3_model_scaling_report.json` |
| paper_tables | yes | 14924 | `experiments/cape_kg_eacl_20260627/06_release/paper_tables.md` |
| paper_table_blueprint | yes | 12030 | `experiments/cape_kg_eacl_20260627/06_release/paper_table_blueprint.md` |
| paper_table_blueprint_json | yes | 14900 | `experiments/cape_kg_eacl_20260627/06_release/paper_table_blueprint.json` |
| paper_section_source_map | yes | 9141 | `experiments/cape_kg_eacl_20260627/06_release/paper_section_source_map.md` |
| paper_section_source_map_json | yes | 20915 | `experiments/cape_kg_eacl_20260627/06_release/paper_section_source_map.json` |
| eacl_submission_package_manifest | yes | 14120 | `experiments/cape_kg_eacl_20260627/06_release/eacl_submission_package_manifest.md` |
| eacl_submission_package_manifest_json | yes | 27348 | `experiments/cape_kg_eacl_20260627/06_release/eacl_submission_package_manifest.json` |
| post_human_scoring_readiness | yes | 7034 | `experiments/cape_kg_eacl_20260627/06_release/post_human_scoring_readiness.md` |
| post_human_scoring_readiness_json | yes | 41215 | `experiments/cape_kg_eacl_20260627/06_release/post_human_scoring_readiness.json` |
| eacl_paper_draft | yes | 21410 | `experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md` |
| current_reports_index | yes | 13075 | `experiments/cape_kg_eacl_20260627/07_reports/README_current_reports_ko.md` |
| structural_evaluation | yes | 2087 | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md` |
| rdf_shacl_export | yes | 870167 | `outputs/12_rdf/cape_kg_layer2.ttl` |
| rdf_shacl_validation | yes | 1327 | `outputs/12_rdf/cape_kg_shacl_validation_report.md` |
| structural_gap_worklist | yes | 8155 | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_gap_worklist_report.md` |
| structural_review_action_plan | yes | 3565 | `experiments/cape_kg_eacl_20260627/06_release/structural_review_action_plan.md` |
| structural_review_optional_returns | yes | 1019 | `experiments/cape_kg_eacl_20260627/05_review/structural_review_optional_returns.csv` |
| structural_review_return_preflight | yes | 1088 | `experiments/cape_kg_eacl_20260627/06_release/structural_review_return_preflight.md` |
| structural_review_application_plan | yes | 2212 | `experiments/cape_kg_eacl_20260627/06_release/structural_review_application_plan.md` |
| structural_review_application_actions | yes | 189 | `experiments/cape_kg_eacl_20260627/05_review/structural_review_application_actions.csv` |
| professor_presentation | yes | 40745 | `experiments/cape_kg_eacl_20260627/07_reports/professor_presentation_revised_current_20260628_ko.md` |
| professor_slide_contents_current | yes | 61204 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md` |
| professor_core_essentials_prompt_cq_node_edge_separate | yes | 23487 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_essentials_prompt_cq_node_edge_separate_20260629_ko.md` |
| professor_core_essentials_separate_from_slides | yes | 20370 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_essentials_separate_from_slides_20260629_ko.md` |
| professor_core_summary_separate_from_slides_sync4 | yes | 16905 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_summary_separate_from_slides_sync4_20260629_ko.md` |
| professor_key_summary_separate_from_slides | yes | 21842 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_key_summary_separate_from_slides_20260629_ko.md` |
| professor_core_contents_separate | yes | 23857 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_contents_separate_20260629_ko.md` |
| professor_key_content_only_prompt_cq_node_edge | yes | 19149 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_key_content_only_prompt_cq_node_edge_20260629_ko.md` |
| professor_core_methodology_prompt_node_edge_summary | yes | 28098 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_methodology_prompt_node_edge_summary_20260629_ko.md` |
| professor_core_summary_current_20260629 | yes | 17526 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_summary_current_20260629_ko.md` |
| professor_core_summary_current | yes | 20172 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_summary_current_20260628_ko.md` |
| professor_core_briefing_prompt_cq_node_edge_current | yes | 22956 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_briefing_prompt_cq_node_edge_current_20260628_ko.md` |
| prompt_node_edge_traceability | yes | 13157 | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| prompt_node_edge_traceability_json | yes | 24271 | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.json` |
| evidence_graph_projection_report | yes | 1638 | `outputs/13_evidence_graph/evidence_graph_projection_report.md` |
| evidence_graph_projection_summary | yes | 1603 | `outputs/13_evidence_graph/evidence_graph_projection_summary.json` |
| neo4j_evidence_query_pack | yes | 8410 | `experiments/cape_kg_eacl_20260627/06_release/neo4j_evidence_query_pack.md` |
| neo4j_evidence_query_pack_json | yes | 10917 | `experiments/cape_kg_eacl_20260627/06_release/neo4j_evidence_query_pack.json` |
| neo4j_evidence_queries_cypher | yes | 4954 | `outputs/11_neo4j_import_flat/neo4j_evidence_queries.cypher` |
| annotation_expansion_report | yes | 2513 | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_expansion_report.md` |
| latest_release_bundle_index | yes | 2061 | `experiments/cape_kg_eacl_20260627/06_release/latest_release_bundle_index.md` |
| latest_release_bundle_index_json | yes | 5114 | `experiments/cape_kg_eacl_20260627/06_release/latest_release_bundle_index.json` |
| release_checksums | yes | 378 | `experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256` |
| handoff_checksums | yes | 1587 | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256` |

## 다음 명령

### check_handoff_checksums

```bash
sha256sum -c experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256
```

### validate_return_files

```bash
python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627
```

### validate_strong_return_files

```bash
python3 scripts/validate_cape_strong_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627
```

### dry_run_strong_return_apply_wrapper

```bash
PYTHON_BIN=python3 APPLY_IMPORTS=0 bash scripts/run_cape_strong_return_apply.sh
```

### apply_strong_returns_with_wrapper

```bash
PYTHON_BIN=python3 APPLY_IMPORTS=1 bash scripts/run_cape_strong_return_apply.sh
```

### dry_run_human_return_apply_wrapper

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh
```

### apply_human_returns_with_wrapper

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh
```

### low_level_dry_run_refresh

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_post_annotation_refresh.sh
```

### low_level_apply_refresh

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_post_annotation_refresh.sh
```

### check_release_checksums

```bash
sha256sum -c experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256
```

## 사용 시 주의

- 이 문서는 완료 선언이 아니라 완료 여부 감사표입니다.
- silver/proxy diagnostic은 human-gold 성능 증거로 취급하지 않습니다.
- claim gate FAIL은 현재 expected state입니다. 실패 원인은 실험 오류가 아니라 human-gold 미완료입니다.
