# CAPE-KG Anonymized Submission Prep

Generated: 2026-06-29T19:06:50.250431+00:00
Plan: `AX_EACL_submission_review_revised_plan.md`

이 문서는 ARR/EACL 업로드 직전 익명화와 public-safe supplement 준비를 위한 점검 산출물입니다. 최종 제출 승인 문서가 아니며, `safe_to_use_as_submission=false`와 `submission_ready=false`를 의도적으로 유지합니다.

## Summary

| Item | Value |
| --- | --- |
| Overall status | PASS |
| Claim status | anonymized_submission_prep_ready_not_upload_ready |
| Safe to use as submission | False |
| Submission ready | False |
| Upload ready | False |
| Risk rows | 200 |
| Paper draft risk rows | 8 |
| Public-safe tar file count | 385 |
| Public-safe tar blocking hits | 0 |
| Manual gates | 5 |
| Release stamp | return_preflight_sync02_20260629 |
| Public-safe bundle | experiments/cape_kg_eacl_20260627/06_release/bundles/cape_kg_eacl_public_safe_skeleton_return_preflight_sync02_20260629.tar.gz |

## Manual Gates

| gate_id | status | action |
| --- | --- | --- |
| ANON01_final_acl_pdf | pending_pdf_render | Render the final ACL-formatted PDF after human-gold results are inserted and verify page limits. |
| ANON02_author_identity | pending_author_action | Remove author names, local usernames, acknowledgments, and self-identifying repository paths from the upload manuscript. |
| ANON03_public_safe_supplement | public_safe_scaffold_ready_upload_rewrite_pending | Use only the public-safe skeleton bundle, rename the top-level supplement directory, and avoid source-text or internal review files. |
| ANON04_rights_review | pending_author_rights_confirmation | Confirm that no restricted source text, OCR snippets, or private review work files are included in any external supplement. |
| ANON05_final_policy_confirmation | pending_author_confirmation | Confirm no dual submission and complete responsible NLP / ethics checklist answers immediately before upload. |

## Required Inputs

| path | exists | bytes |
| --- | --- | --- |
| AX_EACL_submission_review_revised_plan.md | True | 29461 |
| experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md | True | 21410 |
| experiments/cape_kg_eacl_20260627/06_release/arr_submission_policy_checklist.md | True | 12933 |
| experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | True | 19910 |
| experiments/cape_kg_eacl_20260627/06_release/latest_release_bundle_index.json | True | 5107 |
| experiments/cape_kg_eacl_20260627/06_release/bundles/cape_kg_eacl_public_safe_skeleton_return_preflight_sync02_20260629.tar.gz | True | 1532240 |

## Risk Scan Preview

