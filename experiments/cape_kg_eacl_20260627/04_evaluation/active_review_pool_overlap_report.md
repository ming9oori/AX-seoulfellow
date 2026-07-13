# CAPE-KG Active Review Pool Overlap Diagnostic

Generated: 2026-06-29T18:55:22.746612+00:00
Claim status: `pool_design_diagnostic_not_human_effort_claim`

This report explains how the active-priority, uncertainty-only, and random-control review arms are pooled into one human-effort sheet.
It is a design diagnostic only; human-review efficiency claims still require reviewer timing and adjudicated labels.

## Pooling Summary

- Total arm assignments before pooling: 300
- Unique review rows after pooling: 204
- Duplicate assignments removed: 96
- Pooling reduction rate: 0.32

## Arm Counts

| arm | rows |
|---|---:|
| active_priority | 100 |
| uncertainty_only | 100 |
| random_control | 100 |

## Pairwise Overlap

| left arm | right arm | overlap rows | Jaccard |
|---|---|---:|---:|
| active_priority | uncertainty_only | 48 | 0.315789 |
| active_priority | random_control | 30 | 0.176471 |
| uncertainty_only | random_control | 31 | 0.183432 |

## Membership Buckets

| bucket | rows | silver error rows | silver high-impact rows |
|---|---:|---:|---:|
| active_only | 35 | 35 | 18 |
| uncertainty_only | 34 | 34 | 25 |
| random_only | 52 | 51 | 32 |
| active_and_uncertainty_only | 35 | 35 | 24 |
| active_and_random_only | 17 | 17 | 8 |
| uncertainty_and_random_only | 18 | 18 | 15 |
| all_three | 13 | 13 | 8 |

## Claim Scope

- The overlap counts describe assignment design, not model quality.
- `silver_error_rows` and `silver_high_impact_error_rows` are proxy labels used only to prioritize review.
- Final active-review efficiency requires the returned `active_review_human_effort.reviewed.csv` and adjudicated human-gold outcomes.
