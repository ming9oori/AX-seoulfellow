# CAPE-KG Active Review Human-Effort Plan

Generated: 2026-06-29T18:55:22.746612+00:00
Claim status: `ready_for_human_effort_collection`

This artifact prepares the human-effort evidence needed for the active-review efficiency claim. It does not create a claimable efficiency result until reviewers return timing and correction decisions.

## Files

- Template CSV: `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort_template.csv`
- Expected reviewed CSV: `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort.reviewed.csv`
- Metrics JSON: `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_human_effort_metrics.json`
- Metrics CSV: `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_human_effort_metrics.csv`
- Evaluation report: `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_human_effort_report.md`
- Pool overlap JSON: `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_pool_overlap_summary.json`
- Pool overlap report: `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_pool_overlap_report.md`
- Human-effort briefing: `experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_briefing.md`
- Human-effort briefing CSV: `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort_briefing.csv`

## Review Instructions

- Review each row once in the pooled sheet.
- Fill `reviewer_id`, `review_seconds`, `decision`, `corrected_error`, and `high_impact_correction`.
- Use `decision=correct`, `incorrect`, `partial`, `unsupported`, `invalid`, or `unsure`.
- Mark `corrected_error=true` when the reviewer changed or rejected the candidate.
- Mark `high_impact_correction=true` for evidence, schema, risk, gateway, or central task-flow corrections.
- Save the completed file at the expected reviewed CSV path.

## Current Assignment

- Condition: `P_cape_kg_actual`
- Arm budget: 100
- Pooled rows: 204
- Active rows included: 100
- Uncertainty rows included: 100
- Random-control rows included: 100
- Duplicate assignments removed by pooling: 96
- Pooling reduction rate: 0.32

## Human-Effort Metrics

| arm | assigned | reviewed | seconds | corrected | high-impact | corrections/hour | high-impact/hour | status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| active_priority | 100 | 0 | 0 | 0 | 0 | None | None | pending_human_effort_timing |
| uncertainty_only | 100 | 0 | 0 | 0 | 0 | None | None | pending_human_effort_timing |
| random_control | 100 | 0 | 0 | 0 | 0 | None | None | pending_human_effort_timing |

## Claim Scope

- `ready_for_human_effort_collection`: template and evaluator are ready, but no reviewed timing file is present.
- `pending_human_effort_timing`: reviewed decisions may be partial or missing review seconds.
- `human_effort_evaluated`: reviewer timing and decisions are present, but paper claims still require adjudicated gold outcome alignment.
