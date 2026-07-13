# CAPE-KG Public-Safe Revised Plan Completion Audit

Generated: 2026-06-29T18:56:33.340480+00:00
Plan file: `AX_EACL_submission_review_revised_plan.md`

This public-safe audit exposes completion status, counts, and generic next steps without source text, private review paths, or reviewed file names.

## Public Safety

- Claim status: `public_safe_revised_plan_completion_audit_ready_not_submission_complete`
- Source text included: `False`
- Private review paths included: `False`
- Reviewed file names included: `False`

## Completion Decision

- Plan completion proven: `False`
- Submission ready: `False`
- Reason: The revised plan's automatic scaffolds are ready, but required human-gold, IAA, adjudication, proposed human-gold scoring, and expert/effort evidence are missing.

## Summary

| metric | value |
| --- | --- |
| checklist_item_count | 20 |
| completion_proven_item_count | 11 |
| human_blocked_item_count | 9 |
| minimum_human_blocker_count | 4 |
| strong_or_optional_human_blocker_count | 4 |
| claim_gate_overall_status | FAIL |
| pre_human_handoff_status | PASS |
| pre_human_handoff_checks | 92 |
| required_human_return_files | 14 |
| present_human_return_files | 0 |
| method_modules_missing_required | 0 |

## Public Audit Rows

| scope | id | status | claimable | proof_state | completion_proven | human_blocked | evidence_category | public_next_step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| minimum_accept | min.gold_chunks | pending_human | no | human_required_not_complete | no | yes | human_gold_return_required | Complete two-reviewer gold labeling and adjudicated resolution for the minimum evaluation set. |
| minimum_accept | min.gold_items | pending_human | no | human_required_not_complete | no | yes | human_gold_return_required | Complete two-reviewer gold labeling and adjudicated resolution for the minimum evaluation set. |
| minimum_accept | min.iaa | pending_human | no | human_required_not_complete | no | yes | human_gold_return_required | Compute agreement after both reviewer streams are complete. |
| minimum_accept | min.gold_sampling_ready | pass | yes | proven_for_current_automatic_stage | yes | no | public_or_release_artifact_available | No additional automatic step is required before human returns. |
| minimum_accept | min.baselines | pass | yes | proven_for_current_automatic_stage | yes | no | public_or_release_artifact_available | No additional automatic step is required before human returns. |
| minimum_accept | min.proposed | partial | no | scaffold_ready_human_evidence_pending | no | yes | human_gold_return_required | Score the proposed condition against adjudicated human-gold labels. |
| minimum_accept | min.ablations | pass | yes | proven_for_current_automatic_stage | yes | no | public_or_release_artifact_available | No additional automatic step is required before human returns. |
| minimum_accept | min.error_analysis | pass | yes | proven_for_current_automatic_stage | yes | no | public_or_release_artifact_available | No additional automatic step is required before human returns. |
| minimum_accept | min.public_subset | pass | yes | proven_for_current_automatic_stage | yes | no | public_or_release_artifact_available | No additional automatic step is required before human returns. |
| minimum_accept | min.release_plan | pass | yes | proven_for_current_automatic_stage | yes | no | public_or_release_artifact_available | No additional automatic step is required before human returns. |
| minimum_accept | min.limitations | pass | yes | proven_for_current_automatic_stage | yes | no | public_or_release_artifact_available | No additional automatic step is required before human returns. |
| minimum_accept | min.public_synthetic_examples | pass | yes | proven_for_current_automatic_stage | yes | no | public_or_release_artifact_available | No additional automatic step is required before human returns. |
| strong_accept | strong.gold_chunks | pending_human | no | human_required_not_complete | no | yes | strong_or_expert_return_required | Complete the optional larger human-gold review set before making strong-scale claims. |
| strong_accept | strong.gold_items | pending_human | no | human_required_not_complete | no | yes | strong_or_expert_return_required | Complete the optional larger human-gold review set before making strong-scale claims. |
| strong_accept | strong.public_cross | pass | yes | proven_for_current_automatic_stage | yes | no | public_or_release_artifact_available | No additional automatic step is required before human returns. |
| strong_accept | strong.edc_taxonomy_baselines | pass | yes | proven_for_current_automatic_stage | yes | no | public_or_release_artifact_available | No additional automatic step is required before human returns. |
| strong_accept | strong.mapping_downstream | partial | no | scaffold_ready_human_evidence_pending | no | yes | strong_or_expert_return_required | Complete expert review before making ranking or utility claims. |
| strong_accept | strong.active_review | partial | no | scaffold_ready_human_evidence_pending | no | yes | strong_or_expert_return_required | Collect reviewer effort and correction outcomes before claiming review-efficiency gains. |
| strong_accept | strong.visualization | pass | yes | proven_for_current_automatic_stage | yes | no | public_or_release_artifact_available | No additional automatic step is required before human returns. |
| method_modules | method.m1_m11 | partial | yes | scaffold_ready_human_evidence_pending | no | yes | internal_completion_evidence | Inspect current plan evidence and update after human returns. |

## Source Artifact Roles

- `claim_gate_report`
- `eacl_plan_compliance_matrix`
- `human_review_master_return_files`
- `paper_readiness_checklist`
- `pre_human_handoff_validation`
- `submission_completion_audit`