| scope | path | line | risk_type | severity | snippet |
| --- | --- | --- | --- | --- | --- |
| paper_draft | experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md | 29 | source_or_review_private_path | manual_rewrite_required | \| min.gold_chunks \| 100+ adjudicated gold chunks \| Complete two-annotator labeling and adjudication for at least 100 chunks. \| |
| paper_draft | experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md | 36 | source_or_review_private_path | manual_rewrite_required | We study evidence-grounded procedural knowledge graph construction for long, noisy Korean bid and proposal documents. The proposed CAPE-KG framework anchors extraction to competency questions, retrieves task-specific schema context, constra |
| paper_draft | experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md | 51 | source_or_review_private_path | manual_rewrite_required | - Human annotation, adjudication, IAA, mapping review, crosswalk review, active-review, and optional structural-review workbenches with an 11-file minimum paper gate, 3 optional/strong claim returns, and 2 optional structural returns in the |
| paper_draft | experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md | 98 | source_or_review_private_path | manual_rewrite_required | The annotation package and workbench are ready, but the paper must not claim human-gold results until two annotators and adjudication are complete. |
| paper_draft | experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md | 105 | source_or_review_private_path | manual_rewrite_required | \| Human-gold adjudication \| 1 \| 0 \| final adjudicated gold labels \| |
| paper_draft | experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md | 268 | source_or_review_private_path | manual_rewrite_required | - `06_release/human_gate_action_plan.md` and `05_review/human_gate_required_returns.csv` |
| paper_draft | experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md | 270 | source_or_review_private_path | manual_rewrite_required | - `06_release/human_review_handoff/human_review_handoff_report.md` |
| paper_draft | experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md | 280 | source_or_review_private_path | manual_rewrite_required | - Human-gold annotation, adjudication, and IAA are not complete. |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 4 | internal_experiment_path | review_before_upload | Experiment: `experiments/cape_kg_eacl_20260627` |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 46 | internal_experiment_path | review_before_upload | \| schema_and_cq \| CAPE node/edge schema \| experiments/cape_kg_eacl_20260627/02_schema/cape_schema.json \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 47 | internal_experiment_path | review_before_upload | \| schema_and_cq \| SHACL-style shapes \| experiments/cape_kg_eacl_20260627/02_schema/cape_shapes.shacl.ttl \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 48 | internal_experiment_path | review_before_upload | \| schema_and_cq \| Competency questions \| experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 49 | internal_experiment_path | review_before_upload | \| prompts \| LLM condition prompt: B0_plain_llm_triple_extraction.txt \| experiments/cape_kg_eacl_20260627/02_schema/prompts/B0_plain_llm_triple_extraction.txt \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 50 | internal_experiment_path | review_before_upload | \| prompts \| LLM condition prompt: B1_predicate_constrained_llm.txt \| experiments/cape_kg_eacl_20260627/02_schema/prompts/B1_predicate_constrained_llm.txt \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 51 | internal_experiment_path | review_before_upload | \| prompts \| LLM condition prompt: B2_current_project_baseline.txt \| experiments/cape_kg_eacl_20260627/02_schema/prompts/B2_current_project_baseline.txt \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 52 | internal_experiment_path | review_before_upload | \| prompts \| LLM condition prompt: B3_edc_style_baseline.txt \| experiments/cape_kg_eacl_20260627/02_schema/prompts/B3_edc_style_baseline.txt \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 53 | internal_experiment_path | review_before_upload | \| prompts \| LLM condition prompt: B4_taxonomy_rag_baseline.txt \| experiments/cape_kg_eacl_20260627/02_schema/prompts/B4_taxonomy_rag_baseline.txt \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 54 | internal_experiment_path | review_before_upload | \| prompts \| LLM condition prompt: B5_procedural_prompt_baseline.txt \| experiments/cape_kg_eacl_20260627/02_schema/prompts/B5_procedural_prompt_baseline.txt \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 55 | internal_experiment_path | review_before_upload | \| prompts \| LLM condition prompt: B6_sac_kg_verifier_pruner_baseline.txt \| experiments/cape_kg_eacl_20260627/02_schema/prompts/B6_sac_kg_verifier_pruner_baseline.txt \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 56 | internal_experiment_path | review_before_upload | \| prompts \| LLM condition prompt: P_cape_kg.txt \| experiments/cape_kg_eacl_20260627/02_schema/prompts/P_cape_kg.txt \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 57 | internal_experiment_path | review_before_upload | \| prompts \| LLM condition prompt: P_minus_Schema_retrieval.txt \| experiments/cape_kg_eacl_20260627/02_schema/prompts/P_minus_Schema_retrieval.txt \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 58 | internal_experiment_path | review_before_upload | \| prompts \| LLM condition prompt: strict_json_contract.txt \| experiments/cape_kg_eacl_20260627/02_schema/prompts/strict_json_contract.txt \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 83 | internal_experiment_path | review_before_upload | \| evaluation_protocol \| Locked evaluation protocol \| experiments/cape_kg_eacl_20260627/06_release/evaluation_protocol_lock.md \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 84 | internal_experiment_path | review_before_upload | \| evaluation_protocol \| Locked evaluation protocol JSON \| experiments/cape_kg_eacl_20260627/06_release/evaluation_protocol_lock.json \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 85 | internal_experiment_path | review_before_upload | \| evaluation_protocol \| Claim-safe paper tables \| experiments/cape_kg_eacl_20260627/06_release/paper_tables.md \| yes \| live_release_status \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 86 | internal_experiment_path | review_before_upload | \| evaluation_protocol \| Claim-safe paper tables LaTeX \| experiments/cape_kg_eacl_20260627/06_release/paper_tables.tex \| yes \| live_release_status \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 87 | internal_experiment_path | review_before_upload | \| evaluation_protocol \| Claimability table \| experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md \| yes \| live_release_status \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 88 | internal_experiment_path | review_before_upload | \| evaluation_protocol \| Experiment reproduction card \| experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_card.md \| yes \| live_release_status \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 89 | internal_experiment_path | review_before_upload | \| evaluation_protocol \| Experiment reproduction card JSON \| experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_card.json \| yes \| live_release_status \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 90 | internal_experiment_path | review_before_upload | \| evaluation_protocol \| Experiment reproduction condition CSV \| experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_conditions.csv \| yes \| live_release_status \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 91 | internal_experiment_path | review_before_upload | \| evaluation_protocol \| RQ evidence matrix \| experiments/cape_kg_eacl_20260627/06_release/rq_evidence_matrix.md \| yes \| live_release_status \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 92 | internal_experiment_path | review_before_upload | \| evaluation_protocol \| Public-safe revised plan completion audit \| experiments/cape_kg_eacl_20260627/06_release/revised_plan_completion_audit_public_safe.md \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 93 | internal_experiment_path | review_before_upload | \| evaluation_protocol \| Public-safe revised plan completion audit JSON \| experiments/cape_kg_eacl_20260627/06_release/revised_plan_completion_audit_public_safe.json \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 94 | internal_experiment_path | review_before_upload | \| evaluation_protocol \| Public-safe revised plan completion audit CSV \| experiments/cape_kg_eacl_20260627/06_release/revised_plan_completion_audit_public_safe_items.csv \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 95 | internal_experiment_path | review_before_upload | \| evaluation_protocol \| Metric traceability audit \| experiments/cape_kg_eacl_20260627/06_release/metric_traceability_audit.md \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 96 | internal_experiment_path | review_before_upload | \| evaluation_protocol \| Metric traceability audit JSON \| experiments/cape_kg_eacl_20260627/06_release/metric_traceability_audit.json \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 97 | internal_experiment_path | review_before_upload | \| evaluation_protocol \| Metric traceability audit CSV \| experiments/cape_kg_eacl_20260627/06_release/metric_traceability_audit.csv \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 98 | internal_experiment_path | review_before_upload | \| evaluation_protocol \| Contribution claim traceability \| experiments/cape_kg_eacl_20260627/06_release/contribution_claim_traceability.md \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 99 | internal_experiment_path | review_before_upload | \| evaluation_protocol \| Contribution claim traceability JSON \| experiments/cape_kg_eacl_20260627/06_release/contribution_claim_traceability.json \| yes \| public_safe \| reproducibility \| |
| public_manifest_md | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | 100 | internal_experiment_path | review_before_upload | \| evaluation_protocol \| Contribution claim traceability CSV \| experiments/cape_kg_eacl_20260627/06_release/contribution_claim_traceability.csv \| yes \| public_safe \| reproducibility \| |

- Full risk scan rows: `experiments/cape_kg_eacl_20260627/06_release/anonymized_submission_risk_scan.csv`

## Upload Policy

- Final manuscript upload requires a rendered ACL PDF, not this Markdown draft.
- Supplement upload should be built from the public-safe skeleton only; internal reproducibility bundles are not upload candidates.
- Source-text paths, annotation handoff files, annotator/adjudication files, and local usernames must not appear in the uploaded supplement.
- This artifact is allowed to report internal paths because it is an internal preparation report.

## Interpretation

- This report prepares anonymization and public-safe supplement review; it is not an upload-ready package.
- Internal path references in local reports are expected before final packaging, but must be rewritten or removed from the final ARR upload.
- The public-safe tar scan must stay free of source-text, human-review, adjudication, and internal reproducibility paths.
- Submission-ready language remains forbidden until human-gold, IAA, adjudication, final PDF, and author policy confirmations are complete.
