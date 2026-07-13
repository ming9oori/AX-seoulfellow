# CAPE-KG ARR/EACL Submission Policy Checklist

Generated: 2026-06-29T18:55:33.587774+00:00
As-of date: `2026-06-29`
Plan: `AX_EACL_submission_review_revised_plan.md`

이 문서는 공식 EACL/ARR/ACLPUB 제출 요구사항을 현재 CAPE-KG paper draft, release bundle, claim gate와 연결한 checklist입니다.
형식·정책 준비 상태를 보는 문서이며, human-gold 성능 gate를 대체하지 않습니다.

## Summary

| Item | Value |
| --- | --- |
| Overall status | PASS |
| Claim status | arr_submission_policy_checklist_ready_not_submission_complete |
| Safe to use as submission | False |
| Submission ready | False |
| ARR target date | 2026-08-03 |
| Days to ARR target | 35 |
| Checklist items | 10 |
| Missing evidence files | 0 |
| Claim gate | FAIL |
| Pre-human validation | PASS |
| Pre-human checks | 92 |

## Checklist

| id | requirement | status | paper_use_now | blocker | next_action |
| --- | --- | --- | --- | --- | --- |
| ARR01_deadline_tracking | Track EACL 2027 ARR submission target date and use AoE-style planning. | pass | schedule_reference_only | none | Keep the action board synchronized if official dates change. |
| ARR02_claim_gate_not_submission_ready | Do not mark the package as submission-ready while required human-gold claim gates fail. | pass_expected_not_ready | internal_go_no_go | claim_gate=FAIL; required_failures=4 | Complete human-gold, IAA, adjudication, and proposed-method human-gold scoring before submission-ready language. |
| ARR03_limitations_section | Paper draft includes a dedicated Limitations section after Conclusion and before References. | pass | draft_section_ready | none | Keep Limitations limited to limitations; avoid new results, figures, or analysis in that section. |
| ARR04_ethics_section | Paper draft includes ethics/data-release discussion before References. | pass | draft_section_ready | none | Keep data release, private source-text rights, human review, and LLM-use risks synchronized. |
| ARR05_anonymization | Submission manuscript and supplementary material must be anonymized before ARR upload. | pending_author_action | internal_only_until_anonymized | Current draft/release paths are internal and not anonymized for upload. | Prepare an anonymized paper PDF and anonymized supplement bundle from the public-safe release only. |
| ARR06_page_limit_pdf_check | Long/short paper page limits must be checked on the final ACL-formatted PDF. | pending_pdf_render | not_checkable_from_markdown | Markdown draft cannot prove ACL PDF page count. | Render with the current ACL template and verify long/short page count before upload. |
| ARR07_supplement_public_safe | Supplementary material should be anonymized and avoid tracking/file-hosting risks. | public_safe_scaffold_ready_anonymization_pending | internal_release_ready_not_upload_ready | latest_release_bundle_index.md is the authoritative current-bundle pointer; upload-ready anonymization is not yet produced. | Use public-safe skeleton, remove identifying paths/names, and package through an allowed submission mechanism. |
| ARR08_responsible_nlp_checklist | Responsible NLP, ethics, societal impact, and reproducibility issues should be explicitly covered. | scaffold_ready_final_answers_pending | draft_support_ready | Final checklist answers must be filled at submission time. | Use the Responsible NLP checklist prep plus data-release, license, public-safe, and reviewer-risk artifacts to fill the official checklist. |
| ARR09_no_dual_submission | Authors must ensure the paper is not simultaneously submitted elsewhere while under ARR review. | pending_author_confirmation | author_policy_confirmation_required | Requires author confirmation; cannot be proven by repository artifacts. | Confirm submission venue status immediately before ARR upload. |
| ARR10_final_artifact_sync | Final paper, tables, claims, protocol lock, provenance, and release bundle must be regenerated after any human returns. | pass_pre_human_scaffold | internal_process_ready | pre_human_validation=FAIL; paper_submission_ready=False | After human returns, rerun post-annotation refresh and regenerate the final anonymized submission package. |

