# CAPE-KG Structural Review Return Preflight

Generated: 2026-06-29T18:55:37.081442+00:00
Overall status: `pending_optional_returns`
Claim status: `optional_structural_review_preflight_not_paper_evidence`

This preflight validates optional structural-review return CSV files. Missing optional files are treated as pending, not as submission blockers.

## Summary

| Item | Value |
|---|---:|
| Expected optional files | 2 |
| Present optional files | 0 |
| Valid optional files | 0 |
| Total errors | 0 |
| Total warnings | 0 |

## Files

| task_type | expected | reviewed | completed | status | errors | warnings |
|---|---:|---:|---:|---|---:|---:|
| structural_review_checkpoint_candidates | 45 | 0 | 0 | missing_reviewed_file | 0 | 0 |
| structural_gateway_branch_gaps | 4 | 0 | 0 | missing_reviewed_file | 0 | 0 |

## Interpretation

- `pending_optional_returns`: no optional reviewed structural CSV has been returned yet.
- `PASS`: reviewed structural CSV files that are present passed validation.
- `FAIL`: at least one reviewed structural CSV is malformed and should not be used.
