# CAPE-KG Responsible NLP Checklist Prep

Generated: 2026-06-29T18:56:41.716941+00:00
Plan: `AX_EACL_submission_review_revised_plan.md`

This artifact prepares draft answers and evidence mapping for the ARR/EACL Responsible NLP checklist. It is not the official completed checklist and intentionally keeps `safe_to_use_as_submission=false`, `submission_ready=false`, and `final_answers_ready=false`.

## Summary

| Item | Value |
| --- | --- |
| Overall status | PASS |
| Claim status | responsible_nlp_checklist_prep_ready_not_final_answers |
| Safe to use as submission | False |
| Submission ready | False |
| Final answers ready | False |
| Checklist prep items | 10 |
| Draft answer count | 10 |
| Pending author confirmations | 2 |
| Missing evidence files | 0 |
| ARR policy checklist | arr_submission_policy_checklist_ready_not_submission_complete |
| ARR08 status | scaffold_ready_final_answers_pending |
| Claim gate | FAIL |
| Public reproducibility | public_reproducibility_manifest_ready_not_submission_complete |
| Anonymized prep | anonymized_submission_prep_ready_not_upload_ready |
| Anonymized upload ready | False |

## Checklist Draft Items

| item_id | checklist_area | status | paper_section | remaining_action | claim_boundary |
| --- | --- | --- | --- | --- | --- |
| RNLP01_limitations_and_claim_scope | Limitations and claim scope | draft_ready | Limitations; Results; Ethics | Keep all final performance language synchronized after human/expert returns. | Do not present silver/proxy metrics as final main-result evidence. |
| RNLP02_data_rights_and_release_boundaries | Data rights and release boundaries | draft_ready | Data; Ethics; Reproducibility | Authors must complete final rights review before any external supplement upload. | Public-safe artifacts mitigate reproducibility limits but do not authorize raw source-text redistribution. |
| RNLP03_private_or_sensitive_data | Private or sensitive data | draft_ready | Ethics; Data | Inspect the final anonymized paper and supplement immediately before ARR upload. | Internal preparation artifacts may mention private paths; upload artifacts must not. |
| RNLP04_human_annotation_and_reviewer_privacy | Human annotation and reviewer privacy | pending_human_gold | Ethics; Evaluation | Complete annotation returns, adjudication, and aggregate-only reporting before final claims. | Do not publish reviewer-level private work files or raw timing logs. |
| RNLP05_llm_use_and_hallucination_risk | LLM use and hallucination risk | draft_ready | Methods; Ethics; Limitations | Refresh risk language if the final model set or decoding configuration changes. | Generation coverage and silver diagnostics are not human-gold performance evidence. |
| RNLP06_reproducibility_without_raw_private_corpus | Reproducibility when raw corpus cannot be released | draft_ready | Reproducibility; Ethics | Keep the public-safe bundle and checksums synchronized after every final-result refresh. | Synthetic examples demonstrate format and tooling; they do not replace target-corpus human-gold evaluation. |
| RNLP07_public_benchmark_license_and_citation | Public benchmark license and citation | pending_rights_review | Related Work; Experiments; Reproducibility | Verify citation and redistribution terms for all external resources before submission. | Auxiliary public-benchmark results must not be framed as target-domain final evidence. |
| RNLP08_anonymization_and_supplement_safety | Anonymization and supplement safety | pending_author_confirmation | Submission checklist; Supplement | Prepare final anonymous PDF and upload-safe supplement after human-gold refresh. | Do not upload internal reproducibility bundles or source-derived review handoff materials. |
| RNLP09_dual_use_or_misuse | Dual-use or misuse | draft_ready | Ethics; Limitations | Recheck dual-use wording after final release contents are selected. | Utility claims should be scoped to KG construction and evaluation, not operational deployment readiness. |
| RNLP10_final_author_confirmation | Final author confirmation | pending_author_confirmation | Submission checklist | Authors must complete final policy, rights, and anonymization confirmations immediately before upload. | This prep artifact is not an official completed checklist and must not be marked submission-ready. |

## Draft Answers

### RNLP01_limitations_and_claim_scope. Limitations and claim scope

The study separates KG construction, setup diagnostics, silver/proxy diagnostics, and final human-gold claims. Final extraction and mapping performance claims are withheld until human-gold annotation, IAA, adjudication, and expert review are complete.

