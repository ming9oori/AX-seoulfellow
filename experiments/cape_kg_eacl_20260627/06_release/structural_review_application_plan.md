# CAPE-KG Structural Review Application Plan

Generated: 2026-06-29T18:55:37.115365+00:00
Overall status: `pending_optional_returns`
Claim status: `optional_structural_review_application_dry_run_not_paper_evidence`

This is a dry-run application plan for optional structural-review returns. It does not modify the KG.

## Summary

| Item | Value |
|---|---:|
| Reviewed action rows | 0 |
| Manual update required | 0 |
| No-change decisions | 0 |
| Discussion required | 0 |
| Blocked rows | 0 |

## Preflight

| Item | Value |
|---|---:|
| path | experiments/cape_kg_eacl_20260627/06_release/structural_review_return_preflight.json |
| overall_status | pending_optional_returns |
| present_files | 0 |
| valid_files | 0 |
| error_count | 0 |
| warning_count | 0 |

## Source Files

| task_type | reviewed_file | present | rows |
|---|---|---:|---:|
| structural_review_checkpoint_candidates | `experiments/cape_kg_eacl_20260627/05_review/structural_review_checkpoint_candidates.reviewed.csv` | False | 0 |
| structural_gateway_branch_gaps | `experiments/cape_kg_eacl_20260627/05_review/structural_gateway_branch_gaps.reviewed.csv` | False | 0 |

## Proposed Actions

No optional structural review returns have been provided yet, so there are no application actions.

## Decision Mapping

| reviewed decision | dry-run effect |
|---|---|
| `accept_review_checkpoint` | propose adding/retyping a ReviewCheckpoint or related checkpoint link |
| `merge_with_existing_review` | propose merging with an existing review checkpoint |
| `keep_current_type` | no KG change |
| `reject_candidate` | no KG change |
| `add_branches_to` | propose adding explicit branch targets only with source evidence |
| `split_gateway` | propose splitting an overloaded gateway |
| `keep_gateway_without_branch` | no KG change |
| `reject_gateway` | no KG change |
| `needs_discussion` | discussion required before any KG change |

## Next Step

1. Complete optional structural reviewed CSV files only if structural repair evidence is needed.
2. Run `scripts/validate_cape_structural_review_returns.py`.
3. Run this script to generate the dry-run application plan.
4. Apply KG changes only after explicit review of the proposed actions.
