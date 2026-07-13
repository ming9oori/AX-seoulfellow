# CAPE-KG Structural Review Action Plan

Generated: 2026-06-29T18:55:37.048612+00:00
Claim status: `optional_structural_review_ready_pending_human_review`

## Purpose

This plan turns the structural gap worklist into optional human-review return files. It does not change the 11-file minimum paper gate and is tracked separately for optional/strong claims.

## Summary

| Item | Value |
|---|---:|
| Review checkpoint candidates | 45 |
| Gateway branch gaps | 4 |
| Structural CQ answerability | 1.0 |
| Procedural consistency | 0.995283 |
| Required human-gate effect | does_not_change_minimum_11_file_paper_gate |

## Optional Return Files

| task_type | expected_rows | input_file | reviewed_file | status |
|---|---:|---|---|---|
| structural_review_checkpoint_candidates | 45 | `experiments/cape_kg_eacl_20260627/05_review/structural_review_checkpoint_candidates.csv` | `experiments/cape_kg_eacl_20260627/05_review/structural_review_checkpoint_candidates.reviewed.csv` | ready_for_optional_review |
| structural_gateway_branch_gaps | 4 | `experiments/cape_kg_eacl_20260627/05_review/structural_gateway_branch_gaps.csv` | `experiments/cape_kg_eacl_20260627/05_review/structural_gateway_branch_gaps.reviewed.csv` | ready_for_optional_review |

## Input CSV Fields

- `structural_review_checkpoint_candidates.csv` lists review-signaled task/step rows and their evidence previews.
- `structural_gateway_branch_gaps.csv` includes `guard_condition_labels`, `incoming_task_labels`, and `candidate_branch_target_labels` so reviewers do not need to infer branch targets from IDs alone.
- `human_decision` and `human_notes` are the only fields reviewers must fill unless they need to clarify a branch target in notes.

| input | fields |
|---|---|
| structural_review_checkpoint_candidates.csv | `gap_type, node_id, label, current_type, parent_task_id, incoming_predicates, outgoing_predicates, evidence_anchor_count, evidence_preview, matched_review_terms, recommended_action, human_decision, human_notes` |
| structural_gateway_branch_gaps.csv | `gap_type, gateway_id, gateway_label, guard_condition_edges, guard_condition_ids, guard_condition_labels, incoming_task_count, incoming_task_ids, incoming_task_labels, candidate_branch_target_ids, candidate_branch_target_labels, evidence_anchor_count, evidence_preview, recommended_action, human_decision, human_notes` |

## Decision Policy

- Review checkpoint rows should be accepted only when the activity is a true review/checkpoint, not merely a normal task containing review-like wording.
- Gateway branch rows should add `BRANCHES_TO` only when the source evidence supports explicit branch outcomes.
- Ambiguous rows should be marked `needs_discussion` rather than used to modify the KG automatically.
- The current KG must not be changed from this worklist until reviewed files are returned and an import/update step is explicitly run.

## Allowed Decisions

| task_type | allowed decisions |
|---|---|
| structural_review_checkpoint_candidates | `accept_review_checkpoint;keep_current_type;merge_with_existing_review;reject_candidate;needs_discussion` |
| structural_gateway_branch_gaps | `add_branches_to;keep_gateway_without_branch;split_gateway;reject_gateway;needs_discussion` |

## Next Step

1. Open the input CSV files listed above.
2. Fill `human_decision` and `human_notes` for each row.
3. Save each file with the exact `.reviewed.csv` filename listed above.
4. Keep these files as optional structural review evidence; they do not replace the 11 minimum paper-gate annotation/adjudication return files.
