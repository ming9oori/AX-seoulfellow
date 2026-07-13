# CAPE-KG Revised Plan Completion Audit

Generated: 2026-06-29T18:56:33.340480+00:00
Plan file: `AX_EACL_submission_review_revised_plan.md`

This audit is a completion-proof artifact for the revised EACL plan. It does not mark the project complete; it records which plan requirements are proven by current artifacts and which remain blocked by human evidence.

## Completion Decision

- Claim status: `revised_plan_not_complete_human_evidence_pending`
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
| missing_evidence_row_count | 0 |
| claim_gate_overall_status | FAIL |
| pre_human_handoff_status | PASS |
| pre_human_handoff_checks | 92 |
| required_human_return_files | 14 |
| present_human_return_files | 0 |
| method_modules_missing_required | 0 |

## Expected Human Blockers

| blocker_group | ids |
| --- | --- |
| minimum_accept | min.gold_chunks, min.gold_items, min.iaa, min.proposed |
| strong_or_optional | strong.gold_chunks, strong.gold_items, strong.mapping_downstream, strong.active_review |

## Plan Checklist Audit

| scope | id | status | claimable | proof_state | completion_proven | human_blocked | evidence_files_present | next_step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| minimum_accept | min.gold_chunks | pending_human | no | human_required_not_complete | no | yes | yes | Complete two-annotator labeling and adjudication for at least 100 chunks. |
| minimum_accept | min.gold_items | pending_human | no | human_required_not_complete | no | yes | yes | Adjudicate enough nodes, edges, and evidence anchors to reach 500 gold items. |
| minimum_accept | min.iaa | pending_human | no | human_required_not_complete | no | yes | yes | Import completed annotator A/B files and recompute IAA. |
| minimum_accept | min.gold_sampling_ready | pass | yes | proven_for_current_automatic_stage | yes | no | yes | No additional automatic step required; priority-100 sampling covers 1371/1436 full-120 candidate edges (0.9547), active-review coverage=0.9670, high-impact coverage=1.0000. Human annotation/adjudication still required. |
| minimum_accept | min.baselines | pass | yes | proven_for_current_automatic_stage | yes | no | yes | No additional automatic step required; keep baseline artifacts synchronized. |
| minimum_accept | min.proposed | partial | no | scaffold_ready_human_evidence_pending | no | yes | yes | Score P_cape_kg_actual against adjudicated human gold after gold completion. |
| minimum_accept | min.ablations | pass | yes | proven_for_current_automatic_stage | yes | no | yes | No additional automatic step required; ablation coverage satisfies the minimum gate. |
| minimum_accept | min.error_analysis | pass | yes | proven_for_current_automatic_stage | yes | no | yes | No additional automatic step required; update only if new diagnostics change. |
| minimum_accept | min.public_subset | pass | yes | proven_for_current_automatic_stage | yes | no | yes | No additional automatic step required; public subset evidence is present. |
| minimum_accept | min.release_plan | pass | yes | proven_for_current_automatic_stage | yes | no | yes | No additional automatic step required; regenerate only after source artifacts change. |
| minimum_accept | min.limitations | pass | yes | proven_for_current_automatic_stage | yes | no | yes | No additional automatic step required; keep limitations synchronized with future human results. |
| minimum_accept | min.public_synthetic_examples | pass | yes | proven_for_current_automatic_stage | yes | no | yes | No additional automatic step required; synthetic public-safe examples are ready. |
| strong_accept | strong.gold_chunks | pending_human | no | human_required_not_complete | no | yes | yes | Use `strong_resegmented_342_max18` for optional 300+ two-annotator review and adjudication; do not claim 300+ adjudicated chunks until reviewed returns are imported. |
| strong_accept | strong.gold_items | pending_human | no | human_required_not_complete | no | yes | yes | Complete optional 300+ two-annotator review and adjudication until at least 1,500 gold edge/evidence items are available. |
| strong_accept | strong.public_cross | pass | yes | proven_for_current_automatic_stage | yes | no | yes | No additional automatic step required; cross-check includes PAGED >= 100 and Text2KG >= 200 in a single run. |
| strong_accept | strong.edc_taxonomy_baselines | pass | yes | proven_for_current_automatic_stage | yes | no | yes | No additional automatic step required; B3/B4/B6 family baseline artifacts are present. |
| strong_accept | strong.mapping_downstream | partial | no | scaffold_ready_human_evidence_pending | no | yes | yes | Complete expert review for mapping candidates and crosswalk candidates before making P@K/MRR/nDCG@10, explanation-quality, accept-rate, or utility claims. |
| strong_accept | strong.active_review | partial | no | scaffold_ready_human_evidence_pending | no | yes | yes | Collect reviewed active-review human-effort CSV and validate efficiency against human adjudication outcomes. |
| strong_accept | strong.visualization | pass | yes | proven_for_current_automatic_stage | yes | no | yes | No additional automatic step required; keep the viewer synchronized with future graph updates. |
| method_modules | method.m1_m11 | partial | yes | scaffold_ready_human_evidence_pending | no | yes | yes | All executable module artifacts are present; human-review and human-gold scoring evidence remains required for final paper claims. |