- Status: `draft_ready`
- Paper section: `Limitations; Results; Ethics`
- Remaining action: Keep all final performance language synchronized after human/expert returns.
- Claim boundary: Do not present silver/proxy metrics as final main-result evidence.

### RNLP02_data_rights_and_release_boundaries. Data rights and release boundaries

The target corpus is treated as restricted source-derived enterprise procedural text. Public release is split from internal reproducibility: the public-safe skeleton contains schema, prompts, scripts, synthetic examples, aggregate diagnostics, provenance, and validation reports, while raw or source-derived text remains withheld unless rights are cleared.

- Status: `draft_ready`
- Paper section: `Data; Ethics; Reproducibility`
- Remaining action: Authors must complete final rights review before any external supplement upload.
- Claim boundary: Public-safe artifacts mitigate reproducibility limits but do not authorize raw source-text redistribution.

### RNLP03_private_or_sensitive_data. Private or sensitive data

The workflow assumes that the domain corpus may contain organization-specific or sensitive business-procedure details. Public artifacts should exclude raw OCR text, private review workbooks, reviewer identifiers, and source-derived examples unless explicitly rights-cleared and anonymized.

- Status: `draft_ready`
- Paper section: `Ethics; Data`
- Remaining action: Inspect the final anonymized paper and supplement immediately before ARR upload.
- Claim boundary: Internal preparation artifacts may mention private paths; upload artifacts must not.

### RNLP04_human_annotation_and_reviewer_privacy. Human annotation and reviewer privacy

Human review packages are prepared for annotators, adjudication, mapping experts, crosswalk experts, and active-review effort tracking. Reviewer identities and timing/correction logs should stay private or aggregated, and IAA should be reported as reliability evidence, not personal evaluation.

- Status: `pending_human_gold`
- Paper section: `Ethics; Evaluation`
- Remaining action: Complete annotation returns, adjudication, and aggregate-only reporting before final claims.
- Claim boundary: Do not publish reviewer-level private work files or raw timing logs.

### RNLP05_llm_use_and_hallucination_risk. LLM use and hallucination risk

LLMs are used for baseline, proposed-condition, ablation, and model-scaling prediction generation. The paper should disclose that LLM outputs may hallucinate unsupported nodes, edges, mappings, or evidence; schema constraints, evidence anchors, strict JSON validation, and claim gates reduce but do not eliminate this risk.

- Status: `draft_ready`
- Paper section: `Methods; Ethics; Limitations`
- Remaining action: Refresh risk language if the final model set or decoding configuration changes.
- Claim boundary: Generation coverage and silver diagnostics are not human-gold performance evidence.

### RNLP06_reproducibility_without_raw_private_corpus. Reproducibility when raw corpus cannot be released

The release provides schema, prompts, evaluation scripts, RDF/SHACL shapes, provenance records, checksums, public benchmark adapters, and synthetic examples so that the method and metrics remain inspectable even if the private domain corpus cannot be redistributed.

- Status: `draft_ready`
- Paper section: `Reproducibility; Ethics`
- Remaining action: Keep the public-safe bundle and checksums synchronized after every final-result refresh.
- Claim boundary: Synthetic examples demonstrate format and tooling; they do not replace target-corpus human-gold evaluation.

### RNLP07_public_benchmark_license_and_citation. Public benchmark license and citation

Public benchmark adapters are included as auxiliary checks and should follow original benchmark licenses and citation requirements. Their results support external sanity checking, not the main Korean enterprise-corpus performance claim.

- Status: `pending_rights_review`
- Paper section: `Related Work; Experiments; Reproducibility`
- Remaining action: Verify citation and redistribution terms for all external resources before submission.
- Claim boundary: Auxiliary public-benchmark results must not be framed as target-domain final evidence.

### RNLP08_anonymization_and_supplement_safety. Anonymization and supplement safety

The current internal package is not upload-ready. An anonymization prep scan exists, but the final ARR upload requires an ACL-formatted anonymous PDF and a supplement rebuilt from the public-safe skeleton with local usernames, absolute paths, source-derived workbooks, and private review files removed.

- Status: `pending_author_confirmation`
- Paper section: `Submission checklist; Supplement`
- Remaining action: Prepare final anonymous PDF and upload-safe supplement after human-gold refresh.
- Claim boundary: Do not upload internal reproducibility bundles or source-derived review handoff materials.

### RNLP09_dual_use_or_misuse. Dual-use or misuse