## Official Sources

| source_id | title | url | used_for |
| --- | --- | --- | --- |
| SRC01_eacl_2027_dates | EACL 2027 official site | https://2027.eacl.org/ | ARR submission deadline and conference date. |
| SRC02_arr_cfp | ACL Rolling Review Call for Papers | https://aclrollingreview.org/cfp | ARR submission, anonymized supplementary material, and desk-rejection policy cues. |
| SRC03_arr_author_checklist | ARR author checklist / common submission problems | https://aclrollingreview.org/authorchecklist | Page-limit and Limitations-section checks. |
| SRC04_aclpub_formatting | ACLPUB paper formatting guidelines | https://acl-org.github.io/ACLPUB/formatting.html | Limitations placement and formatting expectations. |
| SRC05_arr_authors | ARR author guidelines | https://aclrollingreview.org/authors | Under-review and anonymous-preprint policy cues. |
| SRC06_responsible_nlp | ARR Responsible NLP Research Checklist | https://aclrollingreview.org/responsibleNLPresearch/ | Ethics, societal impact, and reproducibility checklist scope. |

## Detailed Evidence

### ARR01_deadline_tracking. Track EACL 2027 ARR submission target date and use AoE-style planning.

- Status: `pass`
- Paper use now: `schedule_reference_only`
- Source IDs: SRC01_eacl_2027_dates
- Blocker: none
- Next action: Keep the action board synchronized if official dates change.

| path | exists | bytes |
| --- | --- | --- |
| AX_EACL_submission_review_revised_plan.md | True | 29461 |
| experiments/cape_kg_eacl_20260627/06_release/submission_timeline_action_board.md | True | 6133 |

### ARR02_claim_gate_not_submission_ready. Do not mark the package as submission-ready while required human-gold claim gates fail.

- Status: `pass_expected_not_ready`
- Paper use now: `internal_go_no_go`
- Source IDs: SRC02_arr_cfp
- Blocker: claim_gate=FAIL; required_failures=4
- Next action: Complete human-gold, IAA, adjudication, and proposed-method human-gold scoring before submission-ready language.

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md | True | 4370 |
| experiments/cape_kg_eacl_20260627/06_release/submission_completion_audit_ko.md | True | 25787 |
| experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md | True | 14477 |

### ARR03_limitations_section. Paper draft includes a dedicated Limitations section after Conclusion and before References.

- Status: `pass`
- Paper use now: `draft_section_ready`
- Source IDs: SRC03_arr_author_checklist, SRC04_aclpub_formatting
- Blocker: none
- Next action: Keep Limitations limited to limitations; avoid new results, figures, or analysis in that section.

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md | True | 21410 |
| experiments/cape_kg_eacl_20260627/06_release/limitations.md | True | 1176 |

### ARR04_ethics_section. Paper draft includes ethics/data-release discussion before References.

- Status: `pass`
- Paper use now: `draft_section_ready`
- Source IDs: SRC06_responsible_nlp
- Blocker: none
- Next action: Keep data release, private source-text rights, human review, and LLM-use risks synchronized.

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md | True | 21410 |
| experiments/cape_kg_eacl_20260627/06_release/data_release_ethics_statement.md | True | 6315 |
| experiments/cape_kg_eacl_20260627/06_release/external_resource_license_report.md | True | 2807 |

### ARR05_anonymization. Submission manuscript and supplementary material must be anonymized before ARR upload.

- Status: `pending_author_action`
- Paper use now: `internal_only_until_anonymized`
- Source IDs: SRC02_arr_cfp, SRC05_arr_authors
- Blocker: Current draft/release paths are internal and not anonymized for upload.
- Next action: Prepare an anonymized paper PDF and anonymized supplement bundle from the public-safe release only.

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md | True | 21410 |
| experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | True | 19910 |
| experiments/cape_kg_eacl_20260627/06_release/release_bundle_safety_report.md | True | 2110 |

