# CAPE-KG Active-Review Effort Roundtrip Smoke

Generated: 2026-06-29T18:55:22.794770+00:00
Overall status: `PASS`
Claim status: `active_review_effort_roundtrip_smoke_not_paper_evidence`

This is a synthetic engineering smoke test for the active-review human-effort CSV path.
It is not paper evidence and must not be used as human-effort or model-quality evidence.

## Summary

- selected rows: 30
- reviewed rows: 30
- validation status: `validated`
- validation errors: 0
- validation warnings: 0
- ready for metric import: True

## Metrics

| arm | assigned | reviewed | seconds | corrected | high-impact | status |
|---|---:|---:|---:|---:|---:|---|
| active_priority | 20 | 20 | 572.0 | 6 | 1 | human_effort_evaluated |
| uncertainty_only | 22 | 22 | 643.0 | 8 | 2 | human_effort_evaluated |
| random_control | 15 | 15 | 420.0 | 2 | 1 | human_effort_evaluated |

## Claim Scope

- The reviewed CSV is synthetic and scoped only to roundtrip validation.
- The real `active_review_human_effort.reviewed.csv` is still required before any human-effort claim.