The method structures enterprise procedural knowledge and could reveal operational workflows if raw private text were released. The current mitigation is to keep raw/source-derived materials restricted, publish only public-safe scaffolding, and report aggregated results.

- Status: `draft_ready`
- Paper section: `Ethics; Limitations`
- Remaining action: Recheck dual-use wording after final release contents are selected.
- Claim boundary: Utility claims should be scoped to KG construction and evaluation, not operational deployment readiness.

### RNLP10_final_author_confirmation. Final author confirmation

Several Responsible NLP checklist answers require author confirmation rather than repository evidence: no dual submission, final anonymization, rights clearance, final page-limit check, and whether any acknowledgments or identifying metadata remain.

- Status: `pending_author_confirmation`
- Paper section: `Submission checklist`
- Remaining action: Authors must complete final policy, rights, and anonymization confirmations immediately before upload.
- Claim boundary: This prep artifact is not an official completed checklist and must not be marked submission-ready.

## Remaining Author Actions

- Fill the official ARR Responsible NLP checklist in the submission system using these draft answers as support.
- Confirm final data-rights and redistribution boundaries after selecting the final supplement.
- Render and inspect the final anonymous ACL PDF and upload-safe supplement.
- Complete human-gold, IAA, adjudication, mapping/crosswalk expert review, and active-review effort returns before final performance claims.
- Confirm no dual submission and remove identifying metadata immediately before upload.

## Claim Boundaries

- This artifact prepares checklist answers; it is not the official submitted checklist.
- safe_to_use_as_submission=false and submission_ready=false are intentional.
- No final quality, mapping, or review-efficiency claims are unlocked by this artifact.
- Human-gold and expert-review blockers remain active.

## Evidence Files

| path | exists | bytes |
| --- | --- | --- |
| AX_EACL_submission_review_revised_plan.md | True | 29461 |
| experiments/cape_kg_eacl_20260627/06_release/claim_language_guardrails.md | True | 19281 |
| experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md | True | 6429 |
| experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md | True | 4370 |
| experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md | True | 21410 |
| experiments/cape_kg_eacl_20260627/06_release/data_release_ethics_statement.md | True | 6315 |
| experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | True | 19910 |
| experiments/cape_kg_eacl_20260627/06_release/external_resource_license_report.md | True | 2807 |
| experiments/cape_kg_eacl_20260627/06_release/release_bundle_safety_report.md | True | 2110 |
| experiments/cape_kg_eacl_20260627/06_release/anonymized_submission_prep.md | True | 17046 |
| experiments/cape_kg_eacl_20260627/06_release/anonymized_submission_risk_scan.csv | True | 57075 |
| experiments/cape_kg_eacl_20260627/06_release/public_external_release_excluded_review_queue.md | True | 30908 |
| experiments/cape_kg_eacl_20260627/06_release/human_review_launch_checklist_ko.md | True | 12049 |
| experiments/cape_kg_eacl_20260627/06_release/human_review_master_checklist_ko.md | True | 15446 |
| experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.md | True | 12146 |
| experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md | True | 13157 |
| experiments/cape_kg_eacl_20260627/06_release/strict_json_diagnostics.md | True | 8741 |
| experiments/cape_kg_eacl_20260627/06_release/qwen3_model_scaling_report.md | True | 4752 |
| experiments/cape_kg_eacl_20260627/06_release/reviewer_risk_register.md | True | 17456 |
| experiments/cape_kg_eacl_20260627/06_release/public_synthetic_examples/README.md | True | 969 |
| experiments/cape_kg_eacl_20260627/06_release/provenance_manifest.md | True | 55803 |
| experiments/cape_kg_eacl_20260627/06_release/evaluation_protocol_lock.md | True | 19847 |
| experiments/cape_kg_eacl_20260627/06_release/external_resource_license_report.csv | True | 3710 |
| experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_crosscheck_report.md | True | 1379 |
| experiments/cape_kg_eacl_20260627/06_release/arr_submission_policy_checklist.md | True | 12933 |
| experiments/cape_kg_eacl_20260627/06_release/latest_release_bundle_index.md | True | 2061 |
| experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256 | True | 378 |
| experiments/cape_kg_eacl_20260627/06_release/submission_timeline_action_board.md | True | 6133 |
| experiments/cape_kg_eacl_20260627/06_release/submission_completion_audit_ko.md | True | 25787 |

## Missing Evidence

- No missing evidence files.