### ARR06_page_limit_pdf_check. Long/short paper page limits must be checked on the final ACL-formatted PDF.

- Status: `pending_pdf_render`
- Paper use now: `not_checkable_from_markdown`
- Source IDs: SRC03_arr_author_checklist, SRC04_aclpub_formatting
- Blocker: Markdown draft cannot prove ACL PDF page count.
- Next action: Render with the current ACL template and verify long/short page count before upload.

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md | True | 21410 |
| experiments/cape_kg_eacl_20260627/06_release/paper_section_source_map.md | True | 9141 |
| experiments/cape_kg_eacl_20260627/06_release/paper_table_blueprint.md | True | 12030 |

### ARR07_supplement_public_safe. Supplementary material should be anonymized and avoid tracking/file-hosting risks.

- Status: `public_safe_scaffold_ready_anonymization_pending`
- Paper use now: `internal_release_ready_not_upload_ready`
- Source IDs: SRC02_arr_cfp
- Blocker: latest_release_bundle_index.md is the authoritative current-bundle pointer; upload-ready anonymization is not yet produced.
- Next action: Use public-safe skeleton, remove identifying paths/names, and package through an allowed submission mechanism.

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/06_release/latest_release_bundle_index.md | True | 2061 |
| experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | True | 19910 |
| experiments/cape_kg_eacl_20260627/06_release/public_external_release_review_queue.md | True | 1112 |

### ARR08_responsible_nlp_checklist. Responsible NLP, ethics, societal impact, and reproducibility issues should be explicitly covered.

- Status: `scaffold_ready_final_answers_pending`
- Paper use now: `draft_support_ready`
- Source IDs: SRC06_responsible_nlp
- Blocker: Final checklist answers must be filled at submission time.
- Next action: Use the Responsible NLP checklist prep plus data-release, license, public-safe, and reviewer-risk artifacts to fill the official checklist.

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/06_release/data_release_ethics_statement.md | True | 6315 |
| experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | True | 19910 |
| experiments/cape_kg_eacl_20260627/06_release/reviewer_risk_register.md | True | 17456 |

### ARR09_no_dual_submission. Authors must ensure the paper is not simultaneously submitted elsewhere while under ARR review.

- Status: `pending_author_confirmation`
- Paper use now: `author_policy_confirmation_required`
- Source IDs: SRC05_arr_authors
- Blocker: Requires author confirmation; cannot be proven by repository artifacts.
- Next action: Confirm submission venue status immediately before ARR upload.

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/06_release/submission_timeline_action_board.md | True | 6133 |

### ARR10_final_artifact_sync. Final paper, tables, claims, protocol lock, provenance, and release bundle must be regenerated after any human returns.

- Status: `pass_pre_human_scaffold`
- Paper use now: `internal_process_ready`
- Source IDs: SRC02_arr_cfp
- Blocker: pre_human_validation=FAIL; paper_submission_ready=False
- Next action: After human returns, rerun post-annotation refresh and regenerate the final anonymized submission package.

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/06_release/post_human_scoring_readiness.md | True | 7034 |
| experiments/cape_kg_eacl_20260627/06_release/paper_table_blueprint.md | True | 12030 |
| experiments/cape_kg_eacl_20260627/06_release/evaluation_protocol_lock.md | True | 19847 |
| experiments/cape_kg_eacl_20260627/06_release/provenance_manifest.md | True | 55803 |
| experiments/cape_kg_eacl_20260627/06_release/eacl_submission_package_manifest.md | True | 14120 |

## Claim Policy

- `pass` means the local artifact required for that policy item exists; it does not mean the paper is submission-ready.
- `pending_author_action`, `pending_pdf_render`, and anonymization-related statuses require manual author or final-PDF work.
- `safe_to_use_as_submission=false` and `submission_ready=false` are intentional while human-gold and expert-review gates remain open.
- Re-run this builder after changing official deadlines, paper sections, release bundles, or human-return status.