## Method Module Audit

| module | name | status | required_artifacts | missing_required | human_dependent | proof_state |
| --- | --- | --- | --- | --- | --- | --- |
| M1 | Document structure recovery | implemented_artifacts_present | 5 | 0 | no | artifact_present |
| M2 | CQ generation and selection | implemented_artifacts_present | 7 | 0 | no | artifact_present |
| M3 | CQ-linked schema retrieval | implemented_artifacts_present_human_claim_pending | 8 | 0 | yes | artifact_present_human_claim_pending |
| M4 | Procedural frame extraction | implemented_artifacts_present_human_claim_pending | 6 | 0 | yes | artifact_present_human_claim_pending |
| M5 | Evidence-span constrained triple extraction | implemented_artifacts_present_human_claim_pending | 28 | 0 | yes | artifact_present_human_claim_pending |
| M6 | Span verifier | implemented_artifacts_present_human_claim_pending | 15 | 0 | yes | artifact_present_human_claim_pending |
| M7 | Ontology/SHACL validator | implemented_artifacts_present | 10 | 0 | no | artifact_present |
| M8 | Procedural consistency validator | implemented_artifacts_present_human_claim_pending | 19 | 0 | yes | artifact_present_human_claim_pending |
| M9 | Alias/canonicalization module | implemented_artifacts_present_human_claim_pending | 7 | 0 | yes | artifact_present_human_claim_pending |
| M10 | Active review queue | implemented_artifacts_present_human_claim_pending | 18 | 0 | yes | artifact_present_human_claim_pending |
| M11 | NCS/PCF mapping evaluator | implemented_artifacts_present_human_claim_pending | 13 | 0 | yes | artifact_present_human_claim_pending |

## First Missing Return Files

| required_for_minimum | task_type | owner | batch_or_group | expected_rows | reviewed_file | status |
| --- | --- | --- | --- | --- | --- | --- |
| yes | human_gold_annotation | annotator_A | full_120_priority_batch_001 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.reviewed.jsonl | missing_reviewed_file |
| yes | human_gold_annotation | annotator_B | full_120_priority_batch_001 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.reviewed.jsonl | missing_reviewed_file |
| yes | human_gold_annotation | annotator_A | full_120_priority_batch_002 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_A_full_120_priority_batch_002.reviewed.jsonl | missing_reviewed_file |
| yes | human_gold_annotation | annotator_B | full_120_priority_batch_002 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_B_full_120_priority_batch_002.reviewed.jsonl | missing_reviewed_file |
| yes | human_gold_annotation | annotator_A | full_120_priority_batch_003 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_A_full_120_priority_batch_003.reviewed.jsonl | missing_reviewed_file |
| yes | human_gold_annotation | annotator_B | full_120_priority_batch_003 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_B_full_120_priority_batch_003.reviewed.jsonl | missing_reviewed_file |
| yes | human_gold_annotation | annotator_A | full_120_priority_batch_004 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_A_full_120_priority_batch_004.reviewed.jsonl | missing_reviewed_file |
| yes | human_gold_annotation | annotator_B | full_120_priority_batch_004 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_B_full_120_priority_batch_004.reviewed.jsonl | missing_reviewed_file |

## Source Artifacts

- `eacl_plan_compliance_matrix`: `experiments/cape_kg_eacl_20260627/06_release/eacl_plan_compliance_matrix.json`
- `claim_gate_report`: `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.json`
- `pre_human_handoff_validation`: `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.json`
- `submission_completion_audit`: `experiments/cape_kg_eacl_20260627/06_release/submission_completion_audit_ko.json`
- `paper_readiness_checklist`: `experiments/cape_kg_eacl_20260627/06_release/paper_readiness_checklist.json`
- `human_review_master_return_files`: `experiments/cape_kg_eacl_20260627/05_review/human_review_master_return_files.csv`
